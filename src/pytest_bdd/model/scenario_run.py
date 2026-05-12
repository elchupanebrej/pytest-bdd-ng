"""Provide scenario runtime model helpers."""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from attrs import define, field
from returns.maybe import Nothing

from pytest_bdd.model.run import (
    ActiveObjectSet,
    ContextErrorState,
    HookPhase,
    LifecycleKind,
    LifecycleObjectRef,
    NodeKind,
    NoPreviousStep,
    ReferenceResolverState,
    RunStage,
    RunStatus,
    _finished_feature_ref,
    _finished_previous_step_ref,
    _finished_scenario_ref,
    _finished_step_ref,
    _inactive_feature_ref,
    _inactive_scenario_ref,
    _inactive_step_ref,
    _no_previous_step_ref,
)

if TYPE_CHECKING:
    from cucumber_messages import GherkinDocument, Pickle, PickleStep, Source

    from pytest_bdd.model.feature_binding import FeatureRuntimeBinding
    from pytest_bdd.model.run import Run
    from pytest_bdd.types.json import JSONObject


@define(slots=True)
class RunNode:
    """Track the lifecycle transitions of a specific execution node (feature, scenario, or step)."""

    id: str
    parent_id: str
    kind: NodeKind
    object_ref: LifecycleObjectRef
    is_active: bool
    opened_at_transition: int
    closed_at_transition: int | None = None

    def close(self, at_transition: int) -> None:
        """Mark the node as inactive and record the transition index at which it finished executing."""
        self.is_active = False
        self.closed_at_transition = at_transition

    def as_dict(self) -> JSONObject:
        """
        Serialize the run node state into a dictionary representation.

        Returns:
            A dictionary containing the node's properties and transition states.

        """
        return {
            "id": self.id,
            "parent_id": self.parent_id,
            "kind": self.kind,
            "object_ref": self.object_ref.as_dict(),
            "is_active": self.is_active,
            "opened_at_transition": self.opened_at_transition,
            "closed_at_transition": self.closed_at_transition,
        }


@define(slots=True)
class StepRun:
    """Capture the execution context, data, and outcomes associated with an individual step run."""

    step: PickleStep | None = None
    keyword: str | None = None
    text: str = ""
    parameters: dict[str, object] = field(factory=dict)
    status: RunStatus = RunStatus.ok
    duration: float | None = None
    attachments: list[object] = field(factory=list)
    doc_string: object | None = None
    data_table: object | None = None
    line_number: int | None = None


@define(slots=True)
class ScenarioRun:
    """Manage the active execution context, state tracking, and lifecycle for a specific scenario attempt."""

    id: str
    run_ref: LifecycleObjectRef
    active_hook: HookPhase
    stage: RunStage
    status: RunStatus
    active_set: ActiveObjectSet
    run: Run
    transition_index: int = 0
    feature_ref: LifecycleObjectRef = field(factory=_inactive_feature_ref)
    scenario_ref: LifecycleObjectRef = field(factory=_inactive_scenario_ref)
    step_ref: LifecycleObjectRef = field(factory=_inactive_step_ref)
    previous_step_ref: LifecycleObjectRef = field(factory=_no_previous_step_ref)
    last_error: ContextErrorState | None = None
    feature_uri: str | None = None
    feature_node: RunNode | None = None
    scenario_node: RunNode | None = None
    step_node: RunNode | None = None
    gherkin_document: GherkinDocument | None = None
    feature_source: Source | None = None
    pickle: Pickle | None = None
    step_object: PickleStep | None = None
    previous_step_object: PickleStep | NoPreviousStep = field(factory=NoPreviousStep)
    step_run: StepRun | None = None
    reference_resolver: ReferenceResolverState = field(factory=ReferenceResolverState)
    _active_kind_index: dict[LifecycleKind, LifecycleObjectRef] = field(init=False, repr=False)

    def __attrs_post_init__(self) -> None:
        """Initialize the internal lookup dictionary."""
        self._active_kind_index = {
            "run": self.active_set.run,
            "feature": self.active_set.feature,
            "scenario": self.active_set.scenario,
            "step": self.active_set.step,
        }

    def advance_transition(self) -> None:
        """Increment the internal transition index to reflect the scenario moving to a new execution state."""
        self.transition_index += 1

    def record_context_error(
        self,
        *,
        code: Literal["object_inactive", "transition_order_violation", "context_not_initialized", "binding_missing"],
        message: str,
        hook_name: str,
        requested_kind: LifecycleKind | None = None,
    ) -> ContextErrorState:
        """
        Record a context-related execution error, storing it in the scenario and parent run context.

        Returns:
            A ContextErrorState containing the specifics of the encountered context error.

        """
        error = ContextErrorState(
            code=code,
            message=message,
            hook_name=hook_name,
            stage=self.stage,
            requested_kind=requested_kind,
        )
        self.last_error = error
        self.run.last_error = error
        return error

    def set_active_set(self, active_set: ActiveObjectSet) -> None:
        """Handle set active set."""
        self.active_set = active_set
        self._active_kind_index = {
            "run": self.active_set.run,
            "feature": self.active_set.feature,
            "scenario": self.active_set.scenario,
            "step": self.active_set.step,
        }

    def get_active_object(self, kind: LifecycleKind) -> LifecycleObjectRef | None:
        """
        Retrieve the active object reference for a specified lifecycle kind.

        Returns:
            The LifecycleObjectRef if active, or None if the object is inactive or undefined.

        """
        candidate = self._active_kind_index.get(kind)
        if candidate is None or not candidate.is_active:
            return Nothing.value_or(None)
        return candidate

    def require_feature_binding(self, *, hook_name: str) -> FeatureRuntimeBinding:
        """
        Fetch the current feature binding, verifying its availability in the active context.

        Returns:
            The bound FeatureRuntimeBinding.

        Raises:
            RuntimeError: If the feature binding is missing or the context is not initialized.

        """
        binding = self.feature_binding
        if binding is not None:
            return binding
        error = self.record_context_error(
            code="binding_missing",
            message=f"Feature runtime binding is unavailable for {hook_name} at stage '{self.stage.value}'",
            hook_name=hook_name,
            requested_kind="feature",
        )
        raise RuntimeError(error.message)

    def require_gherkin_document(self, *, hook_name: str) -> GherkinDocument:
        """
        Fetch the active Gherkin document from the feature binding.

        Returns:
            The current GherkinDocument instance.

        Raises:
            RuntimeError: If the feature binding or document is missing.

        """
        binding = self.feature_binding
        if binding is not None:
            return binding.gherkin_document
        if self.gherkin_document is not None:
            return self.gherkin_document
        error = self.record_context_error(
            code="binding_missing",
            message=f"Feature object is unavailable for {hook_name} at stage '{self.stage.value}'",
            hook_name=hook_name,
            requested_kind="feature",
        )
        raise RuntimeError(error.message)

    def require_pickle(self, *, hook_name: str) -> Pickle:
        """
        Fetch the active Pickle instance associated with the scenario run.

        Returns:
            The currently active Pickle object.

        Raises:
            RuntimeError: If the pickle context is missing or not initialized.

        """
        if self.pickle is not None:
            return self.pickle
        error = self.record_context_error(
            code="context_not_initialized",
            message=f"Pickle object is unavailable for {hook_name} at stage '{self.stage.value}'",
            hook_name=hook_name,
            requested_kind="scenario",
        )
        raise RuntimeError(error.message)

    def require_step_object(self, *, hook_name: str) -> PickleStep:
        """
        Fetch the active PickleStep instance for the current step execution.

        Returns:
            The currently active PickleStep object.

        Raises:
            RuntimeError: If the step context is missing or not initialized.

        """
        if self.step_object is not None:
            return self.step_object
        error = self.record_context_error(
            code="context_not_initialized",
            message=f"Step object is unavailable for {hook_name} at stage '{self.stage.value}'",
            hook_name=hook_name,
            requested_kind="step",
        )
        raise RuntimeError(error.message)

    def ensure_finished_for_cleanup(self, *, at_transition: int) -> None:
        """Force the scenario run to a finished state during teardown or cleanup procedures."""
        if self.step_node is not None and self.step_node.is_active:
            self.step_node.close(at_transition)
        if self.scenario_node is not None and self.scenario_node.is_active:
            self.scenario_node.close(at_transition)
        if self.feature_node is not None and self.feature_node.is_active:
            self.feature_node.close(at_transition)

        self.feature_ref = _finished_feature_ref()
        self.scenario_ref = _finished_scenario_ref()
        self.step_ref = _finished_step_ref()
        self.previous_step_ref = _finished_previous_step_ref()
        self.step_object = None
        self.previous_step_object = NoPreviousStep()
        self.stage = RunStage.finished
        self.set_active_set(
            ActiveObjectSet(
                run=self.run_ref,
                feature=self.feature_ref,
                scenario=self.scenario_ref,
                step=self.step_ref,
                previous_step=self.previous_step_ref,
                captured_at_stage=RunStage.finished,
            ),
        )

    @property
    def feature_binding(self) -> FeatureRuntimeBinding | None:
        """Handle feature binding."""
        if self.feature_uri is not None:
            return self.run.feature_binding_for_uri(self.feature_uri)
        return self.run.feature_binding_for_document(self.gherkin_document)

    def as_dict(self) -> JSONObject:
        """
        Serialize the complete ScenarioRun state into a JSON-compatible dictionary format.

        Returns:
            A dictionary containing the scenario's IDs, nodes, references, and execution status.

        """
        return {
            "id": self.id,
            "run_ref": self.run_ref.as_dict(),
            "feature_ref": self.feature_ref.as_dict(),
            "scenario_ref": self.scenario_ref.as_dict(),
            "step_ref": self.step_ref.as_dict(),
            "previous_step_ref": self.previous_step_ref.as_dict(),
            "active_hook": self.active_hook.value,
            "stage": self.stage.value,
            "status": self.status.value,
            "active_set": self.active_set.as_dict(),
            "transition_index": self.transition_index,
            "feature_uri": self.feature_uri,
            "last_error": self.last_error.as_dict() if self.last_error is not None else None,
            "run": self.run.as_dict(),
            "feature_node": self.feature_node.as_dict() if self.feature_node is not None else None,
            "scenario_node": self.scenario_node.as_dict() if self.scenario_node is not None else None,
            "step_node": self.step_node.as_dict() if self.step_node is not None else None,
            "reference_resolver": self.reference_resolver.as_dict(),
        }
