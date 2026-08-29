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
        LIBERAL_OPTION = "liberal_steps"

    class Cli(str, Enum):
        LIBERAL_OPTION = "liberal_steps"
