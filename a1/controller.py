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
from flask import Response
import connexion
import json
from jsonschema.exceptions import ValidationError
from a1 import get_module_logger
from a1 import a1rmr, exceptions, utils


logger = get_module_logger(__name__)


def _get_policy_definition(policyname):
    # Currently we read the manifest on each call, which would seem to allow updating A1 in place. Revisit this?
    manifest = utils.get_ric_manifest()
    for m in manifest["controls"]:
        if m["name"] == policyname:
            return m
    raise exceptions.PolicyNotFound()


def _get_needed_policy_info(policyname):
    """
    Get the needed info for a policy
    """
    m = _get_policy_definition(policyname)
    return (
        utils.rmr_string_to_int(m["message_receives_rmr_type"]),
        m["message_receives_payload_schema"] if "message_receives_payload_schema" in m else None,
        utils.rmr_string_to_int(m["message_sends_rmr_type"]),
    )


def _get_needed_policy_fetch_info(policyname):
    """
    Get the needed info for fetching a policy state
    """
    m = _get_policy_definition(policyname)
    req_k = "control_state_request_rmr_type"
    ack_k = "control_state_request_reply_rmr_type"
    return (
        utils.rmr_string_to_int(m[req_k]) if req_k in m else None,
        utils.rmr_string_to_int(m[ack_k]) if ack_k in m else None,
    )


def _try_func_return(func):
    """
    generic caller that returns the apporp http response if exceptions are raised
    """
    try:
        return func()
    except ValidationError as exc:
        logger.exception(exc)
        return "", 400
    except exceptions.PolicyNotFound as exc:
        logger.exception(exc)
        return "", 404
    except exceptions.MissingManifest as exc:
        logger.exception(exc)
        return "A1 was unable to find the required RIC manifest. report this!", 500
    except exceptions.MissingRmrString as exc:
        logger.exception(exc)
        return "A1 does not have a mapping for the desired rmr string. report this!", 500
    except exceptions.MessageSendFailure as exc:
        logger.exception(exc)
        return "A1 was unable to send a needed message to a downstream subscriber", 504
    except exceptions.ExpectedAckNotReceived as exc:
        logger.exception(exc)
        return "A1 was expecting an ACK back but it didn't receive one or didn't recieve the expected ACK", 504
    except BaseException as exc:
        # catch all, should never happen...
        logger.exception(exc)
        return Response(status=500)


def _put_handler(policyname, data):
    """
    Handles policy put
    """

    mtype_send, schema, mtype_return = _get_needed_policy_info(policyname)

    # validate the PUT against the schema, or if there is no shema, make sure the pUT is empty
    if schema:
        utils.validate_json(data, schema)
    elif data != {}:
        return "BODY SUPPLIED BUT POLICY HAS NO EXPECTED BODY", 400

    # send rmr, wait for ACK
    return_payload = a1rmr.send_ack_retry(json.dumps(data), message_type=mtype_send, expected_ack_message_type=mtype_return)

    # right now it is assumed that xapps respond with JSON payloads
    # it is further assumed that they include a field "status" and that the value "SUCCESS" indicates a good policy change
    try:
        rpj = json.loads(return_payload)
        return (rpj, 200) if rpj["status"] == "SUCCESS" else ({"reason": "BAD STATUS", "return_payload": rpj}, 502)
    except json.decoder.JSONDecodeError:
        return {"reason": "NOT JSON", "return_payload": return_payload}, 502
    except KeyError:
        return {"reason": "NO STATUS", "return_payload": rpj}, 502


def _get_handler(policyname):
    """
    Handles policy GET
    """
    mtype_send, mtype_return = _get_needed_policy_fetch_info(policyname)

    if not (mtype_send and mtype_return):
        return "POLICY DOES NOT SUPPORT FETCHING", 400

    # send rmr, wait for ACK
    return_payload = a1rmr.send_ack_retry("", message_type=mtype_send, expected_ack_message_type=mtype_return)

    # right now it is assumed that xapps respond with JSON payloads
    try:
        return (json.loads(return_payload), 200)
    except json.decoder.JSONDecodeError:
        return {"reason": "NOT JSON", "return_payload": return_payload}, 502


# Public


def put_handler(policyname):
    """
    Handles policy replacement
    """
    data = connexion.request.json
    return _try_func_return(lambda: _put_handler(policyname, data))


def get_handler(policyname):
    """
    Handles policy GET
    """
    return _try_func_return(lambda: _get_handler(policyname))


def healthcheck_handler():
    """
    Handles healthcheck GET
    Currently, this basically checks the server is alive.a1rmr
    """
    return "", 200
