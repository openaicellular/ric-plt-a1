"""
Main a1 controller
"""
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
from flask import Response
from jsonschema import validate
from jsonschema.exceptions import ValidationError
import connexion
from a1 import get_module_logger
from a1 import a1rmr, exceptions, data


logger = get_module_logger(__name__)


def _try_func_return(func):
    """
    generic caller that returns the apporp http response if exceptions are raised
    """
    try:
        return func()
    except (ValidationError, exceptions.PolicyTypeAlreadyExists, exceptions.CantDeleteNonEmptyType):
        return "", 400
    except (exceptions.PolicyTypeNotFound, exceptions.PolicyInstanceNotFound):
        return "", 404
    except BaseException as exc:
        # catch all, should never happen...
        logger.exception(exc)
        return Response(status=500)


def _gen_body_to_handler(operation, policy_type_id, policy_instance_id, payload=None):
    """
    used to create the payloads that get sent to downstream policy handlers
    """
    return {
        "operation": operation,
        "policy_type_id": policy_type_id,
        "policy_instance_id": policy_instance_id,
        "payload": payload,
    }


# Healthcheck


def get_healthcheck():
    """
    Handles healthcheck GET
    Currently, this basically checks the server is alive
    """
    return "", 200


# Policy types


def get_all_policy_types():
    """
    Handles GET /a1-p/policytypes
    """
    return _try_func_return(data.get_type_list)


def create_policy_type(policy_type_id):
    """
    Handles PUT /a1-p/policytypes/policy_type_id
    """

    def put_type_handler():
        data.store_policy_type(policy_type_id, body)
        return "", 201

    body = connexion.request.json
    return _try_func_return(put_type_handler)


def get_policy_type(policy_type_id):
    """
    Handles GET /a1-p/policytypes/policy_type_id
    """
    return _try_func_return(lambda: data.get_policy_type(policy_type_id))


def delete_policy_type(policy_type_id):
    """
    Handles DELETE /a1-p/policytypes/policy_type_id
    """

    def delete_policy_type_handler():
        data.delete_policy_type(policy_type_id)
        return "", 204

    return _try_func_return(delete_policy_type_handler)


# Policy instances


def get_all_instances_for_type(policy_type_id):
    """
    Handles GET /a1-p/policytypes/policy_type_id/policies
    """
    return _try_func_return(lambda: data.get_instance_list(policy_type_id))


def get_policy_instance(policy_type_id, policy_instance_id):
    """
    Handles GET /a1-p/policytypes/polidyid/policies/policy_instance_id
    """
    return _try_func_return(lambda: data.get_policy_instance(policy_type_id, policy_instance_id))


def get_policy_instance_status(policy_type_id, policy_instance_id):
    """
    Handles GET /a1-p/policytypes/polidyid/policies/policy_instance_id/status

    Return the aggregated status. The order of rules is as follows:
        1. If a1 has received at least one status, and *all* received statuses are "DELETED", we blow away the instance and return a 404
        2. if a1 has received at least one status and at least one is OK, we return "IN EFFECT"
        3. "NOT IN EFFECT" otherwise (no statuses, or none are OK but not all are deleted)
    """

    def get_status_handler():
        vector = data.get_policy_instance_statuses(policy_type_id, policy_instance_id)
        for i in vector:
            if i == "OK":
                return "IN EFFECT", 200
        return "NOT IN EFFECT", 200

    return _try_func_return(get_status_handler)


def create_or_replace_policy_instance(policy_type_id, policy_instance_id):
    """
    Handles PUT /a1-p/policytypes/polidyid/policies/policy_instance_id
    """
    instance = connexion.request.json

    def put_instance_handler():
        """
        Handles policy instance put

        For now, policy_type_id is used as the message type
        """
        #  validate the PUT against the schema
        schema = data.get_policy_type(policy_type_id)["create_schema"]
        validate(instance=instance, schema=schema)

        # store the instance
        data.store_policy_instance(policy_type_id, policy_instance_id, instance)

        # send rmr (best effort)
        body = _gen_body_to_handler("CREATE", policy_type_id, policy_instance_id, payload=instance)
        a1rmr.queue_work({"payload": json.dumps(body), "msg type": policy_type_id})

        return "", 202

    return _try_func_return(put_instance_handler)


def delete_policy_instance(policy_type_id, policy_instance_id):
    """
    Handles DELETE /a1-p/policytypes/polidyid/policies/policy_instance_id
    """

    def delete_instance_handler():
        """
        here we send out the DELETEs but we don't delete the instance until a GET is called where we check the statuses
        """
        data.instance_is_valid(policy_type_id, policy_instance_id)

        # send rmr (best effort)
        body = _gen_body_to_handler("DELETE", policy_type_id, policy_instance_id)
        a1rmr.queue_work({"payload": json.dumps(body), "msg type": policy_type_id})

        return "", 202

    return _try_func_return(delete_instance_handler)
