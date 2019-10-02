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
import gevent
from rmr import rmr, helpers
from a1 import get_module_logger

logger = get_module_logger(__name__)


RETRY_TIMES = int(os.environ.get("RMR_RETRY_TIMES", 4))
MRC = None


def init_rmr():
    """
    called from run; not called for unit tests
    """
    global MRC
    # rmr.RMRFL_MTCALL puts RMR into a multithreaded mode, where a receiving thread populates an
    # internal ring of messages, and receive calls read from that
    # currently the size is 2048 messages, so this is fine for the foreseeable future
    MRC = rmr.rmr_init(b"4562", rmr.RMR_MAX_RCV_BYTES, rmr.RMRFL_MTCALL)

    while rmr.rmr_ready(MRC) == 0:
        gevent.sleep(1)
        logger.debug("not yet ready")


def send(payload, message_type=0):
    """
    Sends a message up to RETRY_TIMES
    If the message is sent successfully, it returns the transactionid
    Does nothing otherwise
    """
    # we may be called many times in asynchronous loops, so for now, it is safer not to share buffers. We can investigate later whether this is really a problem.
    sbuf = rmr.rmr_alloc_msg(MRC, 4096)
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
        sbuf = rmr.rmr_send_msg(MRC, sbuf)
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


def dequeue_all_waiting_messages(filter_type=[]):
    """
    dequeue all waiting rmr messages from rmr
    """
    return helpers.rmr_rcvall_msgs(MRC, filter_type)
