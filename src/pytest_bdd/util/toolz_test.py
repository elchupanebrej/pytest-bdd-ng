"""Provide toolz test helpers."""

from __future__ import annotations

import base64
import pickle  # noqa:S403
import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover
    from pytest_bdd.compatibility.pytest import RunResult

_DUMP_START = "_pytest_bdd_>>>"
_DUMP_END = "<<<_pytest_bdd_"


def dump_obj(*objects: object) -> None:
    """Dump objects to stdout so that they can be inspected by the test suite."""
    for obj in objects:
        dump = pickle.dumps(obj, protocol=pickle.HIGHEST_PROTOCOL)
        encoded = base64.b64encode(dump).decode("ascii")
        print(f"{_DUMP_START}{encoded}{_DUMP_END}")  # noqa: T201 intentional non-debug output


def collect_dumped_objects(result: RunResult) -> list[object]:
    """
    Parse all the objects dumped with `dump_object` from the result.

    Note: You must run the result with output to stdout enabled.
    For example, using ``testdir.runpytest("-s")``.

    Args:
        result: Pytest run result.

    Returns:
        List of unpickled objects.

    """
    stdout = result.stdout.str()  # pytest < 6.2, otherwise we could just do str(result.stdout)
    payloads = re.findall(rf"{_DUMP_START}(.*?){_DUMP_END}", stdout)
    return [pickle.loads(base64.b64decode(payload)) for payload in payloads]  # noqa: S301


class InstanceOfType:
    """
    Helper for equality checks: returns True if.

    the other object is an instance of the given type
    (or always True if no type is specified).
    """

    def __init__(self, type_: type | None = None) -> None:
        """Initialize the instance of type."""
        self.type = type_

    def __eq__(self, other: object) -> bool:
        """
        Return whether the other object matches the expected type.

        Args:
            other: Object to compare.

        Returns:
            True if matches expected type.

        """
        return isinstance(other, self.type) if self.type else True

    __hash__ = None  # type: ignore[assignment]
