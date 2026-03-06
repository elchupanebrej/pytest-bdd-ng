from __future__ import annotations

from pytest_bdd.model.scenario_run import (
    ActiveObjectSet,
    RunStage,
    RunStatus,
    HookPhase,
    LifecycleObjectRef,
    ScenarioRun,
)
from pytest_bdd.plugin.pickle_runner.run_access import build_unavailable_object_error


def test_struct_bdd_diagnostics_payload_contains_stage_and_kind() -> None:
    run_ref = LifecycleObjectRef(kind="run", object_id="run-1", is_active=True)
    context = ScenarioRun(
        id="ctx-struct",
        run_ref=run_ref,
        active_hook=HookPhase.before_step,
        stage=RunStage.step_running,
        status=RunStatus.ok,
        active_set=ActiveObjectSet(run=run_ref, captured_at_stage=RunStage.step_running),
    )

    error = build_unavailable_object_error(
        hook_name="pytest_bdd_before_step",
        scenario_run=context,
        requested_kind="scenario",
    )

    assert error.hook_name == "pytest_bdd_before_step"
    assert error.stage == RunStage.step_running
    assert error.requested_kind == "scenario"
