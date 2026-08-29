from __future__ import annotations

from unittest.mock import MagicMock

from pytest_bdd.model.step import Step, StepType
from pytest_bdd.parsers.string_parser import string
from pytest_bdd.steps.definition import Definition, _resolve_callable_source_location
from pytest_bdd.utils import IdGenerator


def dummy_step() -> None:
    pass


def test_resolve_callable_source_location() -> None:
    file_path, line = _resolve_callable_source_location(dummy_step)
    assert file_path.endswith("test_definition.py")
    assert line > 0


def test_definition_get_parameters_and_fixtures_mapped() -> None:
    parser = string("I have apples")
    defn = Definition(
        func=dummy_step,
        type_=StepType.context,
        parser=parser,
        anonymous_group_names=None,
        converters={"count": int},
        params_fixtures_mapping=True,
        param_defaults={"default_val": "123"},
        target_fixtures=["apple_fixture"],
        liberal=False,
    )
    assert "apple_fixture" in defn.fixtures_mapped_from_step_definition

    step = Step(name="I have apples", keyword="Given", type=StepType.context)
    params = defn.get_parameters(None, step)
    assert params == {"default_val": "123"}


def test_definition_as_message() -> None:
    parser = string("I have apples")
    defn = Definition(
        func=dummy_step,
        type_=StepType.context,
        parser=parser,
        anonymous_group_names=None,
        converters={},
        params_fixtures_mapping=False,
        param_defaults={},
        target_fixtures=[],
        liberal=False,
    )
    config = MagicMock()
    config.stash = {IdGenerator.pytest_bdd_id_generator: IdGenerator()}
    msg = defn.as_message(config)
    assert msg.id == "0"
    assert msg.pattern.source == "I have apples"
