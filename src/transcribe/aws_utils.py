import os


def get_execution_environment_metadata() -> dict:
    EXPECTED_AWS_KEYS = {
        "AWS_REGION",
        "AWS_EXECUTION_ENV",
        "PYTHON_VERSION",
        "PYTHON_PIP_VERSION",
    }
    execution_environment_metadata = {}
    for key, value in os.environ.items():
        if key in EXPECTED_AWS_KEYS or key.startswith("COPILOT_"):
            execution_environment_metadata[key] = value
    return execution_environment_metadata
