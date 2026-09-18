from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from ordered_set import OrderedSet

from pytest_bdd.model.step import Step, StepType
from pytest_bdd.parsers.parse_parser import parse
from pytest_bdd.parsers.re_parser import re as bdd_re
from pytest_bdd.parsers.string_parser import string
from pytest_bdd.steps.decorators import given, then
from pytest_bdd.steps.decorators import step as generic_step
from pytest_bdd.steps.matcher import Matcher
from pytest_bdd.steps.registry import Registry

pytestmark = pytest.mark.unit


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
                next(iter(given_cucumbers.__pytest_bdd_step_definitions__)),
                next(iter(do_generic.__pytest_bdd_step_definitions__)),
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
                next(iter(regex_step.__pytest_bdd_step_definitions__)),
                next(iter(exact_step.__pytest_bdd_step_definitions__)),
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

    parent_reg = Registry(definitions=OrderedSet([next(iter(parent_func.__pytest_bdd_step_definitions__))]))
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


def test_matcher_conjunction_type_inherits_previous_step_type() -> None:
    @given(string("I have a conjunction step"))
    def conjunction_step() -> None:
        pass

    reg = Registry(definitions=OrderedSet([next(iter(conjunction_step.__pytest_bdd_step_definitions__))]))
    matcher = Matcher(MagicMock())
    previous = Step(name="previous", keyword="Given", type=StepType.context)
    step_item = Step(name="I have a conjunction step", keyword="And", type="Conjunction")

    assert matcher(None, None, None, step_item, previous, reg).func is conjunction_step


def test_matcher_unknown_keyword_is_unknown_step_type() -> None:
    matcher = Matcher(MagicMock())
    step_item = Step(name="mystery", keyword="Zzz", type=None)
    with pytest.raises(Matcher.MatchNotFoundError):
        matcher(None, None, None, step_item, None, Registry(definitions=OrderedSet([])))


def test_matcher_liberal_mode_without_cli_or_ini_option() -> None:
    @then(string("I check liberal fallback"))
    def then_state() -> None:
        pass

    class ConfigWithoutLiberalOption:
        option = SimpleNamespace()

        @staticmethod
        def getini(name):
            raise ValueError(name)

    reg = Registry(definitions=OrderedSet([next(iter(then_state.__pytest_bdd_step_definitions__))]))
    matcher = Matcher(ConfigWithoutLiberalOption())
    step_item = Step(name="I check liberal fallback", keyword="Given", type=StepType.context)
    with pytest.raises(Matcher.MatchNotFoundError):
        matcher(None, None, None, step_item, None, reg)
