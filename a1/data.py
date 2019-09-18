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


def get_policy_instance(policy_type_id, policy_instance_id):
    """
    Retrieve a policy instance
    """
    type_is_valid(policy_type_id)
    instance_is_valid(policy_type_id, policy_instance_id)
    return POLICY_DATA[policy_type_id][I][policy_instance_id][D]


def get_policy_instance_statuses(policy_type_id, policy_instance_id):
    """
    Retrieve the status vector for a policy instance
    """
    type_is_valid(policy_type_id)
    instance_is_valid(policy_type_id, policy_instance_id)

    return [{"handler_id": k, "status": v} for k, v in POLICY_DATA[policy_type_id][I][policy_instance_id][H].items()]


def set_policy_instance_status(policy_type_id, policy_instance_id, handler_id, status):
    """
    Update the status of a handler id of a policy instance
    """
    type_is_valid(policy_type_id)
    instance_is_valid(policy_type_id, policy_instance_id)

    POLICY_DATA[policy_type_id][I][policy_instance_id][H][handler_id] = status
