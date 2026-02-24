from __future__ import annotations

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
from pytest_bdd.model.hook_parameter_model import ExecutionContextView


def _build_context() -> ExecutionContext:
    run_ref = LifecycleObjectRef(kind="run", object_id="run-1", is_active=True)
    session = SessionExecutionContext(
        session_context_id="session-1",
        run_ref=run_ref,
        status=ExecutionStatus.ok,
    )
    scenario_node = ExecutionContextNode(
        context_id="ctx-1",
        parent_context_id=session.session_context_id,
        kind="scenario",
        object_ref=LifecycleObjectRef(kind="scenario", object_id="s-1", is_active=True),
        is_active=True,
        opened_at_transition=0,
    )
    active_set = ActiveObjectSet(run=run_ref, captured_at_stage=ExecutionStage.idle)
    return ExecutionContext(
        context_id="ctx-1",
        run_ref=run_ref,
        active_hook=HookPhase.before_scenario,
        stage=ExecutionStage.idle,
        status=ExecutionStatus.ok,
        active_set=active_set,
        session_context=session,
        scenario_node=scenario_node,
    )


def test_execution_context_starts_with_transition_zero() -> None:
    context = _build_context()
    assert context.transition_index == 0


def test_execution_context_advances_transition_index() -> None:
    context = _build_context()
    context.advance_transition()
    context.advance_transition()
    assert context.transition_index == 2


def test_execution_context_active_lookup_respects_inactive_refs() -> None:
    context = _build_context()
    context.feature_ref = LifecycleObjectRef(kind="feature", object_id="feature-1", is_active=False)
    context.set_active_set(
        ActiveObjectSet(
            run=context.run_ref,
            feature=context.feature_ref,
            captured_at_stage=ExecutionStage.scenario_setup,
        )
    )

    assert context.get_active_object("run") is not None
    assert context.get_active_object("feature") is None


def test_execution_context_view_contains_session_root() -> None:
    context = _build_context()
    view = ExecutionContextView(
        session=context.session_context,
        context_id=context.context_id,
        active_set=context.active_set,
        active_hook=context.active_hook,
        stage=context.stage,
        status=context.status,
        transition_index=context.transition_index,
        node_context=context,
    )

    assert view.session.session_context_id == "session-1"
    assert view.context_id == "ctx-1"
