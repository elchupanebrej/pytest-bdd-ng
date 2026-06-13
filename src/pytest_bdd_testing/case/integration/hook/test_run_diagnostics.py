"""

Provide test run diagnostics helpers.
"""

from __future__ import annotations

import pytest

from pytest_bdd.model.run import (
    ActiveObjectSet,
    HookPhase,
    LifecycleObjectRef,
    Run,
    RunStage,
    RunStatus,
)
from pytest_bdd.model.scenario_run import ScenarioRun


def _build_context() -> ScenarioRun:
    run_ref = LifecycleObjectRef(kind="run", object_id="run-1", is_active=True)
    active_set = ActiveObjectSet(run=run_ref, captured_at_stage=RunStage.idle)
    return ScenarioRun(
        id="ctx-1",
        run_ref=run_ref,
        run=Run(id="run-1", run_ref=run_ref, status=RunStatus.ok),
        active_hook=HookPhase.before_scenario,
        stage=RunStage.idle,
        status=RunStatus.ok,
        active_set=active_set,
    )


def test_require_feature_binding_raises_with_binding_missing_error() -> None:
    """
    Verify require feature binding raises with binding missing error.

    Test target:
        Ensure pytest hook lifecycle entrypoints trigger correctly and share state safely via config stash.
    Test type:
        Integration test
    Test scenario:
        Given the relevant preconditions are met, when Ensure pytest hook lifecycle entrypoints trigger correctly and
        share state safely via config stash., then the expected outcome is produced.
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
    context = _build_context()

    with pytest.raises(RuntimeError, match=r"Feature runtime binding is unavailable.*pytest_bdd_before_scenario"):
        context.require_feature_binding(hook_name="pytest_bdd_before_scenario")

    assert context.last_error is not None
    assert context.last_error.code == "binding_missing"
    assert context.run.last_error is context.last_error
