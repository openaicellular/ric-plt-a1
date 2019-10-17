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
from rmr.rmr_mocks import rmr_mocks
from a1 import run


ADM_CTRL = "admission_control_policy"
ADM_CTRL_POLICIES = "/a1-p/policytypes/20000/policies"
ADM_CTRL_INSTANCE = ADM_CTRL_POLICIES + "/" + ADM_CTRL
ADM_CTRL_INSTANCE_STATUS = ADM_CTRL_INSTANCE + "/status"
ADM_CTRL_TYPE = "/a1-p/policytypes/20000"
TEST_TYPE = "/a1-p/policytypes/20001"


def _fake_dequeue(_mrc, _filter_type):
    """for monkeypatching with a good status"""
    fake_msg = {}
    pay = b'{"policy_type_id": 20000, "policy_instance_id": "admission_control_policy", "handler_id": "test_receiver", "status": "OK"}'
    fake_msg["payload"] = pay
    new_messages = [fake_msg]
    return new_messages


def _fake_dequeue_none(_mrc, _filter_type):
    """for monkeypatching with no waiting messages"""
    return []


def _fake_dequeue_deleted(_mrc, _filter_type):
    """for monkeypatching  with a DELETED status"""
    new_msgs = []

    # insert some that don't exist to make sure nothing blows up
    pay = b'{"policy_type_id": 20666, "policy_instance_id": "admission_control_policy", "handler_id": "test_receiver", "status": "DELETED"}'
    fake_msg = {"payload": pay}
    new_msgs.append(fake_msg)

    pay = b'{"policy_type_id": 20000, "policy_instance_id": "darkness", "handler_id": "test_receiver", "status": "DELETED"}'
    fake_msg = {"payload": pay}
    new_msgs.append(fake_msg)

    pay = b'{"policy_type_id": 20000, "policy_instance_id": "admission_control_policy", "handler_id": "test_receiver", "status": "DELETED"}'
    fake_msg = {"payload": pay}
    new_msgs.append(fake_msg)

    return new_msgs


def _test_put_patch(monkeypatch):
    rmr_mocks.patch_rmr(monkeypatch)
    # assert that rmr bad states don't cause problems
    monkeypatch.setattr("rmr.rmr.rmr_send_msg", rmr_mocks.send_mock_generator(10))

    # we need this because free expects a real sbuf
    # TODO: move this into rmr_mocks
    def noop(_sbuf):
        pass

    monkeypatch.setattr("rmr.rmr.rmr_free_msg", noop)

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


# Module level Hack


RMR_THREAD = None


def setup_module():
    """module level setup"""
    global RMR_THREAD
    RMR_THREAD = run.start_rmr_thread(real_init=False)


# Actual Tests


def test_workflow_nothing_there_yet(client, monkeypatch, adm_type_good, adm_instance_good):
    """ test policy put good"""
    monkeypatch.setattr("rmr.helpers.rmr_rcvall_msgs", _fake_dequeue_none)
    # no type there yet
    res = client.get(ADM_CTRL_TYPE)
    assert res.status_code == 404

    # no types at all
    res = client.get("/a1-p/policytypes")
    assert res.status_code == 200
    assert res.json == []

    # instance 404 because type not there yet
    res = client.get(ADM_CTRL_POLICIES)
    assert res.status_code == 404


def test_workflow(client, monkeypatch, adm_type_good, adm_instance_good):
    """
    test a full A1 workflow
    """
    monkeypatch.setattr("rmr.helpers.rmr_rcvall_msgs", _fake_dequeue_none)
    # put the type
    res = client.put(ADM_CTRL_TYPE, json=adm_type_good)
    assert res.status_code == 201

    # cant replace types
    res = client.put(ADM_CTRL_TYPE, json=adm_type_good)
    assert res.status_code == 400

    # type there now
    res = client.get(ADM_CTRL_TYPE)
    assert res.status_code == 200
    assert res.json == adm_type_good
    res = client.get("/a1-p/policytypes")
    assert res.status_code == 200
    assert res.json == [20000]

    # instance 200 but empty list
    res = client.get(ADM_CTRL_POLICIES)
    assert res.status_code == 200
    assert res.json == []

    # no instance there yet
    res = client.get(ADM_CTRL_INSTANCE)
    assert res.status_code == 404
    res = client.get(ADM_CTRL_INSTANCE_STATUS)
    assert res.status_code == 404

    # create a good instance
    _test_put_patch(monkeypatch)
    res = client.put(ADM_CTRL_INSTANCE, json=adm_instance_good)
    assert res.status_code == 202

    # replace is allowed on instances
    res = client.put(ADM_CTRL_INSTANCE, json=adm_instance_good)
    assert res.status_code == 202

    # instance 200 and in list
    res = client.get(ADM_CTRL_POLICIES)
    assert res.status_code == 200
    assert res.json == [ADM_CTRL]

    def get_instance_good(expected):
        # get the instance
        res = client.get(ADM_CTRL_INSTANCE)
        assert res.status_code == 200
        assert res.json == adm_instance_good

        # get the instance status
        res = client.get(ADM_CTRL_INSTANCE_STATUS)
        assert res.status_code == 200
        assert res.get_data(as_text=True) == expected

    # try a status get but we didn't get any ACKs yet to test NOT IN EFFECT
    time.sleep(1)  # wait for the rmr thread
    get_instance_good("NOT IN EFFECT")

    # now pretend we did get a good ACK
    monkeypatch.setattr("rmr.helpers.rmr_rcvall_msgs", _fake_dequeue)
    time.sleep(1)  # wait for the rmr thread
    get_instance_good("IN EFFECT")

    # cant delete type until there are no instances
    res = client.delete(ADM_CTRL_TYPE)
    assert res.status_code == 400

    # delete it
    res = client.delete(ADM_CTRL_INSTANCE)
    assert res.status_code == 202
    res = client.delete(ADM_CTRL_INSTANCE)  # should be able to do multiple deletes
    assert res.status_code == 202

    # status after a delete, but there are no messages yet, should still return
    monkeypatch.setattr("rmr.helpers.rmr_rcvall_msgs", _fake_dequeue)
    time.sleep(1)  # wait for the rmr thread
    get_instance_good("IN EFFECT")

    # now pretend we deleted successfully
    monkeypatch.setattr("rmr.helpers.rmr_rcvall_msgs", _fake_dequeue_deleted)
    time.sleep(1)  # wait for the rmr thread
    res = client.get(ADM_CTRL_INSTANCE_STATUS)  # cant get status
    assert res.status_code == 404
    res = client.get(ADM_CTRL_INSTANCE)  # cant get instance
    assert res.status_code == 404

    # list still 200 but no instance
    res = client.get(ADM_CTRL_POLICIES)
    assert res.status_code == 200
    assert res.json == []

    # delete the type
    res = client.delete(ADM_CTRL_TYPE)
    assert res.status_code == 204

    # cant touch this
    res = client.get(ADM_CTRL_TYPE)
    assert res.status_code == 404
    res = client.delete(ADM_CTRL_TYPE)
    assert res.status_code == 404


def test_bad_instances(client, monkeypatch, adm_type_good):
    """
    test various failure modes
    """
    # put the type (needed for some of the tests below)
    rmr_mocks.patch_rmr(monkeypatch)
    res = client.put(ADM_CTRL_TYPE, json=adm_type_good)
    assert res.status_code == 201

    # bad body
    res = client.put(ADM_CTRL_INSTANCE, json={"not": "expected"})
    assert res.status_code == 400

    # bad media type
    res = client.put(ADM_CTRL_INSTANCE, data="notajson")
    assert res.status_code == 415

    # delete a non existent instance
    res = client.delete(ADM_CTRL_INSTANCE + "DARKNESS")
    assert res.status_code == 404

    # get a non existent instance
    monkeypatch.setattr("rmr.helpers.rmr_rcvall_msgs", _fake_dequeue)
    time.sleep(1)
    res = client.get(ADM_CTRL_INSTANCE + "DARKNESS")
    assert res.status_code == 404

    # delete the type (as cleanup)
    res = client.delete(ADM_CTRL_TYPE)
    assert res.status_code == 204


def test_illegal_types(client, monkeypatch, adm_type_good):
    """
    Test illegal types
    """
    res = client.put("/a1-p/policytypes/19999", json=adm_type_good)
    assert res.status_code == 400
    res = client.put("/a1-p/policytypes/21024", json=adm_type_good)
    assert res.status_code == 400


def test_healthcheck(client):
    """
    test healthcheck
    """
    res = client.get("/a1-p/healthcheck")
    assert res.status_code == 200


def teardown_module():
    """module teardown"""
    RMR_THREAD.stop()
