import sys

import pytest

from hamcrest import assert_that, greater_than_or_equal_to
from pytest_bdd import given, parsers, then
from pytest_bdd.compatibility.pytest import Expression


@given(parsers.parse("Python version is {version}"))
def python_version_is(version) -> None:
    major, minor = map(int, version.split("."))
    if sys.version_info[:2] != (major, minor):
        pytest.skip(f"Python version is not {version}")


@then("Pytest version compatibility holds")
def _pytest_version_compatibility_holds() -> None:
    major = int(pytest.__version__.split(".")[0])
    assert_that(major, greater_than_or_equal_to(7))


@given(parsers.parse("Pytest mark expression is {expression}"))
def _pytest_mark_expression_is(expression):
    expression = expression.strip('"').strip("'")
    return Expression.compile(expression)
