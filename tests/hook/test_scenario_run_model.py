"""Provide test scenario run model helpers."""

from __future__ import annotations

from pytest_bdd.model.run import (
    ActiveObjectSet,
    HookPhase,
    LifecycleObjectRef,
    Run,
    RunStage,
    RunStatus,
)
from pytest_bdd.model.scenario_run import (
    RunNode,
    ScenarioRun,
)


def _build_context() -> ScenarioRun:
    run_ref = LifecycleObjectRef(kind="run", object_id="run-1", is_active=True)
    run = Run(
        id="run-1",
        run_ref=run_ref,
        status=RunStatus.ok,
    )
    scenario_node = RunNode(
        id="ctx-1",
        parent_id=run.id,
        kind="scenario",
        object_ref=LifecycleObjectRef(kind="scenario", object_id="s-1", is_active=True),
        is_active=True,
        opened_at_transition=0,
    )
    active_set = ActiveObjectSet(run=run_ref, captured_at_stage=RunStage.idle)
    return ScenarioRun(
        id="ctx-1",
        run_ref=run_ref,
        active_hook=HookPhase.before_scenario,
        stage=RunStage.idle,
        status=RunStatus.ok,
        active_set=active_set,
        run=run,
        scenario_node=scenario_node,
    )


def test_scenario_run_starts_with_transition_zero() -> None:
    """Verify scenario run starts with transition zero."""
    context = _build_context()
    assert context.transition_index == 0


def test_scenario_run_advances_transition_index() -> None:
    """Verify scenario run advances transition index."""
    context = _build_context()
    context.advance_transition()
    context.advance_transition()
    assert context.transition_index == 2


def test_scenario_run_active_lookup_respects_inactive_refs() -> None:
    """Verify scenario run active lookup respects inactive refs."""
    context = _build_context()
    context.feature_ref = LifecycleObjectRef.inactive("feature", reason="idle")
    context.set_active_set(
        ActiveObjectSet(
            run=context.run_ref,
            feature=context.feature_ref,
            captured_at_stage=RunStage.scenario_setup,
        ),
    )

    assert context.get_active_object("run") is not None
    assert context.get_active_object("feature") is None


def test_active_object_set_uses_explicit_inactive_slots_by_default() -> None:
    """Verify active object set uses explicit inactive slots by default."""
    run_ref = LifecycleObjectRef(kind="run", object_id="run-1", is_active=True)
    active_set = ActiveObjectSet(run=run_ref, captured_at_stage=RunStage.idle)

    assert active_set.feature.is_active is False
    assert active_set.feature.empty_state_reason == "idle"
    assert active_set.scenario.is_active is False
    assert active_set.step.is_active is False
    assert active_set.previous_step.empty_state_reason == "no_previous_step"
