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
import json
from a1.exceptions import PolicyTypeNotFound, PolicyInstanceNotFound, PolicyTypeAlreadyExists, CantDeleteNonEmptyType
from a1 import get_module_logger
from a1 import a1rmr

logger = get_module_logger(__name__)

# This is essentially mockouts for future KV
# Note that the D subkey won't be needed when in redis, since you can store data at x anx x_y
POLICY_DATA = {}
I = "instances"
H = "handlers"
D = "data"


# Internal helpers


def _get_statuses(policy_type_id, policy_instance_id):
    """
    shared helper to get statuses for an instance
    """
    instance_is_valid(policy_type_id, policy_instance_id)
    return [v for _, v in POLICY_DATA[policy_type_id][I][policy_instance_id][H].items()]


def _get_instance_list(policy_type_id):
    """
    shared helper to get instance list for a type
    """
    type_is_valid(policy_type_id)
    return list(POLICY_DATA[policy_type_id][I].keys())


def _clean_up_type(policy_type_id):
    """
    pop through a1s mailbox, updating a1s db of all policy statuses
    for all instances of type, see if it can be deleted
    """
    type_is_valid(policy_type_id)
    for msg in a1rmr.dequeue_all_waiting_messages([21024]):
        # try to parse the messages as responses. Drop those that are malformed
        pay = json.loads(msg["payload"])
        if "policy_type_id" in pay and "policy_instance_id" in pay and "handler_id" in pay and "status" in pay:
            """
            NOTE: can't raise an exception here e.g.:
                instance_is_valid(pti, pii)
            because this is called on many functions; just drop bad status messages.
            We def don't want bad messages that happen to hit a1s mailbox to blow up anything

            NOTE2: we don't use the parameters "policy_type_id, policy_instance" from above here,
            # because we are popping the whole mailbox, which might include other statuses
            """
            pti = pay["policy_type_id"]
            pii = pay["policy_instance_id"]
            if pti in POLICY_DATA and pii in POLICY_DATA[pti][I]:  # manual check per comment above
                POLICY_DATA[pti][I][pii][H][pay["handler_id"]] = pay["status"]
        else:
            logger.debug("Dropping message")
            logger.debug(pay)

    for policy_instance_id in _get_instance_list(policy_type_id):
        # see if we can delete
        vector = _get_statuses(policy_type_id, policy_instance_id)

        """
        TODO: not being able to delete if the list is [] is prolematic.
        There are cases, such as a bad routing file, where this type will never be able to be deleted because it never went to any xapps
        However, A1 cannot distinguish between the case where [] was never going to work, and the case where it hasn't worked *yet*

        However, removing this constraint also leads to problems.
        Deleting the instance when the vector is empty, for example doing so “shortly after” the PUT, can lead to a worse race condition where the xapps get the policy after that, implement it, but because the DELETE triggered “too soon”, you can never get the status or do the delete on it again, so the xapps are all implementing the instance roguely.

        This requires some thought to address.
        For now we stick with the "less bad problem".
        """
        if vector != []:
            all_deleted = True
            for i in vector:
                if i != "DELETED":
                    all_deleted = False
                    break  # have at least one not DELETED, do nothing

            # blow away from a1 db
            if all_deleted:
                del POLICY_DATA[policy_type_id][I][policy_instance_id]


# Types


def get_type_list():
    """
    retrieve all type ids
    """
    return list(POLICY_DATA.keys())


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


def delete_policy_type(policy_type_id):
    """
    delete a policy type; can only be done if there are no instances (business logic)
    """
    pil = get_instance_list(policy_type_id)
    if pil == []:  # empty, can delete
        del POLICY_DATA[policy_type_id]
    else:
        raise CantDeleteNonEmptyType()


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
    _clean_up_type(policy_type_id)
    instance_is_valid(policy_type_id, policy_instance_id)
    return POLICY_DATA[policy_type_id][I][policy_instance_id][D]


def get_policy_instance_statuses(policy_type_id, policy_instance_id):
    """
    Retrieve the status vector for a policy instance
    """
    _clean_up_type(policy_type_id)
    return _get_statuses(policy_type_id, policy_instance_id)


def get_instance_list(policy_type_id):
    """
    retrieve all instance ids for a type
    """
    _clean_up_type(policy_type_id)
    return _get_instance_list(policy_type_id)
