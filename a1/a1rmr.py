"""
a1s rmr functionality
"""
# ==================================================================================
#       Copyright (c) 2019 Nokia
#       Copyright (c) 2018-2019 AT&T Intellectual Property.
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#          http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
# ==================================================================================
import os
import queue
import time
import json
from threading import Thread
from rmr import rmr, helpers
from mdclogpy import Logger
from a1 import data, messages
from a1.exceptions import PolicyTypeNotFound, PolicyInstanceNotFound

mdc_logger = Logger(name=__name__)


RETRY_TIMES = int(os.environ.get("A1_RMR_RETRY_TIMES", 4))


A1_POLICY_REQUEST = 20010
A1_POLICY_RESPONSE = 20011
A1_POLICY_QUERY = 20012


# Note; yes, globals are bad, but this is a private (to this module) global
# No other module can import/access this (well, python doesn't enforce this, but all linters will complain)
__RMR_LOOP__ = None


class _RmrLoop:
    """
    class represents an rmr loop that constantly reads from rmr and performs operations based on waiting messages
    this launches a thread, it should probably only be called once; the public facing method to access these ensures this
    """

    def __init__(self, init_func_override=None, rcv_func_override=None):
        self.keep_going = True
        self.rcv_func = None
        self.last_ran = time.time()
        self.instance_send_queue = queue.Queue()  # thread safe queue https://docs.python.org/3/library/queue.html

        # intialize rmr context
        if init_func_override:
            self.mrc = init_func_override()
        else:
            mdc_logger.debug("Waiting for rmr to initialize..")
            # rmr.RMRFL_MTCALL puts RMR into a multithreaded mode, where a receiving thread populates an
            # internal ring of messages, and receive calls read from that
            # currently the size is 2048 messages, so this is fine for the foreseeable future
            self.mrc = rmr.rmr_init(b"4562", rmr.RMR_MAX_RCV_BYTES, rmr.RMRFL_MTCALL)
            while rmr.rmr_ready(self.mrc) == 0:
                time.sleep(0.5)

        # set the receive function
        self.rcv_func = (
            rcv_func_override
            if rcv_func_override
            else lambda: helpers.rmr_rcvall_msgs_raw(self.mrc, [A1_POLICY_RESPONSE, A1_POLICY_QUERY])
        )

        # start the work loop
        self.thread = Thread(target=self.loop)
        self.thread.start()

    def _assert_good_send(self, sbuf, pre_send_summary):
        """
        common helper function for _send_msg and _rts_msg
        """
        post_send_summary = rmr.message_summary(sbuf)
        if post_send_summary["message state"] == 0 and post_send_summary["message status"] == "RMR_OK":
            return True
        mdc_logger.debug("Message NOT sent!")
        mdc_logger.debug("Pre-send summary: {0}, Post-send summary: {1}".format(pre_send_summary, post_send_summary))
        return False

    def _send_msg(self, pay, mtype, subid):
        """
        sends a msg
        """
        for _ in range(0, RETRY_TIMES):
            sbuf = rmr.rmr_alloc_msg(self.mrc, len(pay), payload=pay, gen_transaction_id=True, mtype=mtype, sub_id=subid)
            sbuf.contents.sub_id = subid
            pre_send_summary = rmr.message_summary(sbuf)
            sbuf = rmr.rmr_send_msg(self.mrc, sbuf)  # send
            if self._assert_good_send(sbuf, pre_send_summary):
                rmr.rmr_free_msg(sbuf)  # free
                break

    def _rts_msg(self, pay, sbuf_rts, mtype):
        """
        sends a message using rts
        we do not call free here because we may rts many times; it is called after the rts loop
        """
        for _ in range(0, RETRY_TIMES):
            pre_send_summary = rmr.message_summary(sbuf_rts)
            sbuf_rts = rmr.rmr_rts_msg(self.mrc, sbuf_rts, payload=pay, mtype=mtype)
            if self._assert_good_send(sbuf_rts, pre_send_summary):
                break
        return sbuf_rts  # in some cases rts may return a new sbuf

    def loop(self):
        """
        This loop runs forever, and has 3 jobs:
        - send out any messages that have to go out (create instance, delete instance)
        - read a1s mailbox and update the status of all instances based on acks from downstream policy handlers
        - clean up the database (eg delete the instance) under certain conditions based on those statuses (NOT DONE YET)
        """
        # loop forever
        mdc_logger.debug("Work loop starting")
        while self.keep_going:

            # send out all messages waiting for us
            while not self.instance_send_queue.empty():
                work_item = self.instance_send_queue.get(block=False, timeout=None)
                payload = json.dumps(messages.a1_to_handler(*work_item)).encode("utf-8")
                self._send_msg(payload, A1_POLICY_REQUEST, work_item[1])

            # read our mailbox
            for (msg, sbuf) in self.rcv_func():
                # TODO: in the future we may also have to catch SDL errors
                try:
                    mtype = msg["message type"]
                except (KeyError, TypeError, json.decoder.JSONDecodeError):
                    mdc_logger.debug("Dropping malformed policy ack/query message: {0}".format(msg))

                if mtype == A1_POLICY_RESPONSE:
                    try:
                        # got a policy response, update status
                        pay = json.loads(msg["payload"])
                        data.set_policy_instance_status(
                            pay["policy_type_id"], pay["policy_instance_id"], pay["handler_id"], pay["status"]
                        )
                        mdc_logger.debug("Successfully received status update: {0}".format(pay))
                    except (PolicyTypeNotFound, PolicyInstanceNotFound):
                        mdc_logger.debug("Received a response  for a non-existent instance")
                    except (KeyError, TypeError, json.decoder.JSONDecodeError):
                        mdc_logger.debug("Dropping malformed policy ack message: {0}".format(msg))

                elif mtype == A1_POLICY_QUERY:
                    try:
                        # got a query, do a lookup and send out all instances
                        pti = json.loads(msg["payload"])["policy_type_id"]
                        mdc_logger.debug("Received query for: {0}".format(pti))
                        for pii in data.get_instance_list(pti):
                            instance = data.get_policy_instance(pti, pii)
                            payload = json.dumps(messages.a1_to_handler("CREATE", pti, pii, instance)).encode("utf-8")
                            sbuf = self._rts_msg(payload, sbuf, A1_POLICY_REQUEST)
                    except (PolicyTypeNotFound, PolicyInstanceNotFound):
                        mdc_logger.debug("Received a query for a non-existent type: {0}".format(msg))
                    except (KeyError, TypeError, json.decoder.JSONDecodeError):
                        mdc_logger.debug("Dropping malformed policy query message: {0}".format(msg))

                else:
                    mdc_logger.debug("Received message type {0} but A1 does not handle this".format(mtype))

                # we must free each sbuf
                rmr.rmr_free_msg(sbuf)

            self.last_ran = time.time()
            time.sleep(1)


# Public


def start_rmr_thread(init_func_override=None, rcv_func_override=None):
    """
    Start a1s rmr thread
    """
    global __RMR_LOOP__
    if __RMR_LOOP__ is None:
        __RMR_LOOP__ = _RmrLoop(init_func_override, rcv_func_override)


def stop_rmr_thread():
    """
    stops the rmr thread
    """
    __RMR_LOOP__.keep_going = False


def queue_instance_send(item):
    """
    push an item into the work queue
    currently the only type of work is to send out messages
    """
    __RMR_LOOP__.instance_send_queue.put(item)


def healthcheck_rmr_thread(seconds=30):
    """
    returns a boolean representing whether the rmr loop is healthy, by checking two attributes:
    1. is it running?,
    2. is it stuck in a long (> seconds) loop?
    """
    return __RMR_LOOP__.thread.is_alive() and ((time.time() - __RMR_LOOP__.last_ran) < seconds)


def replace_rcv_func(rcv_func):
    """purely for the ease of unit testing to test different rcv scenarios"""
    __RMR_LOOP__.rcv_func = rcv_func
