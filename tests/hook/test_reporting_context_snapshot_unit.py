from __future__ import annotations

from types import SimpleNamespace

from pytest_bdd.model.scenario_run import (
    ActiveObjectSet,
    HookPhase,
    LifecycleObjectRef,
    Run,
    RunStage,
    RunStatus,
    ScenarioRun,
)
from pytest_bdd.plugin.pickle_runner.run_access import build_reporting_context_snapshot


def _build_scenario_run(*, stage: RunStage) -> ScenarioRun:
    run_ref = LifecycleObjectRef(kind="run", object_id="run-1", is_active=True)
    run_root = Run(
        id="run-1",
        run_ref=run_ref,
        status=RunStatus.ok,
    )
    return ScenarioRun(
        id="ctx-1",
        run_ref=run_ref,
        active_hook=HookPhase.before_scenario,
        stage=stage,
        status=RunStatus.ok,
        active_set=ActiveObjectSet(run=run_ref, captured_at_stage=stage),
        run=run_root,
    )


def _build_request(*, config: SimpleNamespace | None = None, session: SimpleNamespace | None = None):
    if config is None:
        config = SimpleNamespace(stash={})
    if session is None:
        session = SimpleNamespace(config=config, name="run-session")
    return SimpleNamespace(config=config, session=session, node=SimpleNamespace(nodeid="node::test"))


def test_snapshot_uses_run_from_stash_with_active_scenario() -> None:
    request = _build_request()
    context = _build_scenario_run(stage=RunStage.scenario_running)
    context.run.active_scenario_run = context
    context.run.set_in_pytest_stash(request.config)

    snapshot = build_reporting_context_snapshot(request=request)

    assert snapshot is not None
    assert snapshot.resolved_from_hierarchy is True
    assert snapshot.fallback_reason is None
    assert snapshot.stage == RunStage.scenario_running


def test_snapshot_falls_back_to_run_root_from_stash() -> None:
    config = SimpleNamespace(stash={})
    session = SimpleNamespace(config=config, name="run-session")
    request = _build_request(config=config, session=session)
    stash_root = Run(
        id="run-stash",
        run_ref=LifecycleObjectRef(kind="run", object_id="run-stash", is_active=True),
        status=RunStatus.ok,
    )
    stash_root.set_in_pytest_stash(config)

    snapshot = build_reporting_context_snapshot(request=request, fallback_reason="hierarchy-missing")

    assert snapshot is not None
    assert snapshot.resolved_from_hierarchy is True
    assert snapshot.run_id == "run-stash"
    assert snapshot.active_set.run.object_id == "run-stash"
    assert snapshot.fallback_reason == "hierarchy-missing"
