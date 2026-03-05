from __future__ import annotations

from pytest_bdd.model.scenario_run import (
    ActiveObjectSet,
    RunStage,
    RunStatus,
    HookPhase,
    LifecycleObjectRef,
    ScenarioRun,
)
from pytest_bdd.plugin.scenario_runner.run_access import resolve_active_object_or_error


def _build_context() -> ScenarioRun:
    run_ref = LifecycleObjectRef(kind="run", object_id="run-1", is_active=True)
    active_set = ActiveObjectSet(run=run_ref, captured_at_stage=RunStage.idle)
    return ScenarioRun(
        context_id="ctx-1",
        run_ref=run_ref,
        active_hook=HookPhase.before_scenario,
        stage=RunStage.idle,
        status=RunStatus.ok,
        active_set=active_set,
    )


def test_inactive_object_resolution_returns_structured_error() -> None:
    context = _build_context()

    active_object, error = resolve_active_object_or_error(
        hook_name="pytest_bdd_before_step",
        scenario_run=context,
        requested_kind="feature",
    )

    assert active_object is None
    assert error is not None
    assert error.code == "object_inactive"
    assert error.requested_kind == "feature"


def test_active_object_resolution_returns_reference() -> None:
    context = _build_context()
    active_object, error = resolve_active_object_or_error(
        hook_name="pytest_bdd_before_step",
        scenario_run=context,
        requested_kind="run",
    )

    assert error is None
    assert active_object is not None
    assert active_object.object_id == "run-1"
