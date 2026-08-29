from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

from pytest_bdd.model.step import StepType
from pytest_bdd.steps.definition import Definition
from pytest_bdd.steps.manager import StepDefinitionManager

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping, Sequence

    from pytest_bdd.steps.types import ConverterT, ParamsFixturesMapping, StepDecorator, StepFunc


def not_implemented(step_func: StepFunc) -> StepFunc:
    cast("Any", step_func).__pytest_bdd_not_implemented__ = True
    for d in getattr(step_func, "__pytest_bdd_step_definitions__", ()):
        if isinstance(d, Definition):
            d.not_implemented = True
    return step_func


def tolerant(step_func: StepFunc) -> StepFunc:
    cast("Any", step_func).__pytest_bdd_tolerant__ = True
    for d in getattr(step_func, "__pytest_bdd_step_definitions__", ()):
        if isinstance(d, Definition):
            d.tolerant = True
    return step_func


def _step(
    step_type: str | StepType | None,
    parserlike: object,
    anonymous_group_names: Iterable[str] | None = None,
    converters: Mapping[str, ConverterT] | None = None,
    target_fixture: str | None = None,
    target_fixtures: Sequence[str] | None = None,
    params_fixtures_mapping: ParamsFixturesMapping = True,
    param_defaults: Mapping[str, object] | None = None,
    *,
    liberal: bool | None = None,
    stacklevel: int = 1,
) -> StepDecorator:
    return StepDefinitionManager.decorator_builder(
        step_type,
        parserlike,
        anonymous_group_names=anonymous_group_names,
        converters=converters,
        target_fixture=target_fixture,
        target_fixtures=target_fixtures,
        params_fixtures_mapping=params_fixtures_mapping,
        param_defaults=param_defaults,
        liberal=liberal,
        stacklevel=stacklevel + 1,
    )


def given(parserlike: object, *args: Any, **kwargs: Any) -> StepDecorator:
    return _step(StepType.context, parserlike, *args, **kwargs)


def when(parserlike: object, *args: Any, **kwargs: Any) -> StepDecorator:
    return _step(StepType.action, parserlike, *args, **kwargs)


def then(parserlike: object, *args: Any, **kwargs: Any) -> StepDecorator:
    return _step(StepType.outcome, parserlike, *args, **kwargs)


def step(parserlike: object, *args: Any, **kwargs: Any) -> StepDecorator:
    return _step(StepType.unknown, parserlike, *args, **kwargs)


__all__ = ["given", "not_implemented", "step", "then", "tolerant", "when"]
