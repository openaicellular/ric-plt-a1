import pytest


@pytest.fixture
def adm_type_good():
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
    return {"enforce": True, "window_length": 10, "blocking_rate": 20, "trigger_threshold": 10}
