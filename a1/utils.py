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
