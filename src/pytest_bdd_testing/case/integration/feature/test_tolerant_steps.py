"""

Tolerant step runtime status tests.
"""

from __future__ import annotations

import textwrap

from pytest_bdd.plugin.pickle_runner import entrypoint as pickle_runner_entrypoint
from pytest_bdd.plugin.scenario_test_collector import entrypoint as scenario_test_collector_entrypoint


def _run_pytest_bdd(testdir, *args):
    testdir.monkeypatch.setenv("PYTEST_DISABLE_PLUGIN_AUTOLOAD", "1")
    return testdir.runpytest_inprocess(
        *args,
        plugins=[pickle_runner_entrypoint, scenario_test_collector_entrypoint],
    )


def _write_tolerant_case(testdir, *, scenario_decorator: str = "", scenario_tag: str = ""):
    testdir.makeini("[pytest]\ndisable_feature_autoload = true\n")
    testdir.makefile(
        ".feature",
        tolerant=textwrap.dedent(
            f"""\
            Feature: Tolerant steps

                {scenario_tag}
                Scenario: Tolerant failure
                    Given a tolerant step fails
                    Then a later step runs
            """,
        ),
    )
    testdir.makepyfile(
        textwrap.dedent(
            f"""\
            from pathlib import Path

            import pytest

            from pytest_bdd import given, scenario, then, tolerant


            {scenario_decorator}
            @scenario("tolerant.feature", "Tolerant failure")
            def test_tolerant_failure():
                pass


            @tolerant
            @given("a tolerant step fails")
            def tolerant_step():
                raise AssertionError("soft failure")


            @then("a later step runs")
            def later_step():
                Path("later.txt").write_text("ran", encoding="utf-8")
            """,
        ),
    )


def test_tolerant_step_default_fails(testdir):
    """
    Default tolerant status preserves strict failure behavior.

    Test target:
        Guard exception handling, validation checks, and error reporting to ensure fail-safe execution.
    Test type:
        Integration test
    Test scenario:
        Given the relevant preconditions are met, when Guard exception handling, validation checks, and error reporting
        to ensure fail-safe execution., then the expected outcome is produced.
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
    _write_tolerant_case(testdir)

    result = _run_pytest_bdd(testdir)

    result.assert_outcomes(failed=1)
    assert not testdir.tmpdir.join("later.txt").check()


def test_pytest_marker_wins_over_tolerant_cli(testdir):
    """
    Pytest marker status wins over CLI tolerant status.

    Test target:
        Allow step matching flexibility for user convenience without causing false positive failures.
    Test type:
        Integration test
    Test scenario:
        Given the relevant preconditions are met, when Allow step matching flexibility for user convenience without
        causing false positive failures., then the expected outcome is produced.
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
    _write_tolerant_case(testdir, scenario_decorator='@pytest.mark.tolerant_status("ignored")')

    result = _run_pytest_bdd(testdir, "--tolerant-status", "failed")

    result.assert_outcomes(passed=1)
    assert testdir.tmpdir.join("later.txt").read() == "ran"


def test_gherkin_tag_wins_over_tolerant_cli(testdir):
    """
    Gherkin tag status wins over CLI tolerant status.

    Test target:
        Allow step matching flexibility for user convenience without causing false positive failures.
    Test type:
        Integration test
    Test scenario:
        Given the relevant preconditions are met, when Allow step matching flexibility for user convenience without
        causing false positive failures., then the expected outcome is produced.
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
    _write_tolerant_case(testdir, scenario_tag="@tolerant-status-ignored")

    result = _run_pytest_bdd(testdir, "--tolerant-status", "failed")

    result.assert_outcomes(passed=1)
    assert testdir.tmpdir.join("later.txt").read() == "ran"
