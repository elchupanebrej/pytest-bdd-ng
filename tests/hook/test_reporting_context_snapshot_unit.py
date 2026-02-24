from __future__ import annotations

from types import SimpleNamespace

from pytest_bdd.model.execution_context import (
    ActiveObjectSet,
    ExecutionContext,
    ExecutionStage,
    ExecutionStatus,
    HookPhase,
    LifecycleObjectRef,
    SessionExecutionContext,
)
from pytest_bdd.model.hook_parameter_model import ExecutionContextView
from pytest_bdd.plugin.scenario_runner.context_access import build_reporting_context_snapshot
from pytest_bdd.plugin.scenario_runner.context_store import ExecutionContextStore


def _build_execution_context(*, stage: ExecutionStage) -> ExecutionContext:
    run_ref = LifecycleObjectRef(kind="run", object_id="run-1", is_active=True)
    session_root = SessionExecutionContext(
        session_context_id="session-1",
        run_ref=run_ref,
        status=ExecutionStatus.ok,
    )
    return ExecutionContext(
        context_id="ctx-1",
        run_ref=run_ref,
        active_hook=HookPhase.before_scenario,
        stage=stage,
        status=ExecutionStatus.ok,
        active_set=ActiveObjectSet(run=run_ref, captured_at_stage=stage),
        session_context=session_root,
    )


def _build_request(*, config: SimpleNamespace | None = None, session: SimpleNamespace | None = None):
    if config is None:
        config = SimpleNamespace(stash={})
    if session is None:
        session = SimpleNamespace(config=config, name="run-session")
    return SimpleNamespace(config=config, session=session, node=SimpleNamespace(nodeid="node::test"))


def test_snapshot_uses_direct_execution_context_argument() -> None:
    request = _build_request()
    context = _build_execution_context(stage=ExecutionStage.step_running)

    snapshot = build_reporting_context_snapshot(request=request, execution_context=context)

    assert snapshot is not None
    assert snapshot.resolved_from_hierarchy is True
    assert snapshot.fallback_reason is None
    assert snapshot.session_context_id == "session-1"
    assert snapshot.stage == ExecutionStage.step_running


def test_snapshot_uses_request_execution_context_view_node_context() -> None:
    request = _build_request()
    context = _build_execution_context(stage=ExecutionStage.scenario_running)
    request.execution_context = ExecutionContextView(
        session=context.session_context,
        context_id=context.context_id,
        active_set=context.active_set,
        active_hook=context.active_hook,
        stage=context.stage,
        status=context.status,
        transition_index=context.transition_index,
        node_context=context,
    )

    snapshot = build_reporting_context_snapshot(request=request)

    assert snapshot is not None
    assert snapshot.resolved_from_hierarchy is True
    assert snapshot.fallback_reason is None
    assert snapshot.stage == ExecutionStage.scenario_running


def test_snapshot_falls_back_to_session_root_from_stash() -> None:
    config = SimpleNamespace(stash={})
    session = SimpleNamespace(config=config, name="run-session")
    request = _build_request(config=config, session=session)
    stash_root = SessionExecutionContext(
        session_context_id="session-stash",
        run_ref=LifecycleObjectRef(kind="run", object_id="run-stash", is_active=True),
        status=ExecutionStatus.ok,
    )
    ExecutionContextStore.set_session_root_in_config(config, stash_root)

    snapshot = build_reporting_context_snapshot(request=request, fallback_reason="hierarchy-missing")

    assert snapshot is not None
    assert snapshot.resolved_from_hierarchy is False
    assert snapshot.session_context_id == "session-stash"
    assert snapshot.active_set.run.object_id == "run-stash"
    assert snapshot.fallback_reason == "hierarchy-missing"


def test_snapshot_builds_synthetic_fallback_without_stash_context() -> None:
    config = SimpleNamespace(stash={})
    session = SimpleNamespace(config=config, name="run-session")
    request = _build_request(config=config, session=session)

    snapshot = build_reporting_context_snapshot(request=request)

    assert snapshot is not None
    assert snapshot.resolved_from_hierarchy is False
    assert snapshot.fallback_reason == "hierarchy_not_available"
    assert snapshot.active_set.run.kind == "run"
    assert snapshot.active_set.run.object_id == "run-session"
    assert snapshot.session_context_id.startswith("session-")
