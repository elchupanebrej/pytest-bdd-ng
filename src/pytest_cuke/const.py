from __future__ import annotations

import re
from enum import Enum

TAG_PREFIX = "@"

PYTHON_REPLACE_REGEX = re.compile(r"\W")
ALPHA_REGEX = re.compile(r"^\d+_*")


class PytestConfigParam(str, Enum):
    CONTINUE_ON_COLLECTION_ERRORS = "continue_on_collection_errors"


class Steps:
    class Ini(str, Enum):
        LIBERAL_OPTION = "cuke_liberal_steps"

    class Cli(str, Enum):
        LIBERAL_OPTION = "cuke_liberal_steps"


IDE_DIAGNOSTIC_MEDIA_TYPE = "application/vnd.pytest-bdd.diagnostic+json"
IDE_LAUNCH_MEDIA_TYPE = "application/vnd.pytest-bdd.launch+json"
IDE_STEP_BINDING_MEDIA_TYPE = "application/vnd.pytest-bdd.step-binding+json"

PYTEST_OUTCOME_MEDIA_TYPE = "application/vnd.pytest-cuke.pytest-outcome+json"
PYTEST_STEP_OUTCOME_MEDIA_TYPE = "application/vnd.pytest-cuke.step-outcome+json"
PYTEST_SOURCE_MEDIA_TYPE = "application/vnd.pytest-cuke.source+json"
