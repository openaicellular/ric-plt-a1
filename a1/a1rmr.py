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
from a1 import get_module_logger
from a1 import data
from a1.exceptions import PolicyTypeNotFound, PolicyInstanceNotFound

logger = get_module_logger(__name__)


RETRY_TIMES = int(os.environ.get("RMR_RETRY_TIMES", 4))

_SEND_QUEUE = queue.Queue()  # thread safe queue https://docs.python.org/3/library/queue.html


def _init_rmr():
    """
    init an rmr context
    This gets monkeypatched out for unit testing
    """
    # rmr.RMRFL_MTCALL puts RMR into a multithreaded mode, where a receiving thread populates an
    # internal ring of messages, and receive calls read from that
    # currently the size is 2048 messages, so this is fine for the foreseeable future
    logger.debug("Waiting for rmr to initialize..")
    mrc = rmr.rmr_init(b"4562", rmr.RMR_MAX_RCV_BYTES, rmr.RMRFL_MTCALL)
    while rmr.rmr_ready(mrc) == 0:
        time.sleep(0.5)

    return mrc


def _send(mrc, payload, message_type=0):
    """
    Sends a message up to RETRY_TIMES
    If the message is sent successfully, it returns the transactionid
    Does nothing otherwise
    """
    # TODO: investigate moving this below and allocating the space based on the payload size
    sbuf = rmr.rmr_alloc_msg(mrc, 4096)
    payload = payload if isinstance(payload, bytes) else payload.encode("utf-8")

    # retry RETRY_TIMES to send the message
    for _ in range(0, RETRY_TIMES):
        # setup the send message
        rmr.set_payload_and_length(payload, sbuf)
        rmr.generate_and_set_transaction_id(sbuf)
        sbuf.contents.state = 0
        sbuf.contents.mtype = message_type
        pre_send_summary = rmr.message_summary(sbuf)
        logger.debug("Pre message send summary: %s", pre_send_summary)
        transaction_id = pre_send_summary["transaction id"]  # save the transactionid because we need it later

        # send
        sbuf = rmr.rmr_send_msg(mrc, sbuf)
        post_send_summary = rmr.message_summary(sbuf)
        logger.debug("Post message send summary: %s", rmr.message_summary(sbuf))

        # check success or failure
        if post_send_summary["message state"] == 0 and post_send_summary["message status"] == "RMR_OK":
            # we are good
            logger.debug("Message sent successfully!")
            rmr.rmr_free_msg(sbuf)
            return transaction_id

    # we failed all RETRY_TIMES
    logger.debug("Send failed all %s times, stopping", RETRY_TIMES)
    rmr.rmr_free_msg(sbuf)
    return None


# Public


def queue_work(item):
    """
    push an item into the work queue
    currently the only type of work is to send out messages
    """
    _SEND_QUEUE.put(item)


class RmrLoop:
    """
    class represents an rmr loop meant to be called as a longstanding separate thread
    """

    def __init__(self, _init_func_override=None, rcv_func_override=None):
        self._rmr_is_ready = False
        self._keep_going = True
        self._init_func_override = _init_func_override  # useful for unit testing
        self._rcv_func_override = rcv_func_override  # useful for unit testing to mock certain recieve scenarios
        self._rcv_func = None

    def rmr_is_ready(self):
        """returns whether rmr has been initialized"""
        return self._rmr_is_ready

    def stop(self):
        """sets a flag for the loop to end"""
        self._keep_going = False

    def loop(self):
        """
        This loop runs in an a1 thread forever, and has 3 jobs:
        - send out any messages that have to go out (create instance, delete instance)
        - read a1s mailbox and update the status of all instances based on acks from downstream policy handlers
        - clean up the database (eg delete the instance) under certain conditions based on those statuses (NOT DONE YET)
        """

        # get a context
        mrc = self._init_func_override() if self._init_func_override else _init_rmr()
        self._rmr_is_ready = True
        logger.debug("Rmr is ready")

        # set the receive function called below
        self._rcv_func = (
            self._rcv_func_override if self._rcv_func_override else lambda: helpers.rmr_rcvall_msgs(mrc, [21024])
        )

        # loop forever
        logger.debug("Work loop starting")
        while self._keep_going:
            # send out all messages waiting for us
            while not _SEND_QUEUE.empty():
                work_item = _SEND_QUEUE.get(block=False, timeout=None)
                _send(mrc, payload=work_item["payload"], message_type=work_item["msg type"])

            # read our mailbox and update statuses
            updated_instances = set()
            for msg in self._rcv_func():
                try:
                    pay = json.loads(msg["payload"])
                    pti = pay["policy_type_id"]
                    pii = pay["policy_instance_id"]
                    data.set_status(pti, pii, pay["handler_id"], pay["status"])
                    updated_instances.add((pti, pii))
                except (PolicyTypeNotFound, PolicyInstanceNotFound, KeyError, json.decoder.JSONDecodeError):
                    # TODO: in the future we may also have to catch SDL errors
                    logger.debug(("Dropping malformed or non applicable message", msg))

            # for all updated instances, see if we can trigger a delete
            # should be no catch needed here, since the status update would have failed if it was a bad pair
            for ut in updated_instances:
                data.clean_up_instance(ut[0], ut[1])

        # TODO: what's a reasonable sleep time? we don't want to hammer redis too much, and a1 isn't a real time component
        time.sleep(1)


def start_rmr_thread(init_func_override=None, rcv_func_override=None):
    """
    Start a1s rmr thread
    Also called during unit testing
    """
    rmr_loop = RmrLoop(init_func_override, rcv_func_override)
    thread = Thread(target=rmr_loop.loop)
    thread.start()
    while not rmr_loop.rmr_is_ready():
        time.sleep(0.5)
    return rmr_loop  # return the handle; useful during unit testing
