from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

from pytest_bdd.compatibility.enum import StrEnum

LifecycleKind = Literal["run", "feature", "scenario", "step"]
NodeKind = Literal["feature", "scenario", "step"]


class HookPhase(StrEnum):
    before_scenario = "before_scenario"
    run_scenario = "run_scenario"
    after_scenario = "after_scenario"
    run_step = "run_step"
    before_step = "before_step"
    before_step_call = "before_step_call"
    after_step = "after_step"
    step_error = "step_error"
    step_lookup_error = "step_lookup_error"


class ExecutionStage(StrEnum):
    idle = "idle"
    scenario_setup = "scenario_setup"
    scenario_running = "scenario_running"
    step_running = "step_running"
    scenario_teardown = "scenario_teardown"
    finished = "finished"


class ExecutionStatus(StrEnum):
    ok = "ok"
    failed = "failed"
    interrupted = "interrupted"


@dataclass(slots=True)
class LifecycleObjectRef:
    kind: LifecycleKind
    object_id: str
    name: str | None = None
    source: str | None = None
    is_active: bool = True

    def as_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind,
            "object_id": self.object_id,
            "name": self.name,
            "source": self.source,
            "is_active": self.is_active,
        }


@dataclass(slots=True)
class ActiveObjectSet:
    run: LifecycleObjectRef
    captured_at_stage: ExecutionStage
    feature: LifecycleObjectRef | None = None
    scenario: LifecycleObjectRef | None = None
    step: LifecycleObjectRef | None = None
    previous_step: LifecycleObjectRef | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "run": self.run.as_dict(),
            "feature": self.feature.as_dict() if self.feature is not None else None,
            "scenario": self.scenario.as_dict() if self.scenario is not None else None,
            "step": self.step.as_dict() if self.step is not None else None,
            "previous_step": self.previous_step.as_dict() if self.previous_step is not None else None,
            "captured_at_stage": self.captured_at_stage.value,
        }


@dataclass(slots=True)
class ReportingLifecycleState:
    run_started_id: str | None = None
    test_run_hook_started_id: str | None = None
    active_test_case_id: str | None = None
    active_test_case_started_id: str | None = None
    active_test_step_id: str | None = None
    runtime_step_to_test_step_id: dict[int, str] = field(default_factory=dict)
    scenario_attempt_context: dict[str, str | int] | None = None
    step_started_timestamp: Any | None = None
    step_finished_timestamp: Any | None = None

    def reset_scenario_scope(self) -> None:
        self.active_test_case_id = None
        self.active_test_case_started_id = None
        self.active_test_step_id = None
        self.runtime_step_to_test_step_id.clear()
        self.scenario_attempt_context = None
        self.step_started_timestamp = None
        self.step_finished_timestamp = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "run_started_id": self.run_started_id,
            "test_run_hook_started_id": self.test_run_hook_started_id,
            "active_test_case_id": self.active_test_case_id,
            "active_test_case_started_id": self.active_test_case_started_id,
            "active_test_step_id": self.active_test_step_id,
            "runtime_step_to_test_step_id": dict(self.runtime_step_to_test_step_id),
            "scenario_attempt_context": self.scenario_attempt_context,
            "step_started_timestamp": self.step_started_timestamp,
            "step_finished_timestamp": self.step_finished_timestamp,
        }


@dataclass(slots=True)
class ReferenceResolverState:
    missing_reference_diagnostics: list[str] = field(default_factory=list)

    def add_missing_reference(self, message: str) -> None:
        self.missing_reference_diagnostics.append(message)

    def clear(self) -> None:
        self.missing_reference_diagnostics.clear()

    def as_dict(self) -> dict[str, Any]:
        return {
            "missing_reference_diagnostics": list(self.missing_reference_diagnostics),
        }


@dataclass(slots=True)
class ContextErrorState:
    code: Literal["object_inactive", "transition_order_violation", "context_not_initialized"]
    message: str
    hook_name: str
    stage: ExecutionStage
    requested_kind: LifecycleKind | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "message": self.message,
            "hook_name": self.hook_name,
            "stage": self.stage.value,
            "requested_kind": self.requested_kind,
        }


@dataclass(slots=True)
class SessionExecutionContext:
    session_context_id: str
    run_ref: LifecycleObjectRef
    status: ExecutionStatus
    transition_index: int = 0
    active_feature_context_id: str | None = None
    active_scenario_context_id: str | None = None
    active_step_context_id: str | None = None
    last_error: ContextErrorState | None = None
    reporting_state: ReportingLifecycleState = field(default_factory=ReportingLifecycleState)

    def advance_transition(self) -> None:
        self.transition_index += 1

    def as_dict(self) -> dict[str, Any]:
        return {
            "session_context_id": self.session_context_id,
            "run_ref": self.run_ref.as_dict(),
            "status": self.status.value,
            "transition_index": self.transition_index,
            "active_feature_context_id": self.active_feature_context_id,
            "active_scenario_context_id": self.active_scenario_context_id,
            "active_step_context_id": self.active_step_context_id,
            "last_error": self.last_error.as_dict() if self.last_error is not None else None,
            "reporting_state": self.reporting_state.as_dict(),
        }


@dataclass(slots=True)
class ExecutionContextNode:
    context_id: str
    parent_context_id: str
    kind: NodeKind
    object_ref: LifecycleObjectRef
    is_active: bool
    opened_at_transition: int
    closed_at_transition: int | None = None

    def close(self, at_transition: int) -> None:
        self.is_active = False
        self.closed_at_transition = at_transition

    def as_dict(self) -> dict[str, Any]:
        return {
            "context_id": self.context_id,
            "parent_context_id": self.parent_context_id,
            "kind": self.kind,
            "object_ref": self.object_ref.as_dict(),
            "is_active": self.is_active,
            "opened_at_transition": self.opened_at_transition,
            "closed_at_transition": self.closed_at_transition,
        }


@dataclass(slots=True)
class ExecutionContext:
    context_id: str
    run_ref: LifecycleObjectRef
    active_hook: HookPhase
    stage: ExecutionStage
    status: ExecutionStatus
    active_set: ActiveObjectSet
    transition_index: int = 0
    feature_ref: LifecycleObjectRef | None = None
    scenario_ref: LifecycleObjectRef | None = None
    step_ref: LifecycleObjectRef | None = None
    previous_step_ref: LifecycleObjectRef | None = None
    last_error: ContextErrorState | None = None
    session_context: SessionExecutionContext | None = None
    feature_node: ExecutionContextNode | None = None
    scenario_node: ExecutionContextNode | None = None
    step_node: ExecutionContextNode | None = None
    feature_object: Any | None = None
    scenario_object: Any | None = None
    step_object: Any | None = None
    previous_step_object: Any | None = None
    reporting_state: ReportingLifecycleState = field(default_factory=ReportingLifecycleState)
    reference_resolver: ReferenceResolverState = field(default_factory=ReferenceResolverState)
    _active_kind_index: dict[LifecycleKind, LifecycleObjectRef | None] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self._active_kind_index = {
            "run": self.active_set.run,
            "feature": self.active_set.feature,
            "scenario": self.active_set.scenario,
            "step": self.active_set.step,
        }

    def advance_transition(self) -> None:
        self.transition_index += 1

    def set_active_set(self, active_set: ActiveObjectSet) -> None:
        self.active_set = active_set
        self._active_kind_index = {
            "run": self.active_set.run,
            "feature": self.active_set.feature,
            "scenario": self.active_set.scenario,
            "step": self.active_set.step,
        }

    def get_active_object(self, kind: LifecycleKind) -> LifecycleObjectRef | None:
        candidate = self._active_kind_index.get(kind)
        if candidate is None:
            return None
        if not candidate.is_active:
            return None
        return candidate

    def as_dict(self) -> dict[str, Any]:
        return {
            "context_id": self.context_id,
            "run_ref": self.run_ref.as_dict(),
            "feature_ref": self.feature_ref.as_dict() if self.feature_ref is not None else None,
            "scenario_ref": self.scenario_ref.as_dict() if self.scenario_ref is not None else None,
            "step_ref": self.step_ref.as_dict() if self.step_ref is not None else None,
            "previous_step_ref": self.previous_step_ref.as_dict() if self.previous_step_ref is not None else None,
            "active_hook": self.active_hook.value,
            "stage": self.stage.value,
            "status": self.status.value,
            "active_set": self.active_set.as_dict(),
            "transition_index": self.transition_index,
            "last_error": self.last_error.as_dict() if self.last_error is not None else None,
            "session_context": self.session_context.as_dict() if self.session_context is not None else None,
            "feature_node": self.feature_node.as_dict() if self.feature_node is not None else None,
            "scenario_node": self.scenario_node.as_dict() if self.scenario_node is not None else None,
            "step_node": self.step_node.as_dict() if self.step_node is not None else None,
            "reporting_state": self.reporting_state.as_dict(),
            "reference_resolver": self.reference_resolver.as_dict(),
        }


@dataclass(slots=True)
class HookInvocationContext:
    hook_name: str
    hook_phase: HookPhase
    execution_context_ref: ExecutionContext
    request_ref: str
    resolved_objects: ActiveObjectSet

    def as_dict(self) -> dict[str, Any]:
        return {
            "hook_name": self.hook_name,
            "hook_phase": self.hook_phase.value,
            "execution_context_ref": self.execution_context_ref.as_dict(),
            "request_ref": self.request_ref,
            "resolved_objects": self.resolved_objects.as_dict(),
        }


@dataclass(slots=True)
class ReportingContextSnapshot:
    session_context_id: str
    active_set: ActiveObjectSet
    stage: ExecutionStage
    resolved_from_hierarchy: bool
    fallback_reason: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "session_context_id": self.session_context_id,
            "active_set": self.active_set.as_dict(),
            "stage": self.stage.value,
            "resolved_from_hierarchy": self.resolved_from_hierarchy,
            "fallback_reason": self.fallback_reason,
        }


@dataclass(slots=True)
class ExternalApiCompatibilityRecord:
    api_surface_id: str
    baseline_reference: str
    changed_symbols: list[str]
    removed_symbols: list[str]
    renamed_symbols: list[str]
    additive_symbols: list[str]
    consumer_migration_required: bool

    def as_dict(self) -> dict[str, Any]:
        return {
            "api_surface_id": self.api_surface_id,
            "baseline_reference": self.baseline_reference,
            "changed_symbols": self.changed_symbols,
            "removed_symbols": self.removed_symbols,
            "renamed_symbols": self.renamed_symbols,
            "additive_symbols": self.additive_symbols,
            "consumer_migration_required": self.consumer_migration_required,
        }
