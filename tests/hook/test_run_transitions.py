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


def test_transition_updates_stage_for_step_flow() -> None:
    context = _build_context()
    feature = _Dummy("feature", "f-1")
    scenario = _Dummy("scenario", "s-1")
    step = _Dummy("step", "st-1")

    apply_transition(
        context,
        hook_phase=HookPhase.before_step,
        gherkin_document=feature,
        pickle=scenario,
        step=step,
        previous_step=None,
    )

    assert context.stage == RunStage.step_running
    assert context.step_ref is not None
    assert context.step_ref.object_id == "st-1"


def test_transition_marks_failed_status_on_step_error() -> None:
    context = _build_context()
    apply_transition(
        context,
        hook_phase=HookPhase.step_error,
        gherkin_document=_Dummy("feature", "f-1"),
        pickle=_Dummy("scenario", "s-1"),
        step=_Dummy("step", "st-1"),
        previous_step=None,
    )

    assert context.status == RunStatus.failed
    assert context.run.status == RunStatus.failed


def test_transition_clears_scenario_objects_after_after_scenario() -> None:
    context = _build_context()
    context.run.reporting_state.active_test_case_started_id = "case-started-1"
    context.run.reporting_state.active_test_step_id = "step-1"
    context.reference_resolver.add_missing_reference("missing-ast-node")
    apply_transition(
        context,
        hook_phase=HookPhase.after_scenario,
        gherkin_document=_Dummy("feature", "f-1"),
        pickle=_Dummy("scenario", "s-1"),
        step=None,
        previous_step=None,
    )

    assert context.stage == RunStage.finished
    assert context.active_set.scenario is None
    assert context.active_set.step is None
    assert context.run.active_scenario_id is None
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
