import re
from typing import Any, Protocol, Union, runtime_checkable

from pytest_bdd.const import ALPHA_REGEX, PYTHON_REPLACE_REGEX


def format_as_python_identifier(s: Any) -> str:
    s1: str = str(s)
    s2 = re.sub(r"[^.a-zA-Z0-9]", "_", s1)
    s3 = re.sub(r"_+", "_", s2)
    s4 = s3.strip("_")
    return f"_{s4}" if re.match(r"\d.*", s4) else s4


def format_as_simplified_python_identifier(string: str) -> str:
    string = re.sub(PYTHON_REPLACE_REGEX, "", string.replace(" ", "_"))
    return re.sub(ALPHA_REGEX, "", string).lower()


@runtime_checkable
class StringRepresentable(Protocol):
    def __str__(self) -> str: ...  # pragma: no cover


def normalize_to_string(value: Union[StringRepresentable, str, bytes]) -> str:
    return str(value, **({"encoding": "utf-8"} if isinstance(value, bytes) else {}))


class IdGenerator:
    def __init__(self):
        self._id_counter = 0

    def __next__(self):
        try:
            return str(self._id_counter)
        finally:
            self._id_counter += 1

    get_next_id = __next__
