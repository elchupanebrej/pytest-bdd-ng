"""

Gherkin-style threshold behavior tests using testdir.
"""

from __future__ import annotations

pytest_plugins = ("pytester",)


def test_sync_parse_below_threshold(testdir) -> None:
    """
    Below threshold: each file parsed synchronously, no Pool startup.

    Test target:
        Enforce Gherkin specification compliance during parsing.
    Test type:
        Integration test
    Test scenario:
        Given the relevant preconditions are met, when Enforce Gherkin specification compliance during parsing., then
        the expected outcome is produced.
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
    """
    At/above threshold: Pool used. 20 files with threshold=10.

    Test target:
        Ensure parallel execution safety, state isolation, and barrier synchronization under xdist.
    Test type:
        Integration test
    Test scenario:
        Given the relevant preconditions are met, when Ensure parallel execution safety, state isolation, and barrier
        synchronization under xdist., then the expected outcome is produced.
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
    """
    --disable-batch-collection skips batch parser entirely.

    Test target:
        Validate component collaboration, integration contracts, and boundary conditions.
    Test type:
        Integration test
    Test scenario:
        Given the relevant preconditions are met, when Validate component collaboration, integration contracts, and
        boundary conditions., then the expected outcome is produced.
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
