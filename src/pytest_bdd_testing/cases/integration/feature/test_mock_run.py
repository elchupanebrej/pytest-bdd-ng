"""Mock-run integration tests."""

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
    """Mock-run verifies step definitions exist."""
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
