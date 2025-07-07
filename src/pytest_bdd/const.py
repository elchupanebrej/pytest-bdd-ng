import re

from pytest_bdd.compatibility.enum import StrEnum

TAG_PREFIX = "@"

PYTHON_REPLACE_REGEX = re.compile(r"\W")
ALPHA_REGEX = re.compile(r"^\d+_*")


class PytestConfigParam(StrEnum):
    CONTINUE_ON_COLLECTION_ERRORS = "continue_on_collection_errors"
