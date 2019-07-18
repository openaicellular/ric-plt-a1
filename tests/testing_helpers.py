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
import json
import os
from rmr.rmr_mocks import rmr_mocks


def _get_fixture_path(name):
    cur_dir = os.path.dirname(os.path.realpath(__file__))
    return "{0}/fixtures/{1}".format(cur_dir, name)


def patch_all(monkeypatch, nonexisting_rmr=False, nofetch=False):
    rmr_mocks.patch_rmr(monkeypatch)

    # patch manifest
    man = json.loads(open(_get_fixture_path("ricmanifest.json"), "r").read())
    if nonexisting_rmr:
        man["controls"][0]["message_receives_rmr_type"] = "DARKNESS"

    if nofetch:
        del man["controls"][0]["control_state_request_rmr_type"]

    monkeypatch.setattr("a1.utils.get_ric_manifest", lambda: man)

    # patch rmr mapping
    mapping = open(_get_fixture_path("rmr_string_int_mapping.txt"), "r").readlines()
    monkeypatch.setattr("a1.utils._get_rmr_mapping_table", lambda: mapping)


def good_payload():
    return {"enforce": True, "window_length": 10, "blocking_rate": 20, "trigger_threshold": 10}
