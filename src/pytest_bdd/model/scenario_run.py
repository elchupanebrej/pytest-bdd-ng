from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Literal

from pytest_bdd.compatibility.enum import StrEnum
from pytest_bdd.model.message_registry import EnvelopeRegistry

if TYPE_CHECKING:
    from pytest_bdd.model.message_extension import EventEnvelope

LifecycleKind = Literal["run", "feature", "scenario", "step"]
NodeKind = Literal["feature", "scenario", "step"]


class HookPhase(StrEnum):
    before_scenario = "pytest_bdd_before_scenario"
    run_scenario = "pytest_bdd_run_scenario"
    after_scenario = "pytest_bdd_after_scenario"
    run_step = "pytest_bdd_run_step"
    before_step = "pytest_bdd_before_step"
    before_step_call = "pytest_bdd_before_step_call"
    after_step = "pytest_bdd_after_step"
    step_error = "pytest_bdd_step_error"
    step_lookup_error = "pytest_bdd_step_lookup_error"


class RunStage(StrEnum):
    idle = "idle"
    scenario_setup = "scenario_setup"
    scenario_running = "scenario_running"
    step_running = "step_running"
    scenario_teardown = "scenario_teardown"
    finished = "finished"


class RunStatus(StrEnum):
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
    captured_at_stage: RunStage
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
    stage: RunStage
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
class Run:
    STASH_KEY = "_pytest_bdd_run"
    ENVELOPE_REGISTRY_STASH_KEY = "_pytest_bdd_envelope_registry"

    id: str
    run_ref: LifecycleObjectRef
    status: RunStatus
    transition_index: int = 0
    active_feature_id: str | None = None
    active_scenario_id: str | None = None
    active_step_id: str | None = None
    scenario_runs_by_request: dict[str, ScenarioRun] = field(default_factory=dict, repr=False)
    active_scenario_run: ScenarioRun | None = field(default=None, repr=False)
    last_error: ContextErrorState | None = None
    reporting_state: ReportingLifecycleState = field(default_factory=ReportingLifecycleState)

    def advance_transition(self) -> None:
        self.transition_index += 1

    @classmethod
    def from_pytest_stash(cls, config: Any) -> Run | None:
        stash = config.stash
        candidate = stash[cls.STASH_KEY] if cls.STASH_KEY in stash else None
        if isinstance(candidate, Run):
            return candidate
        return None

    def set_in_pytest_stash(self, config: Any) -> None:
        config.stash[self.STASH_KEY] = self

    @classmethod
    def envelope_registry_from_pytest_stash(cls, config: Any) -> EnvelopeRegistry | None:
        stash = config.stash
        candidate = stash[cls.ENVELOPE_REGISTRY_STASH_KEY] if cls.ENVELOPE_REGISTRY_STASH_KEY in stash else None
        if isinstance(candidate, EnvelopeRegistry):
            return candidate
        return None

    @classmethod
    def ensure_envelope_registry_in_pytest_stash(cls, config: Any) -> EnvelopeRegistry:
        existing = cls.envelope_registry_from_pytest_stash(config)
        if existing is not None:
            return existing
        stash = config.stash
        registry = EnvelopeRegistry()
        stash[cls.ENVELOPE_REGISTRY_STASH_KEY] = registry
        return registry

    @classmethod
    def register_envelope_in_pytest_stash(cls, config: Any, envelope: EventEnvelope) -> EnvelopeRegistry:
        registry = cls.ensure_envelope_registry_in_pytest_stash(config)
        registry.add_envelope(envelope)
        return registry

    @classmethod
    def ensure_for_session(cls, *, config: Any, session: Any) -> Run:
        cls.ensure_envelope_registry_in_pytest_stash(config)
        existing = cls.from_pytest_stash(config)
        if existing is not None:
            return existing

        object_id = (
            getattr(session, "name", None)
            or getattr(session, "nodeid", None)
            or str(id(session))
        )
        run_ref = LifecycleObjectRef(kind="run", object_id=str(object_id), name="run", is_active=True)
        run = Run(
            id=f"run-{id(session)}",
            run_ref=run_ref,
            status=RunStatus.ok,
            transition_index=0,
        )
        run.set_in_pytest_stash(config)
        return run

    @staticmethod
    def _request_key(request: Any) -> str:
        node = getattr(request, "node", None)
        node_id = getattr(node, "nodeid", None)
        if node_id is not None:
            return str(node_id)
        return f"request-{id(request)}"

    @classmethod
    def get_scenario_run(cls, request: Any) -> ScenarioRun | None:
        run = cls.from_pytest_stash(request.config)
        key = cls._request_key(request)
        if run is None:
            return None
        return run.scenario_runs_by_request.get(key)

    @classmethod
    def set_scenario_run(cls, request: Any, scenario_run: ScenarioRun) -> None:
        run = scenario_run.run
        if run is None:
            run = cls.ensure_for_session(config=request.config, session=request.session)
            scenario_run.run = run
        key = cls._request_key(request)
        run.scenario_runs_by_request[key] = scenario_run
        run.active_scenario_run = scenario_run

    @classmethod
    def pop_scenario_run(cls, request: Any) -> ScenarioRun | None:  # noqa: C901
        config = getattr(request, "config", None)
        run = cls.from_pytest_stash(config) if config is not None else None
        if run is None:
            return None
        key = cls._request_key(request)
        scenario_run = run.scenario_runs_by_request.pop(key, None)
        if scenario_run is None:
            return None

        run_root = scenario_run.run
        if run_root is not None:
            if scenario_run.step_node is not None:
                scenario_run.step_node.close(run_root.transition_index)
            if scenario_run.scenario_node is not None:
                scenario_run.scenario_node.close(run_root.transition_index)
            if scenario_run.feature_node is not None:
                scenario_run.feature_node.close(run_root.transition_index)

            if run_root.active_scenario_id == scenario_run.id:
                run_root.active_scenario_id = None
            if run_root.active_scenario_run is scenario_run:
                run_root.active_scenario_run = None
            if run_root.active_step_id is not None:
                run_root.active_step_id = None
            run_root.reporting_state.reset_scenario_scope()

        scenario_run.reference_resolver.clear()
        return scenario_run

    def create_scenario_run(
        self, request: Any, *, feature: Any | None = None, scenario: Any | None = None
    ) -> ScenarioRun:
        from pytest_bdd.plugin.pickle_runner.run_transitions import (  # noqa: PLC0415
            build_lifecycle_ref,
            initial_scenario_run_id,
            runtime_object_id,
        )

        run_ref = build_lifecycle_ref("run", request.session, is_active=True)
        if run_ref is None:
            run_ref = LifecycleObjectRef(kind="run", object_id="run", name="run", is_active=True)

        run = self

        feature_ref = build_lifecycle_ref("feature", feature, is_active=feature is not None)
        scenario_ref = build_lifecycle_ref("scenario", scenario, is_active=scenario is not None)
        active_set = ActiveObjectSet(
            run=run_ref,
            feature=feature_ref,
            scenario=scenario_ref,
            step=None,
            previous_step=None,
            captured_at_stage=RunStage.idle,
        )

        run_node_id = initial_scenario_run_id(request)
        feature_node = None
        if feature_ref is not None:
            feature_node = RunNode(
                id=f"feature-{runtime_object_id(feature)}-{run_node_id}",
                parent_id=run.id,
                kind="feature",
                object_ref=feature_ref,
                is_active=True,
                opened_at_transition=run.transition_index,
            )
            run.active_feature_id = feature_node.id

        scenario_node = None
        if scenario_ref is not None:
            scenario_node = RunNode(
                id=run_node_id,
                parent_id=feature_node.id if feature_node is not None else run.id,
                kind="scenario",
                object_ref=scenario_ref,
                is_active=True,
                opened_at_transition=run.transition_index,
            )
            run.active_scenario_id = scenario_node.id

        scenario_run = ScenarioRun(
            id=run_node_id,
            run_ref=run_ref,
            feature_ref=feature_ref,
            scenario_ref=scenario_ref,
            step_ref=None,
            previous_step_ref=None,
            active_hook=HookPhase.before_scenario,
            stage=RunStage.idle,
            status=RunStatus.ok,
            active_set=active_set,
            transition_index=0,
            run=run,
            feature_node=feature_node,
            scenario_node=scenario_node,
            step_node=None,
            feature_object=feature,
            scenario_object=scenario,
            step_object=None,
            previous_step_object=None,
        )
        key = type(self)._request_key(request)
        run.scenario_runs_by_request[key] = scenario_run
        run.active_scenario_run = scenario_run
        return scenario_run

    def as_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.id,
            "run_ref": self.run_ref.as_dict(),
            "status": self.status.value,
            "transition_index": self.transition_index,
            "active_feature_id": self.active_feature_id,
            "active_scenario_id": self.active_scenario_id,
            "active_step_id": self.active_step_id,
            "last_error": self.last_error.as_dict() if self.last_error is not None else None,
            "reporting_state": self.reporting_state.as_dict(),
        }


@dataclass(slots=True)
class RunNode:
    id: str
    parent_id: str
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
            "id": self.id,
            "parent_id": self.parent_id,
            "kind": self.kind,
            "object_ref": self.object_ref.as_dict(),
            "is_active": self.is_active,
            "opened_at_transition": self.opened_at_transition,
            "closed_at_transition": self.closed_at_transition,
        }


@dataclass(slots=True)
class ScenarioRun:
    id: str
    run_ref: LifecycleObjectRef
    active_hook: HookPhase
    stage: RunStage
    status: RunStatus
    active_set: ActiveObjectSet
    transition_index: int = 0
    feature_ref: LifecycleObjectRef | None = None
    scenario_ref: LifecycleObjectRef | None = None
    step_ref: LifecycleObjectRef | None = None
    previous_step_ref: LifecycleObjectRef | None = None
    last_error: ContextErrorState | None = None
    run: Run | None = None
    feature_node: RunNode | None = None
    scenario_node: RunNode | None = None
    step_node: RunNode | None = None
    feature_object: Any | None = None
    scenario_object: Any | None = None
    step_object: Any | None = None
    previous_step_object: Any | None = None
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
            "id": self.id,
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
            "run": self.run.as_dict() if self.run is not None else None,
            "feature_node": self.feature_node.as_dict() if self.feature_node is not None else None,
            "scenario_node": self.scenario_node.as_dict() if self.scenario_node is not None else None,
            "step_node": self.step_node.as_dict() if self.step_node is not None else None,
            "reference_resolver": self.reference_resolver.as_dict(),
        }


@dataclass(slots=True)
class HookInvocationContext:
    hook_name: str
    hook_phase: HookPhase
    scenario_run_ref: ScenarioRun
    request_ref: str
    resolved_objects: ActiveObjectSet

    def as_dict(self) -> dict[str, Any]:
        return {
            "hook_name": self.hook_name,
            "hook_phase": self.hook_phase.value,
            "scenario_run_ref": self.scenario_run_ref.as_dict(),
            "request_ref": self.request_ref,
            "resolved_objects": self.resolved_objects.as_dict(),
        }


@dataclass(slots=True)
class ReportingContextSnapshot:
    run_id: str
    active_set: ActiveObjectSet
    stage: RunStage
    resolved_from_hierarchy: bool
    fallback_reason: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
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
