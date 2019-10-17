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


def _update_all_statuses(mrc):
    """
    get all waiting messages, and try to parse them as status updates
    (currently, those are the only messages a1 should get, this may have to be revisited later)
    """
    for msg in helpers.rmr_rcvall_msgs(mrc, [21024]):
        try:
            pay = json.loads(msg["payload"])
            data.set_status(pay["policy_type_id"], pay["policy_instance_id"], pay["handler_id"], pay["status"])
        except (PolicyTypeNotFound, PolicyInstanceNotFound, KeyError):
            logger.debug("Dropping malformed or non applicable message")
            logger.debug(msg)


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

    def __init__(self, real_init=True):
        self._rmr_is_ready = False
        self._keep_going = True
        self._real_init = real_init  # useful for unit testing to turn off initialization

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
        mrc = None
        logger.debug("Waiting for rmr to initialize...")
        if self._real_init:
            mrc = _init_rmr()
        self._rmr_is_ready = True
        logger.debug("Rmr is ready")

        # loop forever
        logger.debug("Work loop starting")
        while self._keep_going:
            """
            We never raise an exception here. Log and keep moving
            Bugs will eventually be caught be examining logs.
            """
            try:
                # First, send out all messages waiting for us
                while not _SEND_QUEUE.empty():
                    work_item = _SEND_QUEUE.get(block=False, timeout=None)
                    _send(mrc, payload=work_item["payload"], message_type=work_item["msg type"])

                # Next, update all statuses waiting in a1s mailbox
                _update_all_statuses(mrc)

                # TODO: next body of work is to try to clean up the database for any updated statuses

            except Exception as e:
                logger.debug("Polling thread encountered an unexpected exception, but it will continue:")
                logger.exception(e)

            time.sleep(1)
