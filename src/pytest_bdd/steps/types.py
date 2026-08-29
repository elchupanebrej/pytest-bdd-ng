from __future__ import annotations

from collections.abc import Callable, Collection, Mapping
from inspect import getfile, getsourcelines
from typing import TYPE_CHECKING, TypeAlias, cast

from typing_extensions import Protocol

if TYPE_CHECKING:
    from types import FunctionType


class StepFunc(Protocol):
    __name__: str


StepDecorator: TypeAlias = Callable[[StepFunc], StepFunc]
ConverterT: TypeAlias = Callable[[object], object]
ParamsFixturesMapping: TypeAlias = bool | Collection[str] | Mapping[object, str | None]


def _resolve_callable_source_location(func: StepFunc) -> tuple[str, int]:
    typed_func = cast("FunctionType", func)
    try:
        source_line = getsourcelines(typed_func)[1]
    except (OSError, TypeError):
        source_line = getattr(getattr(func, "__code__", None), "co_firstlineno", 1) or 1
    return getfile(typed_func), int(source_line)


__all__ = [
    "ConverterT",
    "ParamsFixturesMapping",
    "StepDecorator",
    "StepFunc",
    "_resolve_callable_source_location",
]
