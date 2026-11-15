from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from ordered_set import OrderedSet

from pytest_cuke.model.step import Step, StepType
from pytest_cuke.parsers.parse_parser import parse
from pytest_cuke.parsers.re_parser import re as bdd_re
from pytest_cuke.parsers.string_parser import string
from pytest_cuke.steps.decorators import given
from pytest_cuke.steps.decorators import step as generic_step
from pytest_cuke.steps.matcher import Matcher
from pytest_cuke.steps.registry import Registry
from pytest_cuke.warning_types import PytestBDDStepDefinitionWarning


def test_matcher_strict_and_unspecified() -> None:
    @given(parse("I have {count:d} cucumbers"))
    def given_cucumbers(count: int) -> None:
        pass

    @generic_step(string("I do something generic"))
    def do_generic() -> None:
        pass

    reg = Registry(
        definitions=OrderedSet(
            [
                next(iter(given_cucumbers.__pytest_cuke_step_definitions__)),
                next(iter(do_generic.__pytest_cuke_step_definitions__)),
            ]
        )
    )
    matcher = Matcher(MagicMock())
    step_item = Step(name="I have 5 cucumbers", keyword="Given", type=StepType.context)
    match_defn = matcher(None, None, None, step_item, None, reg)
    assert match_defn.func is given_cucumbers
    assert match_defn.get_parameters(None, step_item) == {"count": 5}

    gen_step = Step(name="I do something generic", keyword="When", type=StepType.action)
    assert matcher(None, None, None, gen_step, None, reg).func is do_generic


def test_matcher_specificity_sort() -> None:
    @given(bdd_re(r"I have \d+ apples"))
    def regex_step() -> None:
        pass

    @given(string("I have 5 apples"))
    def exact_step() -> None:
        pass

    reg = Registry(
        definitions=OrderedSet(
            [
                next(iter(regex_step.__pytest_cuke_step_definitions__)),
                next(iter(exact_step.__pytest_cuke_step_definitions__)),
            ]
        )
    )
    matcher = Matcher(MagicMock())
    step_item = Step(name="I have 5 apples", keyword="Given", type=StepType.context)
    assert matcher(None, None, None, step_item, None, reg).func is exact_step


def test_matcher_hierarchy_parent_fallback() -> None:
    @given(string("parent step"))
    def parent_func() -> None:
        pass

    parent_reg = Registry(definitions=OrderedSet([next(iter(parent_func.__pytest_cuke_step_definitions__))]))
    child_reg = Registry(definitions=OrderedSet([]))
    child_reg.parent = parent_reg

    matcher = Matcher(MagicMock())
    step_item = Step(name="parent step", keyword="Given", type=StepType.context)
    assert matcher(None, None, None, step_item, None, child_reg).func is parent_func


def test_matcher_not_found_error() -> None:
    reg = Registry(definitions=OrderedSet([]))
    matcher = Matcher(MagicMock())
    step_item = Step(name="unknown step", keyword="Given", type=StepType.context)
    with pytest.raises(Matcher.MatchNotFoundError):
        matcher(None, None, None, step_item, None, reg)


def test_exact_string_outranks_parse_template() -> None:
    @given(parse("I have {count:d} pears"))
    def template_step(count: int) -> None:
        pass

    @given(string("I have 5 pears"))
    def exact_step() -> None:
        pass

    reg = Registry(
        definitions=OrderedSet(
            [
                next(iter(template_step.__pytest_cuke_step_definitions__)),
                next(iter(exact_step.__pytest_cuke_step_definitions__)),
            ]
        )
    )
    matcher = Matcher(MagicMock())
    step_item = Step(name="I have 5 pears", keyword="Given", type=StepType.context)
    assert matcher(None, None, None, step_item, None, reg).func is exact_step


def _duplicate_registry() -> Registry:
    @given(parse("ambiguous {value}"))
    def first(value: str) -> None:
        pass

    @given(parse("ambiguous {value}"))
    def second(value: str) -> None:
        pass

    return Registry(
        definitions=OrderedSet(
            [
                next(iter(first.__pytest_cuke_step_definitions__)),
                next(iter(second.__pytest_cuke_step_definitions__)),
            ]
        )
    )


def test_equal_priority_definitions_fail_by_default() -> None:
    matcher = Matcher(MagicMock())
    step_item = Step(name="ambiguous blue", keyword="When", type=StepType.action)

    with pytest.raises(Matcher.MatchAmbiguousError, match="ambiguous blue"):
        matcher(None, None, None, step_item, None, _duplicate_registry())


def test_explicit_first_mode_warns_and_selects_stably() -> None:
    config = MagicMock()
    config.option.cuke_ambiguous_steps = "first"
    matcher = Matcher(config)
    step_item = Step(name="ambiguous blue", keyword="When", type=StepType.action)

    with pytest.warns(PytestBDDStepDefinitionWarning, match="ambiguous blue"):
        selected = matcher(None, None, None, step_item, None, _duplicate_registry())

    assert selected.func.__name__ == "first"
