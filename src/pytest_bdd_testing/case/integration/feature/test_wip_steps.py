"""

WIP step runtime status tests.
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


def _write_wip_case(testdir, *, scenario_decorator: str = "", scenario_tag: str = ""):
    testdir.makeini("[pytest]\ndisable_feature_autoload = true\n")
    testdir.makefile(
        ".feature",
        wip=textwrap.dedent(
            f"""\
            Feature: WIP steps

                {scenario_tag}
                Scenario: Pending step
                    Given a pending step
            """,
        ),
    )
    testdir.makepyfile(
        textwrap.dedent(
            f"""\
            import pytest

            from pytest_bdd import given, not_implemented, scenario


            {scenario_decorator}
            @scenario("wip.feature", "Pending step")
            def test_pending():
                pass


            @not_implemented
            @given("a pending step")
            def pending_step():
                raise NotImplementedError
            """,
        ),
    )


def test_not_implemented_default_fails(testdir):
    """
    Default WIP status executes body and fails.

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
    _write_wip_case(testdir)

    result = _run_pytest_bdd(testdir)

    result.assert_outcomes(failed=1)


def test_wip_status_skipped_reports_skip(testdir):
    """
    CLI skipped policy reports skipped scenario.

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
    _write_wip_case(testdir)

    result = _run_pytest_bdd(testdir, "--wip-status", "skipped")

    result.assert_outcomes(skipped=1)


def test_pytest_marker_wins_over_cli(testdir):
    """
    Pytest marker status wins over CLI status.

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
    _write_wip_case(testdir, scenario_decorator='@pytest.mark.wip_status("passed")')

    result = _run_pytest_bdd(testdir, "--wip-status", "failed")

    result.assert_outcomes(passed=1)


def test_gherkin_tag_wins_over_cli(testdir):
    """
    Gherkin tag status wins over CLI status.

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
    _write_wip_case(testdir, scenario_tag="@wip-status-passed")

    result = _run_pytest_bdd(testdir, "--wip-status", "failed")

    result.assert_outcomes(passed=1)
