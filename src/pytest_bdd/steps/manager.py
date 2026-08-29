from __future__ import annotations

from typing import TYPE_CHECKING, cast
from uuid import uuid4
from warnings import warn

import pytest
from ordered_set import OrderedSet

from pytest_bdd.parsers.base import StepParser
from pytest_bdd.steps.definition import Definition
from pytest_bdd.steps.matcher import Matcher
from pytest_bdd.steps.registry import Registry, StepProtocol, StepRegistryProtocol
from pytest_bdd.utils import convert_str_to_python_name, get_caller_module_locals, setdefaultattr
from pytest_bdd.warning_types import PytestBDDStepDefinitionWarning

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping, Sequence

    from pytest_bdd.model.step import StepType
    from pytest_bdd.steps.types import ConverterT, ParamsFixturesMapping, StepDecorator, StepFunc


def _none_fixture(fixture_name: str) -> object:
    @pytest.fixture(name=fixture_name)
    def _fixture() -> None:
        return None

    return _fixture


class StepDefinitionManager:
    Registry = Registry
    Matcher = Matcher
    Definition = Definition
    StepProtocol = StepProtocol
    NamespaceStepRegistryProtocol = StepRegistryProtocol

    @staticmethod
    def decorator_builder(
        step_type: str | StepType | None,
        step_parserlike: object,
        anonymous_group_names: Iterable[str] | None = None,
        converters: Mapping[str, ConverterT] | None = None,
        target_fixture: str | None = None,
        target_fixtures: Sequence[str] | None = None,
        params_fixtures_mapping: ParamsFixturesMapping = True,
        param_defaults: Mapping[str, object] | None = None,
        *,
        liberal: bool | None = None,
        stacklevel: int = 2,
    ) -> StepDecorator:
        if target_fixture is not None and target_fixtures is not None:
            warn(
                PytestBDDStepDefinitionWarning(
                    f"Both target_fixture={target_fixture} and target_fixtures={target_fixtures} are specified. "
                    f"All of them will be injected."
                ),
                stacklevel=stacklevel,
            )
        resolved_target_fixtures = OrderedSet(
            [*([target_fixture] if target_fixture is not None else []), *(target_fixtures or [])]
        )

        def decorator(step_func: StepFunc) -> StepFunc:
            step_parser = StepParser.build(step_parserlike)
            step_definition = Definition(
                func=step_func,
                type_=step_type,
                parser=step_parser,
                anonymous_group_names=anonymous_group_names,
                converters=converters or {},
                params_fixtures_mapping=params_fixtures_mapping,
                param_defaults=param_defaults or {},
                target_fixtures=list(resolved_target_fixtures),
                liberal=liberal,
            )
            step_definitions = cast(
                "set[Definition]", setdefaultattr(step_func, "__pytest_bdd_step_definitions__", value_factory=set)
            )
            step_definitions.add(step_definition)
            caller_locals = get_caller_module_locals(stacklevel=stacklevel)
            caller_locals[convert_str_to_python_name(f"step_{step_type or ''}_{step_parserlike}_{uuid4()}")] = step_func
            for fn in step_definition.fixtures_mapped_from_step_definition:
                if not fn.startswith("pytest_"):
                    caller_locals.setdefault(fn, _none_fixture(fn))
            return step_func

        return decorator
