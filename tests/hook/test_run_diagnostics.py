from __future__ import annotations

import pytest

from pytest_bdd.model.scenario_run import (
    ActiveObjectSet,
    HookPhase,
    LifecycleObjectRef,
    Run,
    RunStage,
    RunStatus,
    ScenarioRun,
)


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
    context = _build_context()

    with pytest.raises(RuntimeError, match=r"Feature runtime binding is unavailable.*pytest_bdd_before_scenario"):
        context.require_feature_binding(hook_name="pytest_bdd_before_scenario")

    assert context.last_error is not None
    assert context.last_error.code == "binding_missing"
    assert context.run.last_error is context.last_error
