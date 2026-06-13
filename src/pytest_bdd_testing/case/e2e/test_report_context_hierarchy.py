"""

Provide test report context hierarchy helpers.
"""

from __future__ import annotations


def _find_bdd_call_report(result):
    for rep in result.getreports(names="pytest_runtest_logreport pytest_collectreport"):
        if getattr(rep, "when", None) != "call":
            continue
        if hasattr(rep, "scenario"):
            return rep
    raise LookupError


def test_reporting_snapshot_uses_context_hierarchy(testdir):
    """
    Verify reporting snapshot uses context hierarchy.

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
    testdir.makefile(
        ".ini",
        pytest="""
        [pytest]
        disable_feature_autoload = true
        """,
    )

    testdir.makefile(
        ".feature",
        test="""
        Feature: Reporting context snapshot
            Scenario: Reporting gets hierarchy snapshot
                Given first step
                When second step
        """,
    )

    testdir.makepyfile(
        """
        from pytest_bdd import given, scenario, when

        @scenario('test.feature', 'Reporting gets hierarchy snapshot')
        def test_reporting_gets_hierarchy_snapshot():
            pass

        @given('first step')
        def first_step():
            return None

        @when('second step')
        def second_step():
            return None
        """,
    )

    result = testdir.inline_run("-q")
    report = _find_bdd_call_report(result)

    assert report.passed
    assert hasattr(report, "execution_context_snapshot")

    snapshot = report.execution_context_snapshot
    assert snapshot["resolved_from_hierarchy"] is True
    assert snapshot["fallback_reason"] is None
    assert snapshot["stage"] == "finished"
    assert snapshot["active_set"]["run"]["kind"] == "run"
    assert snapshot["active_set"]["scenario"]["is_active"] is False
    assert snapshot["active_set"]["scenario"]["empty_state_reason"] == "finished"
    assert snapshot["run_id"].startswith("run-")
