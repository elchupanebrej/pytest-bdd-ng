from __future__ import annotations

from pytest_bdd.model.execution_context import (
    ActiveObjectSet,
    ExecutionContext,
    ExecutionStage,
    ExecutionStatus,
    HookPhase,
    LifecycleObjectRef,
)
from pytest_bdd.plugin.scenario_runner.context_access import build_unavailable_object_error


def test_struct_bdd_diagnostics_payload_contains_stage_and_kind() -> None:
    run_ref = LifecycleObjectRef(kind="run", object_id="run-1", is_active=True)
    context = ExecutionContext(
        context_id="ctx-struct",
        run_ref=run_ref,
        active_hook=HookPhase.before_step,
        stage=ExecutionStage.step_running,
        status=ExecutionStatus.ok,
        active_set=ActiveObjectSet(run=run_ref, captured_at_stage=ExecutionStage.step_running),
    )

    error = build_unavailable_object_error(
        hook_name="pytest_bdd_before_step",
        execution_context=context,
        requested_kind="scenario",
    )

    assert error.hook_name == "pytest_bdd_before_step"
    assert error.stage == ExecutionStage.step_running
    assert error.requested_kind == "scenario"
