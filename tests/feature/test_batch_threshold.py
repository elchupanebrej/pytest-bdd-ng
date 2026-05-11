"""Gherkin-style threshold behavior tests using testdir."""

from __future__ import annotations

pytest_plugins = ("pytester",)


def test_sync_parse_below_threshold(testdir) -> None:
    """Below threshold: each file parsed synchronously, no Pool startup."""
    testdir.makeconftest("""\
from pytest_bdd import given, when, then

@given("a")
def a(): pass
@when("b")
def b(): pass
@then("c")
def c(): pass
""")
    for i in range(5):
        testdir.makefile(
            ".feature",
            **{f"f{i:04d}": f"Feature: F{i}\n  Scenario: S\n    Given a\n    When b\n    Then c\n"},
        )

    result = testdir.runpytest("-v")
    result.assert_outcomes(passed=5)


def test_parallel_parse_at_threshold(testdir) -> None:
    """At/above threshold: Pool used. 20 files with threshold=10."""
    testdir.makeconftest("""\
from pytest_bdd import given, when, then

@given("a")
def a(): pass
@when("b")
def b(): pass
@then("c")
def c(): pass
""")
    for i in range(20):
        testdir.makefile(
            ".feature",
            **{f"f{i:04d}": f"Feature: F{i}\n  Scenario: S\n    Given a\n    When b\n    Then c\n"},
        )

    result = testdir.runpytest("-v", "-o", "batch_threshold=10")
    result.assert_outcomes(passed=20)


def test_disable_batch_via_cli(testdir) -> None:
    """--disable-batch-collection skips batch parser entirely."""
    testdir.makeconftest("""\
from pytest_bdd import given, when, then

@given("a")
def a(): pass
@when("b")
def b(): pass
@then("c")
def c(): pass
""")
    for i in range(5):
        testdir.makefile(
            ".feature",
            **{f"f{i:04d}": f"Feature: F{i}\n  Scenario: S\n    Given a\n    When b\n    Then c\n"},
        )

    result = testdir.runpytest("-v", "--disable-batch-collection")
    result.assert_outcomes(passed=5)
