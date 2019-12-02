"""
Represents A1s database and database access functions.
In the future, this may change to use a different backend, possibly dramatically.
Hopefully, the access functions are a good api so nothing else has to change when this happens

For now, the database is in memory.
We use dict data structures (KV) with the expectation of having to move this into Redis
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
import os
import time
from threading import Thread
import msgpack
from mdclogpy import Logger
from a1.exceptions import PolicyTypeNotFound, PolicyInstanceNotFound, PolicyTypeAlreadyExists, CantDeleteNonEmptyType

mdc_logger = Logger(name=__name__)


INSTANCE_DELETE_NO_RESP_TTL = int(os.environ.get("INSTANCE_DELETE_NO_RESP_TTL", 5))
INSTANCE_DELETE_RESP_TTL = int(os.environ.get("INSTANCE_DELETE_RESP_TTL", 5))


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
METADATA_PREFIX = "a1.policy_inst_metadata."
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


def _generate_instance_metadata_key(policy_type_id, policy_instance_id):
    """
    generate a key for a policy instance metadata
    """
    return "{0}{1}.{2}".format(METADATA_PREFIX, policy_type_id, policy_instance_id)


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


def _type_is_valid(policy_type_id):
    """
    check that a type is valid
    """
    if SDL.get(_generate_type_key(policy_type_id)) is None:
        raise PolicyTypeNotFound()


def _instance_is_valid(policy_type_id, policy_instance_id):
    """
    check that an instance is valid
    """
    _type_is_valid(policy_type_id)
    if SDL.get(_generate_instance_key(policy_type_id, policy_instance_id)) is None:
        raise PolicyInstanceNotFound


def _get_statuses(policy_type_id, policy_instance_id):
    """
    shared helper to get statuses for an instance
    """
    _instance_is_valid(policy_type_id, policy_instance_id)
    prefixes_for_handler = "{0}{1}.{2}.".format(HANDLER_PREFIX, policy_type_id, policy_instance_id)
    return list(SDL.find_and_get(prefixes_for_handler).values())


def _get_instance_list(policy_type_id):
    """
    shared helper to get instance list for a type
    """
    _type_is_valid(policy_type_id)
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


def _get_metadata(policy_type_id, policy_instance_id):
    """
    get instance metadata
    """
    _instance_is_valid(policy_type_id, policy_instance_id)
    metadata_key = _generate_instance_metadata_key(policy_type_id, policy_instance_id)
    return SDL.get(metadata_key)


def _delete_after(policy_type_id, policy_instance_id, ttl):
    """
    this is a blocking function, must call this in a thread to not block!
    waits ttl seconds, then deletes the instance
    """
    _instance_is_valid(policy_type_id, policy_instance_id)

    time.sleep(ttl)

    # ready to delete
    _clear_handlers(policy_type_id, policy_instance_id)  # delete all the handlers
    SDL.delete(_generate_instance_key(policy_type_id, policy_instance_id))  # delete instance
    SDL.delete(_generate_instance_metadata_key(policy_type_id, policy_instance_id))  # delete instance metadata
    mdc_logger.debug("type {0} instance {1} deleted".format(policy_type_id, policy_instance_id))


# Types


def get_type_list():
    """
    retrieve all type ids
    """
    typekeys = SDL.find_and_get(TYPE_PREFIX).keys()
    # policy types are ints but they get butchered to strings in the KV
    return [int(k.split(TYPE_PREFIX)[1]) for k in typekeys]


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
    _type_is_valid(policy_type_id)
    return SDL.get(_generate_type_key(policy_type_id))


# Instances


def store_policy_instance(policy_type_id, policy_instance_id, instance):
    """
    Store a policy instance
    """
    _type_is_valid(policy_type_id)
    creation_timestamp = time.time()

    # store the instance
    key = _generate_instance_key(policy_type_id, policy_instance_id)
    if SDL.get(key) is not None:
        # Reset the statuses because this is a new policy instance, even if it was overwritten
        _clear_handlers(policy_type_id, policy_instance_id)  # delete all the handlers
    SDL.set(key, instance)

    metadata_key = _generate_instance_metadata_key(policy_type_id, policy_instance_id)
    SDL.set(metadata_key, {"created_at": creation_timestamp, "has_been_deleted": False})


def get_policy_instance(policy_type_id, policy_instance_id):
    """
    Retrieve a policy instance
    """
    _instance_is_valid(policy_type_id, policy_instance_id)
    return SDL.get(_generate_instance_key(policy_type_id, policy_instance_id))


def get_instance_list(policy_type_id):
    """
    retrieve all instance ids for a type
    """
    return _get_instance_list(policy_type_id)


def delete_policy_instance(policy_type_id, policy_instance_id):
    """
    initially sets has_been_deleted
    then launches a thread that waits until the relevent timer expires, and finally deletes the instance
    """
    _instance_is_valid(policy_type_id, policy_instance_id)

    # set the metadata first
    deleted_timestamp = time.time()
    metadata_key = _generate_instance_metadata_key(policy_type_id, policy_instance_id)
    existing_metadata = _get_metadata(policy_type_id, policy_instance_id)
    SDL.set(
        metadata_key,
        {"created_at": existing_metadata["created_at"], "has_been_deleted": True, "deleted_at": deleted_timestamp},
    )

    # wait, then delete
    vector = _get_statuses(policy_type_id, policy_instance_id)
    if vector == []:
        # handler is empty; we wait for t1 to expire then goodnight
        clos = lambda: _delete_after(policy_type_id, policy_instance_id, INSTANCE_DELETE_NO_RESP_TTL)
    else:
        # handler is not empty, we wait max t1,t2 to expire then goodnight
        clos = lambda: _delete_after(
            policy_type_id, policy_instance_id, max(INSTANCE_DELETE_RESP_TTL, INSTANCE_DELETE_NO_RESP_TTL)
        )
    Thread(target=clos).start()


# Statuses


def set_policy_instance_status(policy_type_id, policy_instance_id, handler_id, status):
    """
    update the database status for a handler
    called from a1's rmr thread
    """
    _type_is_valid(policy_type_id)
    _instance_is_valid(policy_type_id, policy_instance_id)
    SDL.set(_generate_handler_key(policy_type_id, policy_instance_id, handler_id), status)


def get_policy_instance_status(policy_type_id, policy_instance_id):
    """
    Gets the status of an instance
    """
    _instance_is_valid(policy_type_id, policy_instance_id)
    metadata = _get_metadata(policy_type_id, policy_instance_id)
    metadata["instance_status"] = "NOT IN EFFECT"
    for i in _get_statuses(policy_type_id, policy_instance_id):
        if i == "OK":
            metadata["instance_status"] = "IN EFFECT"
            break
    return metadata
