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
import os
from rmr import rmr

PORT = os.environ.get("TEST_RCV_PORT", "4560")
DELAY = int(os.environ.get("TEST_RCV_SEC_DELAY", 0))
HANDLER_ID = os.environ.get("HANDLER_ID", "test_receiver")

# TODO: should these be made constants?
mrc = rmr.rmr_init(PORT.encode("utf-8"), rmr.RMR_MAX_RCV_BYTES, 0x00)

while rmr.rmr_ready(mrc) == 0:
    time.sleep(1)
    print("not yet ready")

print("listening ON {}".format(PORT))
sbuf = None
while True:
    sbuf = rmr.rmr_torcv_msg(mrc, sbuf, 1000)
    summary = rmr.message_summary(sbuf)
    if summary["message state"] == 12 and summary["message status"] == "RMR_ERR_TIMEOUT":
        # print("Nothing received yet")
        time.sleep(1)
    else:
        print("Message received!: {}".format(summary))

        received_payload = json.loads(summary["payload"])

        payload = {
            "policy_type_id": received_payload["policy_type_id"],
            "policy_instance_id": received_payload["policy_instance_id"],
            "handler_id": HANDLER_ID,
            "status": "OK",
        }

        val = json.dumps(payload).encode("utf-8")
        rmr.set_payload_and_length(val, sbuf)
        sbuf.contents.mtype = 21024
        print("Pre reply summary: {}".format(rmr.message_summary(sbuf)))
        time.sleep(DELAY)

        # try up to 5 times to send back the ack
        for _ in range(5):
            sbuf = rmr.rmr_rts_msg(mrc, sbuf)
            post_reply_summary = rmr.message_summary(sbuf)
            print("Post reply summary: {}".format(post_reply_summary))
            if post_reply_summary["message state"] == 10 and post_reply_summary["message status"] == "RMR_ERR_RETRY":
                time.sleep(1)
            else:
                break
