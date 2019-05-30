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
import time
import random
import string
import os
import signal
import sys
from rmr import rmr


DELAY_MS = int(os.environ.get("BOMBARD_DELAY_MS", 100))

# Init rmr
mrc = rmr.rmr_init(b"4565", rmr.RMR_MAX_RCV_BYTES, 0x00)
while rmr.rmr_ready(mrc) == 0:
    time.sleep(1)
    print("not yet ready")
rmr.rmr_set_stimeout(mrc, 2)
sbuf = rmr.rmr_alloc_msg(mrc, 256)


while True:
    # generate a random value between 1 and 256 bytes, then gen some random  bytes with several nulls thrown in
    val = "BOMBS AWAY".encode("utf8")
    rmr.set_payload_and_length(val, sbuf)
    rmr.generate_and_set_transaction_id(sbuf)
    sbuf.contents.state = 0
    sbuf.contents.mtype = random.choice([20001, 10001])
    print("Pre send summary: {}".format(rmr.message_summary(sbuf)))
    sbuf = rmr.rmr_send_msg(mrc, sbuf)
    print("Post send summary: {}".format(rmr.message_summary(sbuf)))
    time.sleep(0.001 * DELAY_MS)
