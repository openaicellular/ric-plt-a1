"""
pytest conftest
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
import tempfile
import os
import pytest
from a1 import app


@pytest.fixture
def client():
    """
    http://flask.pocoo.org/docs/1.0/testing/
    """

    db_fd, app.app.config["DATABASE"] = tempfile.mkstemp()
    app.app.config["TESTING"] = True
    cl = app.app.test_client()

    yield cl

    os.close(db_fd)
    os.unlink(app.app.config["DATABASE"])


@pytest.fixture
def adm_type_good():
    """
    represents a good put for adm control type
    """
    return {
        "name": "Admission Control",
        "description": "various parameters to control admission of dual connection",
        "policy_type_id": 20000,
        "create_schema": {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "type": "object",
            "properties": {
                "enforce": {"type": "boolean", "default": True},
                "window_length": {
                    "type": "integer",
                    "default": 1,
                    "minimum": 1,
                    "maximum": 60,
                    "description": "Sliding window length (in minutes)",
                },
                "blocking_rate": {
                    "type": "number",
                    "default": 10,
                    "minimum": 1,
                    "maximum": 100,
                    "description": "% Connections to block",
                },
                "trigger_threshold": {
                    "type": "integer",
                    "default": 10,
                    "minimum": 1,
                    "description": "Minimum number of events in window to trigger blocking",
                },
            },
            "required": ["enforce", "blocking_rate", "trigger_threshold", "window_length"],
            "additionalProperties": False,
        },
    }


@pytest.fixture
def adm_instance_good():
    """
    represents a good put for adm control instance
    """
    return {"enforce": True, "window_length": 10, "blocking_rate": 20, "trigger_threshold": 10}
