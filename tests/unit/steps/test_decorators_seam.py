from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import MagicMock

from ordered_set import OrderedSet

from pytest_cuke.model.step import Step, StepType
from pytest_cuke.parsers.string_parser import string
from pytest_cuke.steps.decorators import given, not_implemented, then, tolerant, when
from pytest_cuke.steps.matcher import Matcher
from pytest_cuke.steps.registry import Registry

if TYPE_CHECKING:
    from pytest_cuke.steps.definition import Definition


def test_decorators_and_manager_registration() -> None:
    @given(string("I have a book"), target_fixture="book")
    def given_book() -> str:
        return "The Hobbit"

    assert hasattr(given_book, "__pytest_cuke_step_definitions__")
    definitions = given_book.__pytest_cuke_step_definitions__
    assert len(definitions) == 1
    defn: Definition = next(iter(definitions))
    assert defn.type_ == StepType.context
    assert defn.target_fixtures == ["book"]
    assert "book" in defn.fixtures_mapped_from_step_definition


def test_decorators_not_implemented_and_tolerant() -> None:
    @not_implemented
    @tolerant
    @when(string("I read the book"))
    def when_read() -> None:
        pass

    assert when_read.__pytest_cuke_not_implemented__ is True
    assert when_read.__pytest_cuke_tolerant__ is True
    defn = next(iter(when_read.__pytest_cuke_step_definitions__))
    assert defn.not_implemented is True
    assert defn.tolerant is True


def test_tolerant_can_be_inner_or_outer_to_step_decorator() -> None:
    @tolerant
    @when(string("I tolerate the inner order"))
    def inner_tolerant() -> None:
        pass

    @when(string("I tolerate the outer order"))
    @tolerant
    def outer_tolerant() -> None:
        pass

    assert next(iter(inner_tolerant.__pytest_cuke_step_definitions__)).tolerant is True
    assert next(iter(outer_tolerant.__pytest_cuke_step_definitions__)).tolerant is True


def test_not_implemented_can_be_inner_or_outer_to_step_decorator() -> None:
    @not_implemented
    @when(string("The inner WIP decorator order"))
    def inner_wip() -> None:
        pass

    @when(string("The outer WIP decorator order"))
    @not_implemented
    def outer_wip() -> None:
        pass

    assert next(iter(inner_wip.__pytest_cuke_step_definitions__)).not_implemented is True
    assert next(iter(outer_wip.__pytest_cuke_step_definitions__)).not_implemented is True


def test_matcher_liberal_mode() -> None:
    @then(string("I check state"))
    def then_check() -> None:
        pass

    reg = Registry(definitions=OrderedSet([next(iter(then_check.__pytest_cuke_step_definitions__))]))
    config = MagicMock()
    config.option.cuke_liberal_steps = True
    matcher = Matcher(config)

    step_item = Step(name="I check state", keyword="Given", type=StepType.context)
    match_defn = matcher(None, None, None, step_item, None, reg)
    assert match_defn.func is then_check
