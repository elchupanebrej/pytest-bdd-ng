"""WIP step runtime status tests."""

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
    """Default WIP status executes body and fails."""
    _write_wip_case(testdir)

    result = _run_pytest_bdd(testdir)

    result.assert_outcomes(failed=1)


def test_wip_status_skipped_reports_skip(testdir):
    """CLI skipped policy reports skipped scenario."""
    _write_wip_case(testdir)

    result = _run_pytest_bdd(testdir, "--wip-status", "skipped")

    result.assert_outcomes(skipped=1)


def test_pytest_marker_wins_over_cli(testdir):
    """Pytest marker status wins over CLI status."""
    _write_wip_case(testdir, scenario_decorator='@pytest.mark.wip_status("passed")')

    result = _run_pytest_bdd(testdir, "--wip-status", "failed")

    result.assert_outcomes(passed=1)


def test_gherkin_tag_wins_over_cli(testdir):
    """Gherkin tag status wins over CLI status."""
    _write_wip_case(testdir, scenario_tag="@wip-status-passed")

    result = _run_pytest_bdd(testdir, "--wip-status", "failed")

    result.assert_outcomes(passed=1)
