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
import pytest
import jsonschema
from a1 import utils, exceptions
import testing_helpers


def test_bad_get_ric_manifest(monkeypatch):
    """
    testing missing manifest
    """

    def badopen(filename, mode):
        raise FileNotFoundError()

    monkeypatch.setattr("builtins.open", badopen)
    with pytest.raises(exceptions.MissingManifest):
        utils.get_ric_manifest()


def test_good_get_ric_manifest(monkeypatch):
    """
    test get_ric_manifest
    """
    testing_helpers.patch_all(monkeypatch)
    utils.get_ric_manifest()


def test_validate(monkeypatch):
    """
    test json validation wrapper
    """
    testing_helpers.patch_all(monkeypatch)
    ricmanifest = utils.get_ric_manifest()
    schema = ricmanifest["controls"][0]["message_receives_payload_schema"]
    utils.validate_json(testing_helpers.good_payload(), schema)
    with pytest.raises(jsonschema.exceptions.ValidationError):
        utils.validate_json({"dc_admission_start_time": "10:00:00", "dc_admission_end_time": "nevergonnagiveyouup"}, schema)
