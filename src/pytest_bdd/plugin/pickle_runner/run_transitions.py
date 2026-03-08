from __future__ import annotations

from itertools import count
from typing import TYPE_CHECKING, Any

from pytest_bdd.model.scenario_run import (
    ActiveObjectSet,
    HookPhase,
    LifecycleKind,
    LifecycleObjectRef,
    RunNode,
    RunStage,
    RunStatus,
    ScenarioRun,
)

if TYPE_CHECKING:
    from cucumber_messages import GherkinDocument

    from pytest_bdd.compatibility.pytest import FixtureRequest

_context_index = count(1)


PHASE_TO_STAGE: dict[HookPhase, RunStage] = {
    HookPhase.before_scenario: RunStage.scenario_setup,
    HookPhase.run_scenario: RunStage.scenario_running,
    HookPhase.after_scenario: RunStage.scenario_teardown,
    HookPhase.run_step: RunStage.step_running,
    HookPhase.before_step: RunStage.step_running,
    HookPhase.before_step_call: RunStage.step_running,
    HookPhase.after_step: RunStage.scenario_running,
    HookPhase.step_error: RunStage.scenario_running,
    HookPhase.step_lookup_error: RunStage.scenario_running,
}


def runtime_object_id(obj: Any) -> str:
    if obj is None:
        return "none"
    explicit_id = getattr(obj, "id", None)
    if explicit_id is not None:
        return str(explicit_id)
    nodeid = getattr(obj, "nodeid", None)
    if nodeid is not None:
        return str(nodeid)
    name = getattr(obj, "name", None)
    if name is not None:
        return str(name)
    ast_node_ids = getattr(obj, "ast_node_ids", None)
    if ast_node_ids:
        return str(ast_node_ids[0])
    return str(id(obj))


def runtime_object_name(obj: Any) -> str | None:
    if obj is None:
        return None
    name = getattr(obj, "name", None)
    return str(name) if name is not None else None


def build_lifecycle_ref(kind: LifecycleKind, value: Any, *, is_active: bool) -> LifecycleObjectRef | None:
    if value is None:
        return None
    return LifecycleObjectRef(
        kind=kind,
        object_id=runtime_object_id(value),
        name=runtime_object_name(value),
        source=value.__class__.__name__,
        is_active=is_active,
    )


def initial_scenario_run_id(request: FixtureRequest) -> str:
    node_id = getattr(getattr(request, "node", None), "nodeid", None)
    key = node_id or f"unknown-{next(_context_index)}"
    return f"ctx-{key}-{next(_context_index)}"


def apply_transition(
    scenario_run: ScenarioRun,
    *,
    hook_phase: HookPhase,
    gherkin_document: GherkinDocument | None = None,
    pickle: Any | None = None,
    step: Any | None = None,
    previous_step: Any | None = None,
    status: RunStatus | None = None,
) -> ScenarioRun:
    stage = PHASE_TO_STAGE[hook_phase]
    run = scenario_run.run

    run_ref = scenario_run.run_ref if run is None else build_lifecycle_ref("run", run, is_active=True)
    if run_ref is None:
        run_ref = scenario_run.run_ref

    scenario_is_active = stage not in {RunStage.idle, RunStage.finished}
    feature_is_active = scenario_is_active
    step_is_active = stage is RunStage.step_running

    feature_ref = (
        build_lifecycle_ref("feature", gherkin_document, is_active=feature_is_active)
        if gherkin_document is not None
        else None
    )
    scenario_ref = build_lifecycle_ref("scenario", pickle, is_active=scenario_is_active) if pickle is not None else None

    if hook_phase is HookPhase.after_scenario:
        step_ref = None
        previous_step_ref = None
        scenario_run.step_node = None
    else:
        step_ref = build_lifecycle_ref("step", step, is_active=step_is_active) if step is not None else None
        previous_step_ref = (
            build_lifecycle_ref("step", previous_step, is_active=previous_step is not None)
            if previous_step is not None
            else None
        )
        if step_ref is not None and step_is_active:
            parent_id = scenario_run.scenario_node.id if scenario_run.scenario_node is not None else scenario_run.id
            scenario_run.step_node = RunNode(
                id=f"step-{step_ref.object_id}-{scenario_run.transition_index + 1}",
                parent_id=parent_id,
                kind="step",
                object_ref=step_ref,
                is_active=True,
                opened_at_transition=scenario_run.transition_index + 1,
            )
        else:
            scenario_run.step_node = None

    scenario_run.active_hook = hook_phase
    scenario_run.stage = stage
    scenario_run.status = status or scenario_run.status
    if hook_phase in {HookPhase.step_error, HookPhase.step_lookup_error} and status is None:
        scenario_run.status = RunStatus.failed

    scenario_run.feature_ref = feature_ref
    scenario_run.scenario_ref = scenario_ref
    scenario_run.step_ref = step_ref
    scenario_run.previous_step_ref = previous_step_ref
    scenario_run.gherkin_document = gherkin_document
    scenario_run.pickle = pickle
    scenario_run.step_object = step
    scenario_run.previous_step_object = previous_step

    scenario_run.set_active_set(
        ActiveObjectSet(
            run=run_ref,
            feature=feature_ref,
            scenario=scenario_ref,
            step=step_ref,
            previous_step=previous_step_ref,
            captured_at_stage=stage,
        )
    )
    scenario_run.advance_transition()
    if run is not None:
        run.active_scenario_run = scenario_run
        run.advance_transition()
        run.status = scenario_run.status
        run.active_feature_id = (
            scenario_run.feature_node.id
            if scenario_run.feature_node is not None and scenario_run.feature_node.is_active
            else None
        )
        run.active_scenario_id = (
            scenario_run.scenario_node.id
            if scenario_run.scenario_node is not None and scenario_run.scenario_node.is_active
            else None
        )
        run.active_step_id = (
            scenario_run.step_node.id
            if scenario_run.step_node is not None and scenario_run.step_node.is_active
            else None
        )

    if hook_phase is HookPhase.after_scenario:
        if scenario_run.scenario_node is not None:
            scenario_run.scenario_node.close(scenario_run.transition_index)
        if scenario_run.feature_node is not None:
            scenario_run.feature_node.close(scenario_run.transition_index)

        scenario_run.stage = RunStage.finished
        scenario_run.step_object = None
        scenario_run.previous_step_object = None
        scenario_run.set_active_set(
            ActiveObjectSet(
                run=run_ref,
                feature=None,
                scenario=None,
                step=None,
                previous_step=None,
                captured_at_stage=RunStage.finished,
            )
        )
        if run is not None:
            run.active_scenario_id = None
            run.active_step_id = None

    return scenario_run
