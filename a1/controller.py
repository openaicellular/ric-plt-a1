"""
Main a1 controller
"""
# ==================================================================================
#       Copyright (c) 2019-2020 Nokia
#       Copyright (c) 2018-2020 AT&T Intellectual Property.
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
from jsonschema import validate
from jsonschema.exceptions import ValidationError
import connexion
from mdclogpy import Logger
from ricsdl.exceptions import RejectedByBackend, NotConnected, BackendError
from a1 import a1rmr, exceptions, data


mdc_logger = Logger(name=__name__)


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
    except (RejectedByBackend, NotConnected, BackendError):
        """
        These are SDL errors. At the time of development here, we do not have a good understanding which of these errors are "try again later it may work"
        and which are "never going to work". There is some discussion that RejectedByBackend is in the latter category, suggesting it should map to 400,
        but until we understand the root cause of these errors, it's confusing to clients to give them a 400 (a "your fault" code) because they won't know how to fix
        For now, we log, and 503, and investigate the logs later to improve the handling/reporting.
        """
        # mdc_logger.exception(exc)  # waiting for https://jira.o-ran-sc.org/browse/RIC-39
        return "", 503

    # let other types of unexpected exceptions blow up and log


# Healthcheck


def get_healthcheck():
    """
    Handles healthcheck GET
    Currently, this checks:
    1. whether the a1 webserver is up (if it isn't, this won't even be called, so even entering this function confirms it is)
    2. checks whether the rmr thread is running and has completed a loop recently
    TODO: make "seconds" to pass in a configurable parameter?
    """
    if a1rmr.healthcheck_rmr_thread():
        return "", 200
    return "rmr thread is unhealthy", 500


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

    return _try_func_return(lambda: data.get_policy_instance_status(policy_type_id, policy_instance_id))


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

        # queue rmr send (best effort)
        a1rmr.queue_instance_send(("CREATE", policy_type_id, policy_instance_id, instance))

        return "", 202

    return _try_func_return(put_instance_handler)


def delete_policy_instance(policy_type_id, policy_instance_id):
    """
    Handles DELETE /a1-p/policytypes/polidyid/policies/policy_instance_id
    """

    def delete_instance_handler():
        """
        here we send out the DELETEs but we don't delete the instance until a GET is called where we check the statuses
        We also set the status as deleted which would be reflected in a GET to ../status (before the DELETE completes)
        """
        data.delete_policy_instance(policy_type_id, policy_instance_id)

        # queue rmr send (best effort)
        a1rmr.queue_instance_send(("DELETE", policy_type_id, policy_instance_id, ""))

        return "", 202

    return _try_func_return(delete_instance_handler)
