from __future__ import annotations

from collections.abc import Callable, Collection, Mapping
from inspect import getfile, getsourcelines
from typing import TYPE_CHECKING, TypeAlias, cast

from typing_extensions import Protocol

from pytest_bdd.model.message_extension import StepDefinitionPatternType

if TYPE_CHECKING:
    from types import FunctionType

    from pytest_bdd.model.step import Step
    from pytest_bdd.steps.definition import Definition


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


def _parser_specificity(step_definition: Definition) -> int:
    pt = step_definition.parser.type
    high = {
        StepDefinitionPatternType.pytest_bdd_string_expression,
        StepDefinitionPatternType.pytest_bdd_parse_expression,
        StepDefinitionPatternType.pytest_bdd_cfparse_expression,
        StepDefinitionPatternType.cucumber_expression,
    }
    if pt in high:
        return 2
    regexes = {StepDefinitionPatternType.regular_expression, StepDefinitionPatternType.pytest_bdd_regular_expression}
    return 1 if pt in regexes else 0


def _step_text(step: Step) -> str:
    return getattr(step, "name", getattr(step, "text", str(step)))


__all__ = [
    "ConverterT",
    "ParamsFixturesMapping",
    "StepDecorator",
    "StepFunc",
    "_parser_specificity",
    "_resolve_callable_source_location",
    "_step_text",
]
