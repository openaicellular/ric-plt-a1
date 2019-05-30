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
from jsonschema import validate
from a1 import get_module_logger
from a1 import exceptions


logger = get_module_logger(__name__)


def _get_rmr_mapping_table(cache={}):
    """
    Get the rmr mapping file
    Broken out for ease of unit testing
    """
    try:
        return open("/opt/rmr_string_int_mapping.txt", "r").readlines()
    except FileNotFoundError:
        logger.error("Missing RMR Mapping!")
        raise exceptions.MissingRmrMapping


# Public


def validate_json(instance, schema):
    """
    validate incoming policy payloads
    """
    validate(instance=instance, schema=schema)


def get_ric_manifest():
    """
    Get the ric level manifest
    """
    try:
        with open("/opt/ricmanifest.json", "r") as f:
            content = f.read()
            manifest = json.loads(content)
            return manifest
    except FileNotFoundError:
        logger.error("Missing A1 Manifest!")
        raise exceptions.MissingManifest


def rmr_string_to_int(rmrs, cache={}):
    """
    map an rmr string to an int.
    TODO: should we allow for dynamic updates to this file? If so, we shouldn't cache
    """
    if cache == {}:  # fill the cache if not populated
        lines = _get_rmr_mapping_table()
        for l in lines:
            items = l.split(":")
            cache[items[0]] = int(items[1])

    if rmrs in cache:
        return cache[rmrs]
    raise exceptions.MissingRmrString(rmrs)
