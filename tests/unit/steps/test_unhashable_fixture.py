from __future__ import annotations

from pytest_bdd.steps.definition import Definition
from pytest_bdd.steps.registry import Registry
from pytest_bdd.parsers.string_parser import string


def test_definition_with_unhashable_defaults_is_hashable():
    def dummy_func():
        pass

    defn = Definition(
        func=dummy_func,
        type_="Context",
        parser=string("test {param}"),
        anonymous_group_names=None,
        converters={},
        params_fixtures_mapping={"param": "param"},
        param_defaults={"param": {"nested": [1, 2, 3]}},
        target_fixtures=[],
        liberal=None,
    )

    reg = Registry()
    # Adding to set / registry must not raise TypeError: unhashable type: 'dict'
    reg.registry.add(defn)
    assert defn in reg.registry


def test_module_with_unhashable_fixture(testdir):
    testdir.makepyfile(
        conftest="""
import pytest
from pytest_bdd import given

@pytest.fixture
def unhashable_dict_fixture():
    return {"a": 1, "b": [2, 3]}

@pytest.fixture
def unhashable_list_fixture():
    return [{"item": 1}, {"item": 2}]

@given("I check unhashable fixture")
def check_fixture(unhashable_dict_fixture, unhashable_list_fixture):
    assert unhashable_dict_fixture["a"] == 1
    assert len(unhashable_list_fixture) == 2
"""
    )
    testdir.makefile(
        ".feature",
        test_feature="""
Feature: Unhashable fixtures
    Scenario: Use unhashable fixture in step
        Given I check unhashable fixture
""",
    )
    result = testdir.runpytest_inprocess()
    result.assert_outcomes(passed=1)
