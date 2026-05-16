import sys

import pytest
from pytest_bdd import given, parsers, then

from pytest_bdd.compatibility.enum import StrEnum
from pytest_bdd.compatibility.pytest import Expression


@given(parsers.parse("Python version is {version}"))
def python_version_is(version):
    major, minor = map(int, version.split("."))
    if sys.version_info[:2] != (major, minor):
        pytest.skip(f"Python version is not {version}")


@then("Pytest version compatibility holds")
def pytest_version_compatibility_holds():
    import pytest as pt
    major = int(pt.__version__.split(".")[0])
    assert major >= 7


@given(parsers.parse("Pytest mark expression is {expression}"))
def pytest_mark_expression_is(expression):
    return Expression.compile(expression)


@then("StrEnum behavior is consistent")
def strenum_behavior_is_consistent():
    class TestEnum(StrEnum):
        A = "a"
    assert TestEnum.A == "a"
    assert TestEnum.A.value == "a"
    assert isinstance(TestEnum.A, str)
