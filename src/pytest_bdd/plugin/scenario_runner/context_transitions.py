from __future__ import annotations

from itertools import count
from typing import Any

from pytest_bdd.model.execution_context import (
    ActiveObjectSet,
    ExecutionContext,
    ExecutionContextNode,
    ExecutionStage,
    ExecutionStatus,
    HookPhase,
    LifecycleKind,
    LifecycleObjectRef,
)

_context_index = count(1)


PHASE_TO_STAGE: dict[HookPhase, ExecutionStage] = {
    HookPhase.before_scenario: ExecutionStage.scenario_setup,
    HookPhase.run_scenario: ExecutionStage.scenario_running,
    HookPhase.after_scenario: ExecutionStage.scenario_teardown,
    HookPhase.run_step: ExecutionStage.step_running,
    HookPhase.before_step: ExecutionStage.step_running,
    HookPhase.before_step_call: ExecutionStage.step_running,
    HookPhase.after_step: ExecutionStage.scenario_running,
    HookPhase.step_error: ExecutionStage.scenario_running,
    HookPhase.step_lookup_error: ExecutionStage.scenario_running,
}


def phase_from_hook_name(hook_name: str) -> HookPhase | None:
    normalized_name = hook_name.removeprefix("pytest_bdd_")
    try:
        return HookPhase(normalized_name)
    except ValueError:
        return None


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


def initial_execution_context_id(request: Any) -> str:
    node_id = getattr(getattr(request, "node", None), "nodeid", None)
    key = node_id or f"unknown-{next(_context_index)}"
    return f"ctx-{key}-{next(_context_index)}"


def build_active_object_set(
    *,
    stage: ExecutionStage,
    run_ref: LifecycleObjectRef,
    feature_ref: LifecycleObjectRef | None,
    scenario_ref: LifecycleObjectRef | None,
    step_ref: LifecycleObjectRef | None,
    previous_step_ref: LifecycleObjectRef | None,
) -> ActiveObjectSet:
    return ActiveObjectSet(
        run=run_ref,
        feature=feature_ref,
        scenario=scenario_ref,
        step=step_ref,
        previous_step=previous_step_ref,
        captured_at_stage=stage,
    )


def apply_transition(
    context: ExecutionContext,
    *,
    hook_phase: HookPhase,
    run: Any | None = None,
    feature: Any | None = None,
    scenario: Any | None = None,
    step: Any | None = None,
    previous_step: Any | None = None,
    status: ExecutionStatus | None = None,
) -> ExecutionContext:
    stage = PHASE_TO_STAGE[hook_phase]
    session_root = context.session_context

    run_ref = context.run_ref if run is None else build_lifecycle_ref("run", run, is_active=True)
    if run_ref is None:
        run_ref = context.run_ref

    scenario_is_active = stage not in {ExecutionStage.idle, ExecutionStage.finished}
    feature_is_active = scenario_is_active
    step_is_active = stage is ExecutionStage.step_running

    feature_ref = build_lifecycle_ref("feature", feature, is_active=feature_is_active) if feature is not None else None
    scenario_ref = (
        build_lifecycle_ref("scenario", scenario, is_active=scenario_is_active) if scenario is not None else None
    )

    if hook_phase is HookPhase.after_scenario:
        step_ref = None
        previous_step_ref = None
        context.step_node = None
    else:
        step_ref = build_lifecycle_ref("step", step, is_active=step_is_active) if step is not None else None
        previous_step_ref = (
            build_lifecycle_ref("step", previous_step, is_active=previous_step is not None)
            if previous_step is not None
            else None
        )
        if step_ref is not None and step_is_active:
            parent_context_id = (
                context.scenario_node.context_id if context.scenario_node is not None else context.context_id
            )
            context.step_node = ExecutionContextNode(
                context_id=f"step-{step_ref.object_id}-{context.transition_index + 1}",
                parent_context_id=parent_context_id,
                kind="step",
                object_ref=step_ref,
                is_active=True,
                opened_at_transition=context.transition_index + 1,
            )
        else:
            context.step_node = None

    context.active_hook = hook_phase
    context.stage = stage
    context.status = status or context.status
    if hook_phase in {HookPhase.step_error, HookPhase.step_lookup_error} and status is None:
        context.status = ExecutionStatus.failed

    context.feature_ref = feature_ref
    context.scenario_ref = scenario_ref
    context.step_ref = step_ref
    context.previous_step_ref = previous_step_ref
    context.feature_object = feature
    context.scenario_object = scenario
    context.step_object = step
    context.previous_step_object = previous_step

    context.set_active_set(
        build_active_object_set(
            stage=stage,
            run_ref=run_ref,
            feature_ref=feature_ref,
            scenario_ref=scenario_ref,
            step_ref=step_ref,
            previous_step_ref=previous_step_ref,
        )
    )
    context.advance_transition()
    if session_root is not None:
        session_root.advance_transition()
        session_root.status = context.status
        session_root.active_feature_context_id = (
            context.feature_node.context_id
            if context.feature_node is not None and context.feature_node.is_active
            else None
        )
        session_root.active_scenario_context_id = (
            context.scenario_node.context_id
            if context.scenario_node is not None and context.scenario_node.is_active
            else None
        )
        session_root.active_step_context_id = (
            context.step_node.context_id if context.step_node is not None and context.step_node.is_active else None
        )

    if hook_phase is HookPhase.after_scenario:
        if context.scenario_node is not None:
            context.scenario_node.close(context.transition_index)
        if context.feature_node is not None:
            context.feature_node.close(context.transition_index)

        context.stage = ExecutionStage.finished
        context.feature_object = None
        context.scenario_object = None
        context.step_object = None
        context.previous_step_object = None
        context.set_active_set(
            build_active_object_set(
                stage=ExecutionStage.finished,
                run_ref=run_ref,
                feature_ref=None,
                scenario_ref=None,
                step_ref=None,
                previous_step_ref=None,
            )
        )
        if session_root is not None:
            session_root.active_scenario_context_id = None
            session_root.active_step_context_id = None

    return context
