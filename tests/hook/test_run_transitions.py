from __future__ import annotations

from dataclasses import dataclass

import pytest

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
from pytest_bdd.plugin.pickle_runner.plugin import PickleRunner
from pytest_bdd.plugin.pickle_runner.run_transitions import apply_transition


@dataclass(slots=True)
class _Dummy:
    name: str
    id: str


@dataclass(slots=True)
class _TransitionInputs:
    feature: _Dummy
    scenario: _Dummy
    step: _Dummy
    previous_step: _Dummy


def _build_context() -> ScenarioRun:
    run_ref = LifecycleObjectRef(kind="run", object_id="run", is_active=True)
    session = Run(
        id="run-1",
        run_ref=run_ref,
        status=RunStatus.ok,
    )
    scenario_node = RunNode(
        id="ctx",
        parent_id=session.id,
        kind="scenario",
        object_ref=LifecycleObjectRef(kind="scenario", object_id="s-1", is_active=True),
        is_active=True,
        opened_at_transition=0,
    )
    active_set = ActiveObjectSet(run=run_ref, captured_at_stage=RunStage.idle)
    return ScenarioRun(
        id="ctx",
        run_ref=run_ref,
        active_hook=HookPhase.before_scenario,
        stage=RunStage.idle,
        status=RunStatus.ok,
        active_set=active_set,
        run=session,
        scenario_node=scenario_node,
    )


def _build_transition_inputs() -> _TransitionInputs:
    return _TransitionInputs(
        feature=_Dummy("feature", "f-1"),
        scenario=_Dummy("scenario", "s-1"),
        step=_Dummy("step", "st-1"),
        previous_step=_Dummy("previous-step", "st-0"),
    )


def test_transition_updates_stage_for_step_flow() -> None:
    context = _build_context()
    inputs = _build_transition_inputs()

    apply_transition(
        context,
        hook_phase=HookPhase.before_step,
        gherkin_document=inputs.feature,
        pickle=inputs.scenario,
        step=inputs.step,
        previous_step=None,
    )

    assert context.stage == RunStage.step_running
    assert context.step_ref.object_id == "st-1"
    assert context.active_set.previous_step.empty_state_reason == "no_previous_step"


def test_transition_marks_failed_status_on_step_error() -> None:
    context = _build_context()
    inputs = _build_transition_inputs()
    apply_transition(
        context,
        hook_phase=HookPhase.step_error,
        gherkin_document=inputs.feature,
        pickle=inputs.scenario,
        step=inputs.step,
        previous_step=None,
    )

    assert context.status == RunStatus.failed
    assert context.run.status == RunStatus.failed


def test_transition_clears_scenario_objects_after_after_scenario() -> None:
    context = _build_context()
    inputs = _build_transition_inputs()
    context.run.reporting_state.active_test_case_started_id = "case-started-1"
    context.run.reporting_state.active_test_step_id = "step-1"
    context.reference_resolver.add_missing_reference("missing-ast-node")
    apply_transition(
        context,
        hook_phase=HookPhase.after_scenario,
        gherkin_document=inputs.feature,
        pickle=inputs.scenario,
        step=None,
        previous_step=None,
    )

    assert context.stage == RunStage.finished
    assert context.active_set.feature.is_active is False
    assert context.active_set.feature.empty_state_reason == "finished"
    assert context.active_set.scenario.is_active is False
    assert context.active_set.scenario.empty_state_reason == "finished"
    assert context.active_set.step.is_active is False
    assert context.active_set.step.empty_state_reason == "finished"
    with pytest.raises(AttributeError, match="No active scenario"):
        _ = context.run.active_scenario_id
    assert context.run.reporting_state.active_test_case_started_id == "case-started-1"
    assert context.run.reporting_state.active_test_step_id == "step-1"
    assert context.reference_resolver.missing_reference_diagnostics == ["missing-ast-node"]


def test_pickle_runner_raises_when_lifecycle_hook_has_no_active_scenario_run() -> None:
    runner = PickleRunner()
    run_ref = LifecycleObjectRef(kind="run", object_id="run", is_active=True)
    run = Run(id="run-1", run_ref=run_ref, status=RunStatus.ok)
    config = type(
        "_Config",
        (),
        {
            "stash": {},
            "hook": type("_Hook", (), {"pytest_bdd_before_scenario": staticmethod(lambda **_kwargs: None)})(),
        },
    )()
    run.set_in_stash(config.stash)
    request = type("_Request", (), {"config": config})()

    with pytest.raises(RuntimeError, match=r"Active scenario run.*pytest_bdd_before_scenario"):
        runner._invoke_bdd_hook(
            hook_name="pytest_bdd_before_scenario",
            request=request,
            gherkin_document=_Dummy("feature", "f-1"),
            pickle=_Dummy("scenario", "s-1"),
        )
