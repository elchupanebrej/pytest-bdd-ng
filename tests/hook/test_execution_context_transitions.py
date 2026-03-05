from __future__ import annotations

from dataclasses import dataclass

from pytest_bdd.model.execution_context import (
    ActiveObjectSet,
    ExecutionContext,
    ExecutionContextNode,
    ExecutionStage,
    ExecutionStatus,
    HookPhase,
    LifecycleObjectRef,
    SessionExecutionContext,
)
from pytest_bdd.plugin.scenario_runner.context_transitions import apply_transition


@dataclass(slots=True)
class _Dummy:
    name: str
    id: str


def _build_context() -> ExecutionContext:
    run_ref = LifecycleObjectRef(kind="run", object_id="run", is_active=True)
    session = SessionExecutionContext(
        session_context_id="session-1",
        run_ref=run_ref,
        status=ExecutionStatus.ok,
    )
    scenario_node = ExecutionContextNode(
        context_id="ctx",
        parent_context_id=session.session_context_id,
        kind="scenario",
        object_ref=LifecycleObjectRef(kind="scenario", object_id="s-1", is_active=True),
        is_active=True,
        opened_at_transition=0,
    )
    active_set = ActiveObjectSet(run=run_ref, captured_at_stage=ExecutionStage.idle)
    return ExecutionContext(
        context_id="ctx",
        run_ref=run_ref,
        active_hook=HookPhase.before_scenario,
        stage=ExecutionStage.idle,
        status=ExecutionStatus.ok,
        active_set=active_set,
        session_context=session,
        scenario_node=scenario_node,
    )


def test_transition_updates_stage_for_step_flow() -> None:
    context = _build_context()
    feature = _Dummy("feature", "f-1")
    scenario = _Dummy("scenario", "s-1")
    step = _Dummy("step", "st-1")

    apply_transition(
        context,
        hook_phase=HookPhase.before_step,
        run=_Dummy("run", "run"),
        feature=feature,
        scenario=scenario,
        step=step,
        previous_step=None,
    )

    assert context.stage == ExecutionStage.step_running
    assert context.step_ref is not None
    assert context.step_ref.object_id == "st-1"


def test_transition_marks_failed_status_on_step_error() -> None:
    context = _build_context()
    apply_transition(
        context,
        hook_phase=HookPhase.step_error,
        run=_Dummy("run", "run"),
        feature=_Dummy("feature", "f-1"),
        scenario=_Dummy("scenario", "s-1"),
        step=_Dummy("step", "st-1"),
        previous_step=None,
    )

    assert context.status == ExecutionStatus.failed
    assert context.session_context.status == ExecutionStatus.failed


def test_transition_clears_scenario_objects_after_after_scenario() -> None:
    context = _build_context()
    context.reporting_state.active_test_case_started_id = "case-started-1"
    context.reporting_state.active_test_step_id = "step-1"
    context.reference_resolver.add_missing_reference("missing-ast-node")
    apply_transition(
        context,
        hook_phase=HookPhase.after_scenario,
        run=_Dummy("run", "run"),
        feature=_Dummy("feature", "f-1"),
        scenario=_Dummy("scenario", "s-1"),
        step=None,
        previous_step=None,
    )

    assert context.stage == ExecutionStage.finished
    assert context.active_set.scenario is None
    assert context.active_set.step is None
    assert context.session_context.active_scenario_context_id is None
    assert context.reporting_state.active_test_case_started_id == "case-started-1"
    assert context.reporting_state.active_test_step_id == "step-1"
    assert context.reference_resolver.missing_reference_diagnostics == ["missing-ast-node"]
