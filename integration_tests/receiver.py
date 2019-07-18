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
RETURN_MINT = int(os.environ.get("TEST_RCV_RETURN_MINT", 20001))
RETURN_MINT_FETCH = int(os.environ.get("TEST_RCV_RETURN_MINT", 20003))
DELAY = int(os.environ.get("TEST_RCV_SEC_DELAY", 0))
PAYLOAD_RETURNED = json.loads(
    os.environ.get("TEST_RCV_RETURN_PAYLOAD", '{"ACK_FROM": "ADMISSION_CONTROL", "status": "SUCCESS"}')
)

# TODO: should these be made constants?
mrc = rmr.rmr_init(PORT.encode("utf-8"), rmr.RMR_MAX_RCV_BYTES, 0x00)

while rmr.rmr_ready(mrc) == 0:
    time.sleep(1)
    print("not yet ready")

print("listening")
sbuf = None
while True:
    sbuf = rmr.rmr_torcv_msg(mrc, sbuf, 1000)
    summary = rmr.message_summary(sbuf)
    if summary["message state"] == 12 and summary["message status"] == "RMR_ERR_TIMEOUT":
        # print("Nothing received yet")
        time.sleep(1)
    else:
        print("Message received!: {}".format(summary))

        # if this was a policy fetch (request int =20002), override the payload and return int
        if summary["message type"] == 20002:
            PAYLOAD_RETURNED = {"mock return from FETCH": "pretend policy is here"}
            RETURN_MINT = 20003

        val = json.dumps(PAYLOAD_RETURNED).encode("utf-8")
        rmr.set_payload_and_length(val, sbuf)
        sbuf.contents.mtype = RETURN_MINT
        print("Pre reply summary: {}".format(rmr.message_summary(sbuf)))
        time.sleep(DELAY)
        sbuf = rmr.rmr_rts_msg(mrc, sbuf)
        print("Post reply summary: {}".format(rmr.message_summary(sbuf)))
