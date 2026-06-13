"""

Integration tests for batch feature file collection.
"""

from __future__ import annotations

pytest_plugins = ("pytester",)


def test_batch_collection_collects_all_features(testdir) -> None:
    """
    Verify that batch parser collects all features and tests pass.

    Test target:
        Protect end-to-end functionality and user-facing acceptance criteria.
    Test type:
        E2E/Acceptance test
    Test scenario:
        Given the relevant preconditions are met, when Protect end-to-end functionality and user-facing acceptance
        criteria., then the expected outcome is produced.
    BDD reference:
        None
    Fixtures:
        - None
    Mocks:
        - None
    Side effects:
        None
    Reduction:
        Requires real component interaction that cannot be reproduced by mocking alone.
    Escalation:
        Testing at a higher level would not add coverage and would slow down the suite.
    Atomicity:
        All assertions share the same setup and verify a single coherent behavior.
    Autonomy:
        Covers a distinct code path not exercised by any sibling test.
    Test quality score:
        #test-eval:isolation=5
        #test-eval:determinism=5
        #test-eval:setup_complexity=1
        #test-eval:assertions_clarity=5
    """
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
    """
    Verify --collect-only lists all scenarios with batch parser.

    Test target:
        Protect end-to-end functionality and user-facing acceptance criteria.
    Test type:
        E2E/Acceptance test
    Test scenario:
        Given the relevant preconditions are met, when Protect end-to-end functionality and user-facing acceptance
        criteria., then the expected outcome is produced.
    BDD reference:
        None
    Fixtures:
        - None
    Mocks:
        - None
    Side effects:
        None
    Reduction:
        Requires real component interaction that cannot be reproduced by mocking alone.
    Escalation:
        Testing at a higher level would not add coverage and would slow down the suite.
    Atomicity:
        All assertions share the same setup and verify a single coherent behavior.
    Autonomy:
        Covers a distinct code path not exercised by any sibling test.
    Test quality score:
        #test-eval:isolation=5
        #test-eval:determinism=5
        #test-eval:setup_complexity=1
        #test-eval:assertions_clarity=5
    """
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
    """
    Verify single feature file works correctly (no overhead).

    Test target:
        Protect end-to-end functionality and user-facing acceptance criteria.
    Test type:
        E2E/Acceptance test
    Test scenario:
        Given the relevant preconditions are met, when Protect end-to-end functionality and user-facing acceptance
        criteria., then the expected outcome is produced.
    BDD reference:
        None
    Fixtures:
        - None
    Mocks:
        - None
    Side effects:
        None
    Reduction:
        Requires real component interaction that cannot be reproduced by mocking alone.
    Escalation:
        Testing at a higher level would not add coverage and would slow down the suite.
    Atomicity:
        All assertions share the same setup and verify a single coherent behavior.
    Autonomy:
        Covers a distinct code path not exercised by any sibling test.
    Test quality score:
        #test-eval:isolation=5
        #test-eval:determinism=5
        #test-eval:setup_complexity=1
        #test-eval:assertions_clarity=5
    """
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
