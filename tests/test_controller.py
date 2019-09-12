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
import tempfile
import os

from rmr.rmr_mocks import rmr_mocks
from a1 import app
import testing_helpers
import pytest


ADM_CTRL = "admission_control_policy"
ADM_CTRL_INSTANCE = "/a1-p/policytypes/20000/policies/" + ADM_CTRL
ADM_CTRL_INSTANCE_STATUS = ADM_CTRL_INSTANCE + "/status"


# http://flask.pocoo.org/docs/1.0/testing/
@pytest.fixture
def client():
    db_fd, app.app.config["DATABASE"] = tempfile.mkstemp()
    app.app.config["TESTING"] = True
    cl = app.app.test_client()

    yield cl

    os.close(db_fd)
    os.unlink(app.app.config["DATABASE"])


def _fake_dequeue(_filter_type):
    """
    for monkeypatching a1rmnr.dequeue_all_messages
    """
    fake_msg = {}
    pay = b'{"policy_type_id": 20000, "policy_instance_id": "admission_control_policy", "handler_id": "test_receiver", "status": "OK"}'
    fake_msg["payload"] = pay
    new_messages = [fake_msg]
    return new_messages


def _test_put_patch(monkeypatch):
    testing_helpers.patch_all(monkeypatch)
    monkeypatch.setattr("rmr.rmr.rmr_send_msg", rmr_mocks.send_mock_generator(0))  # good sends for this whole batch

    # we need to repatch alloc (already patched in patch_rmr) to fix the transactionid, alloc is called in send and recieve
    def fake_alloc(_unused, _alsounused):
        sbuf = rmr_mocks.Rmr_mbuf_t()
        sbuf.contents.xaction = b"d49b53e478b711e9a1130242ac110002"
        return sbuf

    # we also need to repatch set, since in the send function, we alloc, then set a new transid
    def fake_set_transactionid(sbuf):
        sbuf.contents.xaction = b"d49b53e478b711e9a1130242ac110002"

    # Note, we could have just patched summary, but this patches at a "lower level" so is a better test
    monkeypatch.setattr("rmr.rmr.rmr_alloc_msg", fake_alloc)
    monkeypatch.setattr("rmr.rmr.generate_and_set_transaction_id", fake_set_transactionid)


# Actual Tests


# def test_policy_get(client, monkeypatch):
#     """
#     test policy GET
#     """
#     _test_put_patch(monkeypatch)
#     monkeypatch.setattr(
#         "a1.a1rmr.dequeue_all_waiting_messages",
#         _fake_dequeue(monkeypatch, msg_payload={"GET ack": "pretend policy is here"}, msg_type=20003),
#     )
#     res = client.get("/a1-p/policies/admission_control_policy")
#     assert res.status_code == 200
#     assert res.json == {"GET ack": "pretend policy is here"}
#
#
# def test_policy_get_unsupported(client, monkeypatch):
#     """
#     test policy GET
#     """
#     testing_helpers.patch_all(monkeypatch, nofetch=True)
#     res = client.get("/a1-p/policies/admission_control_policy")
#     assert res.status_code == 400
#     assert res.data == b'"POLICY DOES NOT SUPPORT FETCHING"\n'
#
#
def test_xapp_put_good(client, monkeypatch):
    """ test policy put good"""

    # nothing there yet
    res = client.get(ADM_CTRL_INSTANCE)
    assert res.status_code == 404
    res = client.get(ADM_CTRL_INSTANCE_STATUS)
    assert res.status_code == 404

    # create a good instance
    _test_put_patch(monkeypatch)
    res = client.put(ADM_CTRL_INSTANCE, json=testing_helpers.good_payload())
    assert res.status_code == 201

    # get the instance
    res = client.get(ADM_CTRL_INSTANCE)
    assert res.status_code == 200
    assert res.json == testing_helpers.good_payload()

    # get the instance status
    monkeypatch.setattr("a1.a1rmr.dequeue_all_waiting_messages", _fake_dequeue)
    res = client.get(ADM_CTRL_INSTANCE_STATUS)
    assert res.status_code == 200
    assert res.json == [{"handler_id": "test_receiver", "status": "OK"}]

    # assert that rmr bad states don't cause problems
    monkeypatch.setattr("rmr.rmr.rmr_send_msg", rmr_mocks.send_mock_generator(10))
    res = client.put(ADM_CTRL_INSTANCE, json=testing_helpers.good_payload())
    assert res.status_code == 201

    monkeypatch.setattr("rmr.rmr.rmr_send_msg", rmr_mocks.send_mock_generator(5))
    res = client.put(ADM_CTRL_INSTANCE, json=testing_helpers.good_payload())
    assert res.status_code == 201


#
#
# def test_xapp_put_bad(client, monkeypatch):
#     """Test policy put fails"""
#     _test_put_patch(monkeypatch)
#     # return from policy handler has a status indicating FAIL
#     monkeypatch.setattr(
#         "a1.a1rmr.dequeue_all_waiting_messages", _fake_dequeue(monkeypatch, msg_payload={"status": "FAIL", "foo": "bar"})
#     )
#     res = client.put("/a1-p/policies/admission_control_policy", json=testing_helpers.good_payload())
#     assert res.status_code == 502
#     assert res.json["reason"] == "BAD STATUS"
#     assert res.json["return_payload"] == {"status": "FAIL", "foo": "bar"}
#
#     # return from policy handler has no status field
#     monkeypatch.setattr("a1.a1rmr.dequeue_all_waiting_messages", _fake_dequeue(monkeypatch, msg_payload={"foo": "bar"}))
#     res = client.put("/a1-p/policies/admission_control_policy", json=testing_helpers.good_payload())
#     assert res.status_code == 502
#     assert res.json["reason"] == "NO STATUS"
#     assert res.json["return_payload"] == {"foo": "bar"}
#
#     # return from policy handler not a json
#     monkeypatch.setattr(
#         "a1.a1rmr.dequeue_all_waiting_messages", _fake_dequeue(monkeypatch, msg_payload="booger", jsonb=False)
#     )
#     res = client.put("/a1-p/policies/admission_control_policy", json=testing_helpers.good_payload())
#     assert res.status_code == 502
#     assert res.json["reason"] == "NOT JSON"
#     assert res.json["return_payload"] == "booger"
#
#     # bad type
#     monkeypatch.setattr("a1.a1rmr.dequeue_all_waiting_messages", _fake_dequeue(monkeypatch, msg_type=666))
#     res = client.put("/a1-p/policies/admission_control_policy", json=testing_helpers.good_payload())
#     assert res.status_code == 504
#     assert res.data == b"\"A1 was expecting an ACK back but it didn't receive one or didn't recieve the expected ACK\"\n"
#
#     # bad state
#     monkeypatch.setattr("a1.a1rmr.dequeue_all_waiting_messages", _fake_dequeue(monkeypatch, msg_state=666))
#     res = client.put("/a1-p/policies/admission_control_policy", json=testing_helpers.good_payload())
#     assert res.status_code == 504
#     assert res.data == b"\"A1 was expecting an ACK back but it didn't receive one or didn't recieve the expected ACK\"\n"
#
#
def test_bad_requests(client, monkeypatch):
    """
    Test bad send failures
    """
    testing_helpers.patch_all(monkeypatch)
    res = client.put(ADM_CTRL_INSTANCE, json={"not": "expected"})
    assert res.status_code == 400

    # bad media type
    res = client.put(ADM_CTRL_INSTANCE, data="notajson")
    assert res.status_code == 415

    # test a PUT body against a poliucy not expecting one
    res = client.put("/a1-p/policytypes/20001/policies/test_policy", json=testing_helpers.good_payload())
    assert res.status_code == 400
    assert res.data == b'"BODY SUPPLIED BUT POLICY HAS NO EXPECTED BODY"\n'


# def test_bad_requests(client, monkeypatch):
#     """Test bad requests"""
#     testing_helpers.patch_all(monkeypatch)
#
#     # test a 404
#     res = client.put("/a1-p/policies/noexist", json=testing_helpers.good_payload())
#     assert res.status_code == 404


# def test_missing_manifest(client, monkeypatch):
#     """
#     test that we get a 500 with an approrpiate message on a missing manifest
#     """
#
#     def f():
#         raise exceptions.MissingManifest()
#
#     monkeypatch.setattr("a1.utils.get_ric_manifest", f)
#
#     res = client.put("/a1-p/policies/admission_control_policy", json=testing_helpers.good_payload())
#     assert res.status_code == 500
#     assert res.data == b'"A1 was unable to find the required RIC manifest. report this!"\n'
#
#


def test_healthcheck(client):
    """
    test healthcheck
    """
    res = client.get("/a1-p/healthcheck")
    assert res.status_code == 200
