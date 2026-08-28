from __future__ import annotations

import pytest
from _pytest.compat import NOTSET
from pytest_bdd.compatibility.pytest import (
    Exit,
    Expression,
    Failed,
    is_pytest_version_greater_or_equal,
    is_set,
    is_testrun_success,
    make_mark,
    make_mark_decorator,
)


def test_is_pytest_version_greater_or_equal() -> None:
    assert is_pytest_version_greater_or_equal("7.0") is True
    assert is_pytest_version_greater_or_equal("999.0") is False


def test_is_testrun_success() -> None:
    assert is_testrun_success(0) is True
    assert is_testrun_success(1) is False
    assert is_testrun_success(pytest.ExitCode.OK) is True
    assert is_testrun_success(pytest.ExitCode.TESTS_FAILED) is False


def test_is_set() -> None:
    assert is_set("value") is True
    assert is_set(NOTSET) is False


def test_make_mark_and_decorator() -> None:
    mark = make_mark("smoke", args=("arg1",), kwargs={"key": "val"})
    assert mark.name == "smoke"
    assert mark.args == ("arg1",)
    assert mark.kwargs == {"key": "val"}

    decorator = make_mark_decorator(mark)
    assert decorator.name == "smoke"


def test_outcomes_and_expression() -> None:
    assert issubclass(Exit, BaseException)
    assert issubclass(Failed, BaseException)
    expr = Expression.compile("a and not b")
    assert expr.evaluate(lambda name: name == "a") is True
