from __future__ import annotations

from pytest_bdd.model.scenario_run import (
    ActiveObjectSet,
    HookPhase,
    LifecycleObjectRef,
    Run,
    RunNode,
    RunStage,
    RunStatus,
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
    context = _build_context()
    assert context.transition_index == 0


def test_scenario_run_advances_transition_index() -> None:
    context = _build_context()
    context.advance_transition()
    context.advance_transition()
    assert context.transition_index == 2


def test_scenario_run_active_lookup_respects_inactive_refs() -> None:
    context = _build_context()
    context.feature_ref = LifecycleObjectRef(kind="feature", object_id="feature-1", is_active=False)
    context.set_active_set(
        ActiveObjectSet(
            run=context.run_ref,
            feature=context.feature_ref,
            captured_at_stage=RunStage.scenario_setup,
        )
    )

    assert context.get_active_object("run") is not None
    assert context.get_active_object("feature") is None
