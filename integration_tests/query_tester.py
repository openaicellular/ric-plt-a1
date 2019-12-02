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
"""
Test receiver
"""

import time
import json
from rmr import rmr

PORT = "4564"

mrc = rmr.rmr_init(PORT.encode("utf-8"), rmr.RMR_MAX_RCV_BYTES, rmr.RMRFL_MTCALL)
test_type = 1006001

while rmr.rmr_ready(mrc) == 0:
    time.sleep(1)
    print("not yet ready")

print("listening ON {}".format(PORT))

# loop
while True:

    # do query
    pay = {"policy_type_id": test_type}
    sbuf_send = rmr.rmr_alloc_msg(mrc, 4096, payload=json.dumps(pay).encode("utf-8"), gen_transaction_id=True, mtype=20012)
    sbuf_send = rmr.rmr_send_msg(mrc, sbuf_send)
    post_send_summary = rmr.message_summary(sbuf_send)

    if not (post_send_summary["message state"] == 0 and post_send_summary["message status"] == "RMR_OK"):
        print("was unable to send query to a1!")
        time.sleep(1)
    else:
        # query worked, wait 2 seconds, then receive everything we have
        time.sleep(1)
        print("reading messages")

        # this is a hacked up version of rmr_rcvall_msgs in the rmr package
        # we need the actual messages, not the summaries, to use rts
        sbuf_rcv = rmr.rmr_alloc_msg(mrc, 4096)  # allocate buffer to have something for a return status
        while True:
            sbuf_rcv = rmr.rmr_torcv_msg(mrc, sbuf_rcv, 0)  # set the timeout to 0 so this doesn't block!!

            summary = rmr.message_summary(sbuf_rcv)
            if summary["message status"] != "RMR_OK":  # ok indicates msg received, stop on all other states
                print("no more instances received. will try again in 1s")
                break

            print("Received: {0}".format(summary))

            received_payload = json.loads(summary["payload"])
            assert received_payload["policy_type_id"] == test_type
            assert summary["message type"] == 20010

            payload = {
                "policy_type_id": received_payload["policy_type_id"],
                "policy_instance_id": received_payload["policy_instance_id"],
                "handler_id": "query_tester",
                "status": "OK",
            }
            val = json.dumps(payload).encode("utf-8")
            rmr.set_payload_and_length(val, sbuf_rcv)  # TODO: extend rmr-python to allow rts to accept this param
            sbuf_rcv.contents.mtype = 20011  # TODO: extend rmr-python to allow rts to accept this param
            print("Pre reply summary: {}".format(rmr.message_summary(sbuf_rcv)))

            # send ack
            sbuf_rcv = rmr.rmr_rts_msg(mrc, sbuf_rcv)
            post_reply_summary = rmr.message_summary(sbuf_rcv)
            print("Post reply summary: {}".format(post_reply_summary))
