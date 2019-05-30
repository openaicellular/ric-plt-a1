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
from rmr import rmr
from a1 import get_module_logger
from a1.exceptions import MessageSendFailure, ExpectedAckNotReceived

logger = get_module_logger(__name__)


RMR_RCV_RETRY_INTERVAL = int(os.environ.get("RMR_RCV_RETRY_INTERVAL", 1000))
RETRY_TIMES = int(os.environ.get("RMR_RETRY_TIMES", 4))
MRC = None


RECEIVED_MESSAGES = []  # used to store messages we need but havent been procedded yet
WAITING_TRANSIDS = {}  # used to store transactionids we are waiting for, so we can filter other stuff out


def _dequeue_all_waiting_messages():
    """
    dequeue all waiting rmr messages from rmr, put them into RECEIVED_MESSAGES
    """
    new_messages = []
    sbuf = rmr.rmr_alloc_msg(MRC, 4096)
    while True:
        sbuf = rmr.rmr_torcv_msg(MRC, sbuf, 0)  # set the timeout to 0 so this doesn't block!!
        summary = rmr.message_summary(sbuf)
        if summary["message state"] == 12 and summary["message status"] == "RMR_ERR_TIMEOUT":
            break
        elif summary["transaction id"] in WAITING_TRANSIDS:  # message is relevent
            new_messages.append(summary)
        else:
            logger.debug("A message was received by a1, but a1 was not expecting it! It's being dropped: %s", summary)
            # do nothing with message, effectively dropped
    return new_messages


def _check_if_ack_received(target_transid, target_type):
    """
    Try to recieve the latest messages, then search the current queue for the target ACK
    TODO: probably a slightly more efficient data structure than list. Maybe a dict by message type
        However, in the near term, where there are not many xapps under A1, this is fine. Revisit later.
    TODO: do we need to deal with duplicate ACKs for the same transaction id?
        Is it possible if the downstream xapp uses rmr_rts? Might be harmless to sit in queue.. might slow things

    """
    new_messages = _dequeue_all_waiting_messages()  # dequeue all waiting messages
    global RECEIVED_MESSAGES  # this is ugly, but fine.. we just need an in memory list across the async calls
    RECEIVED_MESSAGES += new_messages
    for index, summary in enumerate(RECEIVED_MESSAGES):  # Search the queue for the target message
        if (
            summary["message state"] == 0
            and summary["message status"] == "RMR_OK"
            and summary["message type"] == target_type
            and summary["transaction id"] == target_transid
        ):  # Found; delete it from queue
            del RECEIVED_MESSAGES[index]
            return summary
    return None


def init_rmr():
    """
    called from run; not called for unit tests
    """
    global MRC
    MRC = rmr.rmr_init(b"4562", rmr.RMR_MAX_RCV_BYTES, 0x00)

    while rmr.rmr_ready(MRC) == 0:
        gevent.sleep(1)
        logger.debug("not yet ready")


def send(payload, message_type=0):
    """
    sends a message up to RETRY_TIMES
    If the message is sent successfully, it returns the transactionid
    Raises an exception (MessageSendFailure) otherwise
    """
    # we may be called many times in asyncronous loops, so for now, it is safer not to share buffers. We can investifgate later whether this is really a problem.
    sbuf = rmr.rmr_alloc_msg(MRC, 4096)
    payload = payload if isinstance(payload, bytes) else payload.encode("utf-8")

    # retry RETRY_TIMES to send the message
    tried = 0
    while True:
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
            return transaction_id  # we are good
        if post_send_summary["message state"] == 10 and post_send_summary["message status"] == "RMR_ERR_RETRY":
            # in this state, we should retry
            if tried == RETRY_TIMES:
                # we have tried RETRY_TIMES and we are still not getting a good state, raise an exception and let the caller deal with it
                raise MessageSendFailure(str(post_send_summary))
            else:
                tried += 1
        else:
            # we hit a state where we should not even retry
            raise MessageSendFailure(str(post_send_summary))


def send_ack_retry(payload, expected_ack_message_type, message_type=0):
    """
    send a message and check for an ACK.
    If no ACK is recieved, defer execution for RMR_RCV_RETRY_INTERVAL ms, then check again.
    If no ack is received before the timeout (set by _rmr_init), send again and try again up to RETRY_TIMES

    It is critical here to set the RMR_TIMEOUT to 0 in the rmr_rcv_to function, which causes that function NOT to block.
    Instead, if the message isn't there, we give up execution for the interval, which allows the gevent server to process other requests in the meantime.

    Amazing props to https://sdiehl.github.io/gevent-tutorial/
    (which also runs this whole server)
    """

    # try to send the msg to the downstream policy handler
    expected_transaction_id = send(payload, message_type)
    WAITING_TRANSIDS[expected_transaction_id] = 1

    gevent.sleep(0.01)  # wait 10ms before we try the first recieve
    for _ in range(0, RETRY_TIMES):
        logger.debug("Seeing if return message is fufilled")
        summary = _check_if_ack_received(expected_transaction_id, expected_ack_message_type)
        if summary:
            logger.debug("Target ack Message received!: %s", summary)
            logger.debug("current queue size is %d", len(RECEIVED_MESSAGES))
            del WAITING_TRANSIDS[expected_transaction_id]
            return summary["payload"]
        else:
            logger.debug("Deffering execution for %s seconds", str(RMR_RCV_RETRY_INTERVAL / 1000))
            gevent.sleep(RMR_RCV_RETRY_INTERVAL / 1000)

    # we still didn't get the ACK we want
    raise ExpectedAckNotReceived()
