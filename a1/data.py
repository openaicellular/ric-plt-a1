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
import msgpack
from a1.exceptions import PolicyTypeNotFound, PolicyInstanceNotFound, PolicyTypeAlreadyExists, CantDeleteNonEmptyType
from a1 import get_module_logger

logger = get_module_logger(__name__)


class SDLWrapper:
    """
    This is a wrapper around the expected SDL Python interface.
    The usage of POLICY_DATA will be replaced with  SDL when SDL for python is available.
    The eventual SDL API is expected to be very close to what is here.

    We use msgpack for binary (de)serialization: https://msgpack.org/index.html
    """

    def __init__(self):
        self.POLICY_DATA = {}

    def set(self, key, value):
        """set a key"""
        self.POLICY_DATA[key] = msgpack.packb(value, use_bin_type=True)

    def get(self, key):
        """get a key"""
        if key in self.POLICY_DATA:
            return msgpack.unpackb(self.POLICY_DATA[key], raw=False)
        return None

    def find_and_get(self, prefix):
        """get all k v pairs that start with prefix"""
        return {k: msgpack.unpackb(v, raw=False) for k, v in self.POLICY_DATA.items() if k.startswith(prefix)}

    def delete(self, key):
        """ delete a key"""
        del self.POLICY_DATA[key]


SDL = SDLWrapper()

TYPE_PREFIX = "a1.policy_type."
INSTANCE_PREFIX = "a1.policy_instance."
HANDLER_PREFIX = "a1.policy_handler."


# Internal helpers


def _generate_type_key(policy_type_id):
    """
    generate a key for a policy type
    """
    return "{0}{1}".format(TYPE_PREFIX, policy_type_id)


def _generate_instance_key(policy_type_id, policy_instance_id):
    """
    generate a key for a policy instance
    """
    return "{0}{1}.{2}".format(INSTANCE_PREFIX, policy_type_id, policy_instance_id)


def _generate_handler_prefix(policy_type_id, policy_instance_id):
    """
    generate the prefix to a handler key
    """
    return "{0}{1}.{2}.".format(HANDLER_PREFIX, policy_type_id, policy_instance_id)


def _generate_handler_key(policy_type_id, policy_instance_id, handler_id):
    """
    generate a key for a policy handler
    """
    return "{0}{1}".format(_generate_handler_prefix(policy_type_id, policy_instance_id), handler_id)


def _get_statuses(policy_type_id, policy_instance_id):
    """
    shared helper to get statuses for an instance
    """
    instance_is_valid(policy_type_id, policy_instance_id)
    prefixes_for_handler = "{0}{1}.{2}.".format(HANDLER_PREFIX, policy_type_id, policy_instance_id)
    return list(SDL.find_and_get(prefixes_for_handler).values())


def _get_instance_list(policy_type_id):
    """
    shared helper to get instance list for a type
    """
    type_is_valid(policy_type_id)
    prefixes_for_type = "{0}{1}.".format(INSTANCE_PREFIX, policy_type_id)
    instancekeys = SDL.find_and_get(prefixes_for_type).keys()
    return [k.split(prefixes_for_type)[1] for k in instancekeys]


def _clear_handlers(policy_type_id, policy_instance_id):
    """
    delete all the handlers for a policy instance
    """
    all_handlers_pref = _generate_handler_prefix(policy_type_id, policy_instance_id)
    keys = SDL.find_and_get(all_handlers_pref)
    for k in keys:
        SDL.delete(k)


# Types


def get_type_list():
    """
    retrieve all type ids
    """
    typekeys = SDL.find_and_get(TYPE_PREFIX).keys()
    # policy types are ints but they get butchered to strings in the KV
    return [int(k.split(TYPE_PREFIX)[1]) for k in typekeys]


def type_is_valid(policy_type_id):
    """
    check that a type is valid
    """
    if SDL.get(_generate_type_key(policy_type_id)) is None:
        raise PolicyTypeNotFound()


def store_policy_type(policy_type_id, body):
    """
    store a policy type if it doesn't already exist
    """
    key = _generate_type_key(policy_type_id)
    if SDL.get(key) is not None:
        raise PolicyTypeAlreadyExists()
    SDL.set(key, body)


def delete_policy_type(policy_type_id):
    """
    delete a policy type; can only be done if there are no instances (business logic)
    """
    pil = get_instance_list(policy_type_id)
    if pil == []:  # empty, can delete
        SDL.delete(_generate_type_key(policy_type_id))
    else:
        raise CantDeleteNonEmptyType()


def get_policy_type(policy_type_id):
    """
    retrieve a type
    """
    type_is_valid(policy_type_id)
    return SDL.get(_generate_type_key(policy_type_id))


# Instances


def instance_is_valid(policy_type_id, policy_instance_id):
    """
    check that an instance is valid
    """
    type_is_valid(policy_type_id)
    if SDL.get(_generate_instance_key(policy_type_id, policy_instance_id)) is None:
        raise PolicyInstanceNotFound


def store_policy_instance(policy_type_id, policy_instance_id, instance):
    """
    Store a policy instance
    """
    type_is_valid(policy_type_id)
    key = _generate_instance_key(policy_type_id, policy_instance_id)
    if SDL.get(key) is not None:
        # Reset the statuses because this is a new policy instance, even if it was overwritten
        _clear_handlers(policy_type_id, policy_instance_id)  # delete all the handlers
    SDL.set(key, instance)


def get_policy_instance(policy_type_id, policy_instance_id):
    """
    Retrieve a policy instance
    """
    instance_is_valid(policy_type_id, policy_instance_id)
    return SDL.get(_generate_instance_key(policy_type_id, policy_instance_id))


def get_policy_instance_statuses(policy_type_id, policy_instance_id):
    """
    Retrieve the status vector for a policy instance
    """
    return _get_statuses(policy_type_id, policy_instance_id)


def get_instance_list(policy_type_id):
    """
    retrieve all instance ids for a type
    """
    return _get_instance_list(policy_type_id)


# Statuses


def set_status(policy_type_id, policy_instance_id, handler_id, status):
    """
    update the database status for a handler
    called from a1's rmr thread
    """
    type_is_valid(policy_type_id)
    instance_is_valid(policy_type_id, policy_instance_id)
    SDL.set(_generate_handler_key(policy_type_id, policy_instance_id, handler_id), status)


def clean_up_instance(policy_type_id, policy_instance_id):
    """
    see if we can delete an instance based on it's status
    """
    type_is_valid(policy_type_id)
    instance_is_valid(policy_type_id, policy_instance_id)

    """
    TODO: not being able to delete if the list is [] is prolematic.
    There are cases, such as a bad routing file, where this type will never be able to be deleted because it never went to any xapps
    However, A1 cannot distinguish between the case where [] was never going to work, and the case where it hasn't worked *yet*

    However, removing this constraint also leads to problems.
    Deleting the instance when the vector is empty, for example doing so “shortly after” the PUT, can lead to a worse race condition where the xapps get the policy after that, implement it, but because the DELETE triggered “too soon”, you can never get the status or do the delete on it again, so the xapps are all implementing the instance roguely.

    This requires some thought to address.
    For now we stick with the "less bad problem".
    """

    vector = _get_statuses(policy_type_id, policy_instance_id)
    if vector != []:
        all_deleted = True
        for i in vector:
            if i != "DELETED":
                all_deleted = False
                break  # have at least one not DELETED, do nothing

        # blow away from a1 db
        if all_deleted:
            _clear_handlers(policy_type_id, policy_instance_id)  # delete all the handlers
            SDL.delete(_generate_instance_key(policy_type_id, policy_instance_id))  # delete instance
            logger.debug("type %s instance %s deleted", policy_type_id, policy_instance_id)
