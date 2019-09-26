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
Represents A1s database and database access functions.
In the future, this may change to use a different backend, possibly dramatically.
Hopefully, the access functions are a good api so nothing else has to change when this happens

For now, the database is in memory.
We use dict data structures (KV) with the expectation of having to move this into Redis
"""
from a1.exceptions import PolicyTypeNotFound, PolicyInstanceNotFound, PolicyTypeAlreadyExists
from a1 import get_module_logger
from a1 import a1rmr
import json

logger = get_module_logger(__name__)

# This is essentially mockouts for future KV
# Note that the D subkey won't be needed when in redis, since you can store data at x anx x_y
POLICY_DATA = {}
I = "instances"
H = "handlers"
D = "data"


# Types


def type_is_valid(policy_type_id):
    """
    check that a type is valid
    """
    if policy_type_id not in POLICY_DATA:
        logger.error("%s not found", policy_type_id)
        raise PolicyTypeNotFound()


def store_policy_type(policy_type_id, body):
    """
    store a policy type if it doesn't already exist
    """
    if policy_type_id in POLICY_DATA:
        raise PolicyTypeAlreadyExists()

    POLICY_DATA[policy_type_id] = {}
    POLICY_DATA[policy_type_id][D] = body
    POLICY_DATA[policy_type_id][I] = {}


def get_policy_type(policy_type_id):
    """
    retrieve a type
    """
    type_is_valid(policy_type_id)
    return POLICY_DATA[policy_type_id][D]


def get_type_list():
    """
    retrieve all type ids
    """
    return list(POLICY_DATA.keys())


# Instances


def instance_is_valid(policy_type_id, policy_instance_id):
    """
    check that an instance is valid
    """
    type_is_valid(policy_type_id)
    if policy_instance_id not in POLICY_DATA[policy_type_id][I]:
        raise PolicyInstanceNotFound


def store_policy_instance(policy_type_id, policy_instance_id, instance):
    """
    Store a policy instance
    """
    type_is_valid(policy_type_id)

    # store the instance
    # Reset the statuses because this is a new policy instance, even if it was overwritten
    POLICY_DATA[policy_type_id][I][policy_instance_id] = {}
    POLICY_DATA[policy_type_id][I][policy_instance_id][D] = instance
    POLICY_DATA[policy_type_id][I][policy_instance_id][H] = {}


def delete_policy_instance_if_applicable(policy_type_id, policy_instance_id):
    """
    delete a policy instance if all known statuses are DELETED

    pops a1s waiting mailbox
    """
    # pop through a1s mailbox, updating a1s db of all policy statuses
    for msg in a1rmr.dequeue_all_waiting_messages(21024):
        # try to parse the messages as responses. Drop those that are malformed
        # NOTE: we don't use the parameters "policy_type_id, policy_instance" from above here,
        # because we are popping the whole mailbox, which might include other statuses
        pay = json.loads(msg["payload"])
        if "policy_type_id" in pay and "policy_instance_id" in pay and "handler_id" in pay and "status" in pay:
            set_policy_instance_status(pay["policy_type_id"], pay["policy_instance_id"], pay["handler_id"], pay["status"])
        else:
            logger.debug("Dropping message")
            logger.debug(pay)

    # raise if not valid
    instance_is_valid(policy_type_id, policy_instance_id)

    # see if we can delete
    vector = get_policy_instance_statuses(policy_type_id, policy_instance_id)
    if vector != []:
        all_deleted = True
        for i in vector:
            if i != "DELETED":
                all_deleted = False
                break  # have at least one not DELETED, do nothing

        # blow away from a1 db
        if all_deleted:
            del POLICY_DATA[policy_type_id][I][policy_instance_id]


def get_policy_instance(policy_type_id, policy_instance_id):
    """
    Retrieve a policy instance
    """
    instance_is_valid(policy_type_id, policy_instance_id)
    return POLICY_DATA[policy_type_id][I][policy_instance_id][D]


def get_policy_instance_statuses(policy_type_id, policy_instance_id):
    """
    Retrieve the status vector for a policy instance
    """
    instance_is_valid(policy_type_id, policy_instance_id)

    return [v for _, v in POLICY_DATA[policy_type_id][I][policy_instance_id][H].items()]


def set_policy_instance_status(policy_type_id, policy_instance_id, handler_id, status):
    """
    Update the status of a handler id of a policy instance
    """
    instance_is_valid(policy_type_id, policy_instance_id)

    POLICY_DATA[policy_type_id][I][policy_instance_id][H][handler_id] = status


def get_instance_list(policy_type_id):
    """
    retrieve all instance ids for a type
    """
    type_is_valid(policy_type_id)
    return list(POLICY_DATA[policy_type_id][I].keys())
