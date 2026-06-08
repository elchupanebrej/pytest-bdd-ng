"""Integration tests for batch feature file collection."""

from __future__ import annotations

pytest_plugins = ("pytester",)


def test_batch_collection_collects_all_features(testdir) -> None:
    """Verify that batch parser collects all features and tests pass."""
    testdir.makeconftest(
        """\
import pytest
from pytest_bdd import given, when, then

@given("a step")
def given_a_step():
    pass

@when("another step")
def when_another_step():
    pass

@then("a result")
def then_a_result():
    pass
""",
    )
    testdir.makefile(
        ".feature",
        feature1="""\
Feature: Feature One
  Scenario: Scenario One
    Given a step
    When another step
    Then a result
""",
    )
    testdir.makefile(
        ".feature",
        feature2="""\
Feature: Feature Two
  Scenario: Scenario Two
    Given a step
    When another step
    Then a result
""",
    )
    testdir.makefile(
        ".feature",
        feature3="""\
Feature: Feature Three
  Scenario: Scenario Three
    Given a step
    When another step
    Then a result
""",
    )

    result = testdir.runpytest("-v")
    result.assert_outcomes(passed=3)


def test_batch_collection_collect_only(testdir) -> None:
    """Verify --collect-only lists all scenarios with batch parser."""
    testdir.makeconftest(
        """\
import pytest
from pytest_bdd import given

@given("a step")
def given_a_step():
    pass
""",
    )
    testdir.makefile(
        ".feature",
        feature1="""\
Feature: Feature One
  Scenario: Scenario Alpha
    Given a step
""",
    )

    result = testdir.runpytest("--collect-only", "-q")
    result.stdout.fnmatch_lines(["*Scenario Alpha*"])


def test_batch_collection_single_file_no_overhead(testdir) -> None:
    """Verify single feature file works correctly (no overhead)."""
    testdir.makeconftest(
        """\
import pytest
from pytest_bdd import given

@given("a step")
def given_a_step():
    pass
""",
    )
    testdir.makefile(
        ".feature",
        single="""\
Feature: Single Feature
  Scenario: Single Scenario
    Given a step
""",
    )

    result = testdir.runpytest("-v")
    result.assert_outcomes(passed=1)
