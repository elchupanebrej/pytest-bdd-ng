"""

Mock-run integration tests.
"""

from __future__ import annotations

from pytest_bdd.plugin.pickle_runner import entrypoint as pickle_runner_entrypoint
from pytest_bdd.plugin.scenario_test_collector import entrypoint as scenario_test_collector_entrypoint


def _run_pytest_bdd(testdir, *args):
    testdir.monkeypatch.setenv("PYTEST_DISABLE_PLUGIN_AUTOLOAD", "1")
    return testdir.runpytest_inprocess(
        *args,
        plugins=[pickle_runner_entrypoint, scenario_test_collector_entrypoint],
    )


def test_mock_run_still_fails_missing_step_definitions(testdir):
    """
    Mock-run verifies step definitions exist.

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
    testdir.makeini("[pytest]\ndisable_feature_autoload = true\n")
    testdir.makefile(
        ".feature",
        mock_run="""\
        Feature: Mock run

            Scenario: Missing step
                Given a missing step
        """,
    )
    testdir.makepyfile(
        """\
        from pytest_bdd import scenario


        @scenario("mock_run.feature", "Missing step")
        def test_missing():
            pass
        """,
    )

    result = _run_pytest_bdd(testdir, "--mock-run")

    assert result.ret != 0
    result.stdout.fnmatch_lines(['*Step definition is not found: "a missing step".*'])
