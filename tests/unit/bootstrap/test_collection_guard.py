from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import pytest
from ordered_set import OrderedSet

from pytest_cuke.model import Feature, Scenario, Step, StepType
from pytest_cuke.model.message_extension import StepDefinitionPatternType
from pytest_cuke.plugin import _allow_empty_scenarios_enabled, _collection_step_registry, _scenario_has_matching_step
from pytest_cuke.steps.definition import Definition
from pytest_cuke.steps.registry import Registry

pytestmark = pytest.mark.unit


class _StringParser:
    type = StepDefinitionPatternType.pytest_cuke_string_expression
    arguments: tuple[str, ...] = ()
    parser_by_priorities: tuple[Any, ...] = ()
    last_undefined_parameter_types: tuple[()] = ()
    last_undefined_parameter_type_error: None = None

    def __init__(self, matching_text: str) -> None:
        self.matching_text = matching_text

    def is_matching(self, request: Any, name: str) -> bool:
        return name == self.matching_text

    def parse_arguments(self, request: Any, name: str, anonymous_group_names: Any = None) -> dict[str, Any]:
        return {}

    def __str__(self) -> str:
        return self.matching_text


def _definition(matching_text: str) -> Definition:
    return Definition(
        func=lambda: None,
        type_=StepType.context,
        parser=_StringParser(matching_text),  # type: ignore[arg-type]  # This parser implements the matcher protocol used by the unit.
        anonymous_group_names=None,
        converters={},
        params_fixtures_mapping={},
        param_defaults={},
        target_fixtures=(),
        liberal=False,
    )


def _config() -> Any:
    return SimpleNamespace(
        option=SimpleNamespace(cuke_liberal_steps=False),
        getini=lambda name: False,
    )


def test_allow_empty_scenarios_cli_value_overrides_ini() -> None:
    config = SimpleNamespace(
        option=SimpleNamespace(cuke_allow_empty_scenarios=False),
        getini=lambda name: True,
    )

    assert _allow_empty_scenarios_enabled(config) is False


def test_collection_registry_uses_applicable_registries_without_running_fixtures() -> None:
    invoked: list[str] = []
    child_definition = _definition("child")
    parent_definition = _definition("parent")
    root_definition = _definition("root")
    child_registry = Registry(definitions=OrderedSet((child_definition,)))
    parent_registry = Registry(definitions=OrderedSet((parent_definition,)))
    root_registry = Registry(definitions=OrderedSet((root_definition,)))

    def fixture_for(registry: Registry, name: str) -> Any:
        def step_registry() -> Registry:
            invoked.append(name)
            return registry

        step_registry.__pytest_cuke_step_registry__ = registry  # type: ignore[attr-defined]  # Mirrors the marker attached by Registry.fixture.
        return SimpleNamespace(func=step_registry)

    fixture_manager = SimpleNamespace(
        getfixturedefs=lambda name, item: (
            fixture_for(root_registry, "root"),
            fixture_for(parent_registry, "parent"),
            fixture_for(child_registry, "child"),
        )
    )
    item = SimpleNamespace(
        module=SimpleNamespace(__pytest_cuke_step_registry__=child_registry),
        session=SimpleNamespace(_fixturemanager=fixture_manager),
    )

    registry = _collection_step_registry(item)

    assert tuple(registry) == (child_definition, parent_definition, root_definition)
    assert invoked == []


def test_collection_matcher_treats_any_matching_step_as_partial_match() -> None:
    known_definition = _definition("known step")
    registry = Registry(definitions=OrderedSet((known_definition,)))
    item = SimpleNamespace(
        module=SimpleNamespace(__pytest_cuke_step_registry__=registry),
        session=SimpleNamespace(_fixturemanager=SimpleNamespace(getfixturedefs=lambda name, item: ())),
    )
    feature = Feature(name="Example", filename="features/example.feature")
    scenario = Scenario(
        name="partially matched",
        steps=(
            Step(name="known step", keyword="Given ", line=2, type=StepType.context),
            Step(name="missing step", keyword="When ", line=3, type=StepType.action),
        ),
    )

    assert _scenario_has_matching_step(_config(), item, feature, scenario) is True
