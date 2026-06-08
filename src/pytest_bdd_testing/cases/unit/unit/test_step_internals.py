"""Direct unit tests for StepDefinitionManager internals.

These tests directly instantiate attrs classes and mock dependencies
to cover branches that are hard to reach via testdir integration tests.
"""

from __future__ import annotations

import pytest

from pytest_bdd.steps import StepDefinitionManager, _resolve_callable_source_location

pytestmark = [pytest.mark.unit]


def test_resolve_callable_source_location_normal_function():
    """Returns source file and line for a normal function."""

    def my_func():
        pass

    _source_file, source_line = _resolve_callable_source_location(my_func)
    assert isinstance(source_line, int)


def test_resolve_callable_source_location_function_without_code():
    """Handles function with no __code__ attribute gracefully."""

    # A built-in function may not have getsourcelines accessible
    # but we test the fallback path
    def call(_self):
        return None

    obj = type("Dummy", (), {"__call__": call})()
    _source_file, source_line = _resolve_callable_source_location(obj.__call__)
    assert isinstance(source_line, int)
    assert source_line >= 1


def _make_definition_fixtures_mapped(
    *,
    params_fixtures_mapping=True,
    anonymous_group_names=None,
    converters=None,
    target_fixtures=None,
):
    """Helper to create a Definition with specific params_fixtures_mapping."""
    from pytest_bdd.parsers import string as string_parser

    mock_parser = string_parser("test step")
    return StepDefinitionManager.Definition(
        func=lambda: None,
        type_="given",
        parser=mock_parser,
        anonymous_group_names=anonymous_group_names,
        converters=converters or {},
        params_fixtures_mapping=params_fixtures_mapping,
        param_defaults={},
        target_fixtures=target_fixtures or [],
        liberal=None,
    )


def test_mapping_with_string_keys():
    """Mapping with string keys maps param names to fixture names."""
    definition = _make_definition_fixtures_mapped(
        params_fixtures_mapping={"item": "my_fixture"},
        anonymous_group_names=["item"],
    )
    result = definition.fixtures_mapped_from_step_definition
    assert "my_fixture" in result


def test_mapping_with_non_string_keys():
    """Mapping with non-string keys are filtered out from converted_params."""
    definition = _make_definition_fixtures_mapped(
        params_fixtures_mapping={1: "my_fixture"},
        anonymous_group_names=[1],
    )
    result = definition.fixtures_mapped_from_step_definition
    assert "my_fixture" in result


def test_collection_params_fixtures_mapping():
    """Collection params_fixtures_mapping adds fixture names."""
    definition = _make_definition_fixtures_mapped(
        params_fixtures_mapping=["fixture_a", "fixture_b"],
    )
    result = definition.fixtures_mapped_from_step_definition
    assert "fixture_a" in result
    assert "fixture_b" in result


def test_true_params_fixtures_mapping():
    """True params_fixtures_mapping includes bypassed params."""
    definition = _make_definition_fixtures_mapped(
        params_fixtures_mapping=True,
        anonymous_group_names=["item"],
    )
    result = definition.fixtures_mapped_from_step_definition
    assert "item" in result


def test_false_params_fixtures_mapping():
    """False params_fixtures_mapping returns only target fixtures."""
    definition = _make_definition_fixtures_mapped(
        params_fixtures_mapping=False,
        anonymous_group_names=["item"],
        target_fixtures=["explicit_fixture"],
    )
    result = definition.fixtures_mapped_from_step_definition
    assert "explicit_fixture" in result
    assert "item" not in result


def test_empty_params_fixtures_mapping():
    """Empty collection params_fixtures_mapping."""
    definition = _make_definition_fixtures_mapped(
        params_fixtures_mapping=[],
    )
    result = definition.fixtures_mapped_from_step_definition
    assert result == set()


def _make_definition_as_message(parser=None, func=None):
    """Helper to create a Definition for message testing."""
    from pytest_bdd.parsers import string as string_parser

    mock_parser = parser or string_parser("test step")
    mock_func = func or (lambda: None)
    return StepDefinitionManager.Definition(
        func=mock_func,
        type_="given",
        parser=mock_parser,
        anonymous_group_names=None,
        converters={},
        params_fixtures_mapping=True,
        param_defaults={},
        target_fixtures=[],
        liberal=None,
    )


def test_as_message_creates_step_definition():
    """as_message returns a StepDefinition message."""
    from cucumber_messages import StepDefinition

    from pytest_bdd.util.other import IdGenerator

    definition = _make_definition_as_message()
    mock_stash = {"_pytest_bdd_id_generator": IdGenerator()}
    from unittest.mock import MagicMock

    mock_config = MagicMock()
    mock_config.stash = mock_stash

    result = definition.as_message(mock_config)
    assert isinstance(result, StepDefinition)
    # id is a string (UUID-based), verify it's non-empty
    assert result.id


def test_as_message_caches_by_id_generator():
    """as_message caches results per IdGenerator instance."""
    from pytest_bdd.util.other import IdGenerator

    definition = _make_definition_as_message()
    mock_stash = {"_pytest_bdd_id_generator": IdGenerator()}
    from unittest.mock import MagicMock

    mock_config = MagicMock()
    mock_config.stash = mock_stash

    msg1 = definition.as_message(mock_config)
    msg2 = definition.as_message(mock_config)
    assert msg1 is msg2


def _make_definition_get_parameters(
    *,
    params_fixtures_mapping=True,
    converters=None,
    param_defaults=None,
    anonymous_group_names=None,
):
    from pytest_bdd.parsers import string as string_parser

    mock_parser = string_parser("test step")
    return StepDefinitionManager.Definition(
        func=lambda: None,
        type_="given",
        parser=mock_parser,
        anonymous_group_names=anonymous_group_names,
        converters=converters or {},
        params_fixtures_mapping=params_fixtures_mapping,
        param_defaults=param_defaults or {},
        target_fixtures=[],
        liberal=None,
    )


def test_get_parameters_with_defaults():
    """get_parameters merges param_defaults."""
    from unittest.mock import MagicMock

    definition = _make_definition_get_parameters(
        param_defaults={"default_key": "default_value"},
    )
    mock_step = MagicMock()
    mock_step.text = "test step"
    mock_request = MagicMock()

    result = definition.get_parameters(mock_request, mock_step)
    assert result["default_key"] == "default_value"


def test_get_parameters_with_converters():
    """get_parameters applies converters to parsed arguments."""
    from unittest.mock import MagicMock

    from pytest_bdd.parsers import re as re_parser

    parser = re_parser(r"I have (\d+) Euro")
    definition = StepDefinitionManager.Definition(
        func=lambda: None,
        type_="given",
        parser=parser,
        anonymous_group_names=["euro"],
        converters={"euro": int},
        params_fixtures_mapping=True,
        param_defaults={},
        target_fixtures=[],
        liberal=None,
    )
    mock_step = MagicMock()
    mock_step.text = "I have 5 Euro"
    mock_request = MagicMock()

    result = definition.get_parameters(mock_request, mock_step)
    assert result["euro"] == 5
    assert isinstance(result["euro"], int)


def test_get_parameters_uses_identity_converter_by_default():
    """get_parameters leaves parsed values unchanged without converter."""
    from unittest.mock import MagicMock

    from pytest_bdd.parsers import re as re_parser

    parser = re_parser(r"I have (?P<thing>.+)")
    definition = StepDefinitionManager.Definition(
        func=lambda: None,
        type_="given",
        parser=parser,
        anonymous_group_names=None,
        converters={},
        params_fixtures_mapping=True,
        param_defaults={},
        target_fixtures=[],
        liberal=None,
    )
    mock_step = MagicMock()
    mock_step.text = "I have café"

    result = definition.get_parameters(MagicMock(), mock_step)

    assert result == {"thing": "café"}


def test_inject_registry_fixture_and_register_steps():
    """Registry.inject_registry_fixture_and_register_steps registers fixtures."""
    from unittest.mock import MagicMock

    from pytest_bdd.steps import StepDefinitionManager

    class MockNamespace:
        pass

    # Create mock step container with __pytest_bdd_step_definitions__
    mock_step = MagicMock()
    mock_def = MagicMock()
    mock_def.fixtures_mapped_from_step_definition = set()
    mock_step.__pytest_bdd_step_definitions__ = {mock_def}

    namespace = MockNamespace()
    namespace.__dict__["some_step"] = mock_step

    StepDefinitionManager.Registry.inject_registry_fixture(namespace)

    assert hasattr(namespace, "__pytest_bdd_step_registry__")
    assert hasattr(namespace, "step_registry")


def test_registry_iteration():
    """Registry.__iter__ iterates over registered definitions."""
    from unittest.mock import MagicMock

    from pytest_bdd.steps import StepDefinitionManager

    registry = StepDefinitionManager.Registry()
    mock_def = MagicMock()
    registry.registry.add(mock_def)

    definitions = list(registry)
    assert mock_def in definitions
