"""Provide run transitions helpers."""

from __future__ import annotations

from itertools import count
from typing import TYPE_CHECKING

from returns.maybe import Nothing

from pytest_bdd.model.run import (
    ActiveObjectSet,
    HookPhase,
    LifecycleKind,
    LifecycleObjectRef,
    NoPreviousStep,
    RunStage,
    RunStatus,
)
from pytest_bdd.model.scenario_run import (
    RunNode,
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


def runtime_object_id(obj: object) -> str:
    """
    Get runtime object ID.

    Args:
        obj: Object to get ID for.

    Returns:
        String representation of object ID.

    """
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


def runtime_object_name(obj: object) -> str | None:
    """
    Get runtime object name.

    Args:
        obj: Object to get name for.

    Returns:
        Name string or None.

    """
    if obj is None:
        return Nothing.value_or(None)
    name = getattr(obj, "name", None)
    return str(name) if name is not None else None


def build_lifecycle_ref(kind: LifecycleKind, value: object, *, is_active: bool) -> LifecycleObjectRef | None:
    """
    Build a lifecycle reference.

    Args:
        kind: Lifecycle kind.
        value: Object to reference.
        is_active: Whether the object is active.

    Returns:
        LifecycleObjectRef or None.

    """
    if value is None:
        return Nothing.value_or(None)
    return LifecycleObjectRef(
        kind=kind,
        object_id=runtime_object_id(value),
        name=runtime_object_name(value),
        source=value.__class__.__name__,
        is_active=is_active,
    )


def _inactive_ref(kind: LifecycleKind, *, reason: str, fail_fast_code: str | None = None) -> LifecycleObjectRef:
    return LifecycleObjectRef.inactive(kind, reason=reason, fail_fast_code=fail_fast_code)


def _resolve_lifecycle_ref(
    kind: LifecycleKind,
    value: object | None,
    *,
    is_active: bool,
    inactive_reason: str,
    fail_fast_code: str | None = None,
) -> LifecycleObjectRef:
    if value is None:
        return _inactive_ref(kind, reason=inactive_reason, fail_fast_code=fail_fast_code)
    lifecycle_ref = build_lifecycle_ref(kind, value, is_active=is_active)
    if lifecycle_ref is not None:
        return lifecycle_ref
    return _inactive_ref(kind, reason=inactive_reason, fail_fast_code=fail_fast_code)


def _resolve_transition_refs(  # noqa: PLR0913
    scenario_run: ScenarioRun,
    *,
    hook_phase: HookPhase,
    gherkin_document: GherkinDocument | None,
    pickle: object | None,
    step: object | None,
    previous_step: object | None,
) -> tuple[LifecycleObjectRef, LifecycleObjectRef, LifecycleObjectRef, LifecycleObjectRef, LifecycleObjectRef]:
    run_ref = scenario_run.run_ref
    if scenario_run.run is not None:
        run_ref = _resolve_lifecycle_ref("run", scenario_run.run, is_active=True, inactive_reason="idle")

    scenario_is_active = hook_phase not in {HookPhase.after_scenario, HookPhase.step_error, HookPhase.step_lookup_error}
    feature_is_active = scenario_is_active
    step_is_active = (
        hook_phase is HookPhase.run_step
        or hook_phase is HookPhase.before_step
        or hook_phase is HookPhase.before_step_call
    )

    feature_ref = _resolve_lifecycle_ref(
        "feature",
        gherkin_document,
        is_active=feature_is_active,
        inactive_reason="idle" if not feature_is_active else "unresolved_external",
    )
    scenario_ref = _resolve_lifecycle_ref(
        "scenario",
        pickle,
        is_active=scenario_is_active,
        inactive_reason="idle" if not scenario_is_active else "unresolved_external",
    )

    if hook_phase is HookPhase.after_scenario:
        step_ref = _inactive_ref("step", reason="finished", fail_fast_code="object_inactive")
        previous_step_ref = _inactive_ref("step", reason="finished")
    else:
        step_ref = _resolve_lifecycle_ref(
            "step",
            step,
            is_active=step_is_active,
            inactive_reason="idle",
            fail_fast_code="object_inactive",
        )
        previous_step_ref = _resolve_lifecycle_ref(
            "step",
            previous_step,
            is_active=previous_step is not None,
            inactive_reason="no_previous_step",
        )
    return run_ref, feature_ref, scenario_ref, step_ref, previous_step_ref


def _sync_step_node(
    scenario_run: ScenarioRun,
    *,
    step_ref: LifecycleObjectRef,
    step_is_active: bool,
) -> None:
    if step_ref.is_active and step_is_active:
        parent_id = scenario_run.scenario_node.id if scenario_run.scenario_node is not None else scenario_run.id
        scenario_run.step_node = RunNode(
            id=f"step-{step_ref.object_id}-{scenario_run.transition_index + 1}",
            parent_id=parent_id,
            kind="step",
            object_ref=step_ref,
            is_active=True,
            opened_at_transition=scenario_run.transition_index + 1,
        )
        return
    scenario_run.step_node = None


def _finalize_after_scenario(scenario_run: ScenarioRun, *, run_ref: LifecycleObjectRef) -> None:
    if scenario_run.scenario_node is not None:
        scenario_run.scenario_node.close(scenario_run.transition_index)
    if scenario_run.feature_node is not None:
        scenario_run.feature_node.close(scenario_run.transition_index)

    scenario_run.stage = RunStage.finished
    scenario_run.step_object = None
    scenario_run.previous_step_object = NoPreviousStep()
    scenario_run.set_active_set(
        ActiveObjectSet(
            run=run_ref,
            feature=_inactive_ref("feature", reason="finished"),
            scenario=_inactive_ref("scenario", reason="finished"),
            step=_inactive_ref("step", reason="finished", fail_fast_code="object_inactive"),
            previous_step=_inactive_ref("step", reason="finished"),
            captured_at_stage=RunStage.finished,
        ),
    )


def initial_scenario_run_id(request: FixtureRequest) -> str:
    """
    Get initial scenario run ID.

    Returns:
        Initial scenario run ID string.

    """
    node_id = getattr(getattr(request, "node", None), "nodeid", None)
    key = node_id or f"unknown-{next(_context_index)}"
    return f"ctx-{key}-{next(_context_index)}"


def apply_transition(  # noqa: PLR0913
    scenario_run: ScenarioRun,
    *,
    hook_phase: HookPhase,
    gherkin_document: GherkinDocument | None = None,
    pickle: object | None = None,
    step: object | None = None,
    previous_step: object | None = None,
    status: RunStatus | None = None,
) -> ScenarioRun:
    """
    Apply transition to scenario run.

    Returns:
        Updated scenario run.

    """
    stage = PHASE_TO_STAGE[hook_phase]
    run = scenario_run.run
    run_ref, feature_ref, scenario_ref, step_ref, previous_step_ref = _resolve_transition_refs(
        scenario_run,
        hook_phase=hook_phase,
        gherkin_document=gherkin_document,
        pickle=pickle,
        step=step,
        previous_step=previous_step,
    )
    step_is_active = hook_phase in {HookPhase.run_step, HookPhase.before_step, HookPhase.before_step_call}

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
    scenario_run.previous_step_object = previous_step if previous_step is not None else NoPreviousStep()

    _sync_step_node(scenario_run, step_ref=step_ref, step_is_active=step_is_active)

    scenario_run.set_active_set(
        ActiveObjectSet(
            run=run_ref,
            feature=feature_ref,
            scenario=scenario_ref,
            step=step_ref,
            previous_step=previous_step_ref,
            captured_at_stage=stage,
        ),
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

    if hook_phase is HookPhase.after_scenario:
        _finalize_after_scenario(scenario_run, run_ref=run_ref)

    return scenario_run
