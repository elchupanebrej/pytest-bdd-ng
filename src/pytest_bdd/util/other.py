import re
from typing import Any, ClassVar, Protocol, runtime_checkable

from gherkin.stream.id_generator import IdGenerator as BaseIdGenerator

from pytest_bdd.const import ALPHA_REGEX, PYTHON_REPLACE_REGEX
from pytest_bdd.model.stash_access import StashBound


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


def normalize_to_string(value: StringRepresentable | str | bytes) -> str:
    return str(value, **({"encoding": "utf-8"} if isinstance(value, bytes) else {}))


class IdGenerator(BaseIdGenerator, StashBound):
    STASH_KEY: ClassVar[str] = "_pytest_bdd_id_generator"

    def __init__(self):
        self._id_counter = 0

    def __next__(self):
        try:
            return str(self._id_counter)
        finally:
            self._id_counter += 1

    get_next_id = __next__

    @classmethod
    def stash_missing_message(cls) -> str:
        return (
            "`pytest_bdd_id_generator` is unavailable in config.stash. "
            "Execution and collection plugins must initialize stash-backed runtime services before use."
        )

    @classmethod
    def stash_duplicate_message(cls) -> str:
        return (
            "`pytest_bdd_id_generator` is already initialized in config.stash. "
            "Framework bootstrap must initialize it exactly once."
        )
