"""
Provide scenario runtime model helpers.

Responsibility:
    Provide scenario runtime model helpers. It directly owns the observable contract, local decisions, and maintenance
    boundary for this module.

Reason for existence:
    This entity is the information expert for `pytest_bdd.model.scenario_run` because it keeps the nearest code, data
    shape, call signature, and failure knowledge together.

Delegates:
    - RunNode: owns nested behavior below this boundary
    - StepRun: owns nested behavior below this boundary
    - ScenarioRun: owns nested behavior below this boundary

Cohesion:
    The implementation stays together because its imports, calls, state writes, and return contract describe one
    maintainable decision unit.

Separation:
    - module peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
      widening caller knowledge.

Main consumers:
    - src/pytest_bdd/model/run/lifecycle/_run.py: imports or references `scenario_run`
    - src/pytest_bdd/model/run_access.py: imports or references `scenario_run`
    - src/pytest_bdd/plugin/code_generator/collection.py: imports or references `scenario_run`
    - src/pytest_bdd/plugin/debug_mcp/bdd_adapter.py: imports or references `scenario_run`
    - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_core.py: imports or references `scenario_run`

State and side effects:
    mutates error, id, status, self._active_kind_index, binding; depends on __future__.annotations,
    typing.TYPE_CHECKING, typing.Literal, attrs.define, attrs.field.

Invariants:
    - `pytest_bdd.model.scenario_run` keeps its documented import path, ownership boundary, and observable behavior
      stable for callers.

Failure semantics:
    Raises or re-raises RuntimeError; callers must treat these as boundary failures.

Architecture score:
    #arch-eval:reason_for_existence=4
    #arch-eval:owned_responsibility=4
    #arch-eval:delegation_boundary=4
    #arch-eval:cohesion=3
    #arch-eval:separation=3
    #arch-eval:consumer_clarity=4
    #arch-eval:state_invariants=4
    #arch-eval:entity_fullness=4
    #arch-eval:locational_stability=4
"""

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
    """
    Track the lifecycle transitions of a specific execution node (feature, scenario, or step).

    Responsibility:
        Track the lifecycle transitions of a specific execution node (feature, scenario, or step). It directly owns the
        observable contract, local decisions, and maintenance boundary for this class.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.model.scenario_run.RunNode` because it keeps the nearest
        code, data shape, call signature, and failure knowledge together.

    Delegates:
        - close: owns nested behavior below this boundary
        - as_dict: owns nested behavior below this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/model/__init__.py: imports or references `RunNode`
        - src/pytest_bdd/model/run/lifecycle/_run.py: imports or references `RunNode`
        - src/pytest_bdd/model/run_access.py: imports or references `RunNode`
        - src/pytest_bdd/plugin/code_generator/collection.py: imports or references `RunNode`
        - src/pytest_bdd/plugin/pickle_runner/plugin/_executor.py: imports or references `RunNode`

    State and side effects:
        mutates id, parent_id, kind, object_ref, is_active.

    Invariants:
        - `pytest_bdd.model.scenario_run.RunNode` keeps its documented import path, ownership boundary, and observable
          behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=3
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=4
    """

    id: str
    parent_id: str
    kind: NodeKind
    object_ref: LifecycleObjectRef
    is_active: bool
    opened_at_transition: int
    closed_at_transition: int | None = None

    def close(self, at_transition: int) -> None:
        """
        Mark the node as inactive and record the transition index at which it finished executing.

        Responsibility:
            Mark the node as inactive and record the transition index at which it finished executing. It directly owns
            the observable contract, local decisions, and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.model.scenario_run.RunNode.close` because it keeps the
            nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - None, leaf-level implementation boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/model/run/lifecycle/_run.py: imports or references `close`
            - src/pytest_bdd/model/run_access.py: imports or references `close`
            - src/pytest_bdd/plugin/code_generator/collection.py: imports or references `close`
            - src/pytest_bdd/plugin/gherkin_message_reporter/entrypoint.py: imports or references `close`
            - src/pytest_bdd/plugin/gherkin_message_reporter/live_formatter_process.py: imports or references `close`

        State and side effects:
            mutates self.is_active, self.closed_at_transition.

        Invariants:
            - `pytest_bdd.model.scenario_run.RunNode.close` keeps its documented import path, ownership boundary, and
              observable behavior stable for callers.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=2
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=4
        """
        self.is_active = False
        self.closed_at_transition = at_transition

    def as_dict(self) -> JSONObject:
        """
        Serialize the run node state into a dictionary representation.

        Returns:
            A dictionary containing the node's properties and transition states.

        Responsibility:
            Serialize the run node state into a dictionary representation. It directly owns the observable contract,
            local decisions, and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.model.scenario_run.RunNode.as_dict` because it keeps
            the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - self.object_ref.as_dict: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/model/message_transport.py: imports or references `as_dict`
            - src/pytest_bdd/model/run/lifecycle/_run.py: imports or references `as_dict`
            - src/pytest_bdd/model/run/lifecycle/_snapshots.py: imports or references `as_dict`
            - src/pytest_bdd/model/run/lifecycle/_states.py: imports or references `as_dict`
            - src/pytest_bdd/model/run_access.py: imports or references `as_dict`

        State and side effects:
            keeps no local persistent state beyond call-local values.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=3
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=4

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
    """
    Capture the execution context, data, and outcomes associated with an individual step run.

    Responsibility:
        Capture the execution context, data, and outcomes associated with an individual step run. It directly owns the
        observable contract, local decisions, and maintenance boundary for this class.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.model.scenario_run.StepRun` because it keeps the nearest
        code, data shape, call signature, and failure knowledge together.

    Delegates:
        - field: collaborator call used by this boundary
        - define: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/model/__init__.py: imports or references `StepRun`
        - src/pytest_bdd/model/run/lifecycle/_run.py: imports or references `StepRun`
        - src/pytest_bdd/model/run_access.py: imports or references `StepRun`
        - src/pytest_bdd/plugin/code_generator/collection.py: imports or references `StepRun`
        - src/pytest_bdd/plugin/pickle_runner/plugin/_executor.py: imports or references `StepRun`

    State and side effects:
        mutates step, keyword, text, parameters, status.

    Invariants:
        - `pytest_bdd.model.scenario_run.StepRun` keeps its documented import path, ownership boundary, and observable
          behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=3
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=2
        #arch-eval:locational_stability=4
    """

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
    """
    Manage the active execution context, state tracking, and lifecycle for a specific scenario attempt.

    Responsibility:
        Manage the active execution context, state tracking, and lifecycle for a specific scenario attempt. It directly
        owns the observable contract, local decisions, and maintenance boundary for this class.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.model.scenario_run.ScenarioRun` because it keeps the
        nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - __attrs_post_init__: owns nested behavior below this boundary
        - advance_transition: owns nested behavior below this boundary
        - record_context_error: owns nested behavior below this boundary
        - set_active_set: owns nested behavior below this boundary
        - get_active_object: owns nested behavior below this boundary
        - require_feature_binding: owns nested behavior below this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/model/__init__.py: imports or references `ScenarioRun`
        - src/pytest_bdd/model/run/lifecycle/_run.py: imports or references `ScenarioRun`
        - src/pytest_bdd/model/run_access.py: imports or references `ScenarioRun`
        - src/pytest_bdd/plugin/code_generator/collection.py: imports or references `ScenarioRun`
        - src/pytest_bdd/plugin/pickle_runner/plugin/_executor.py: imports or references `ScenarioRun`

    State and side effects:
        mutates error, self._active_kind_index, binding, id, run_ref.

    Invariants:
        - `pytest_bdd.model.scenario_run.ScenarioRun` keeps its documented import path, ownership boundary, and
          observable behavior stable for callers.

    Failure semantics:
        Raises or re-raises RuntimeError; callers must treat these as boundary failures.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=3
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=4
    """

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
        """
        Initialize the internal lookup dictionary.

        Responsibility:
            Initialize the internal lookup dictionary. It directly owns the observable contract, local decisions, and
            maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.model.scenario_run.ScenarioRun.__attrs_post_init__`
            because it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - None, leaf-level implementation boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/model/run/lifecycle/_run.py: imports or references `__attrs_post_init__`
            - src/pytest_bdd/model/run_access.py: imports or references `__attrs_post_init__`
            - src/pytest_bdd/plugin/code_generator/collection.py: imports or references `__attrs_post_init__`
            - src/pytest_bdd/plugin/pickle_runner/plugin/_executor.py: imports or references `__attrs_post_init__`
            - src/pytest_bdd/plugin/pickle_runner/plugin/_plugin.py: imports or references `__attrs_post_init__`

        State and side effects:
            mutates self._active_kind_index.

        Invariants:
            - `pytest_bdd.model.scenario_run.ScenarioRun.__attrs_post_init__` keeps its documented import path,
              ownership boundary, and observable behavior stable for callers.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=2
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=4
        """
        self._active_kind_index = {
            "run": self.active_set.run,
            "feature": self.active_set.feature,
            "scenario": self.active_set.scenario,
            "step": self.active_set.step,
        }

    def advance_transition(self) -> None:
        """
        Increment the internal transition index to reflect the scenario moving to a new execution state.

        Responsibility:
            Increment the internal transition index to reflect the scenario moving to a new execution state. It directly
            owns the observable contract, local decisions, and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.model.scenario_run.ScenarioRun.advance_transition`
            because it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - None, leaf-level implementation boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/model/run/lifecycle/_run.py: imports or references `advance_transition`
            - src/pytest_bdd/model/run_access.py: imports or references `advance_transition`
            - src/pytest_bdd/plugin/code_generator/collection.py: imports or references `advance_transition`
            - src/pytest_bdd/plugin/pickle_runner/plugin/_executor.py: imports or references `advance_transition`
            - src/pytest_bdd/plugin/pickle_runner/plugin/_plugin.py: imports or references `advance_transition`

        State and side effects:
            mutates self.transition_index.

        Invariants:
            - `pytest_bdd.model.scenario_run.ScenarioRun.advance_transition` keeps its documented import path, ownership
              boundary, and observable behavior stable for callers.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=2
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=4
        """
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

        Responsibility:
            Record a context-related execution error, storing it in the scenario and parent run context. It directly
            owns the observable contract, local decisions, and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.model.scenario_run.ScenarioRun.record_context_error`
            because it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - ContextErrorState: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/model/run/lifecycle/_run.py: imports or references `record_context_error`
            - src/pytest_bdd/model/run_access.py: imports or references `record_context_error`
            - src/pytest_bdd/plugin/code_generator/collection.py: imports or references `record_context_error`
            - src/pytest_bdd/plugin/pickle_runner/plugin/_executor.py: imports or references `record_context_error`
            - src/pytest_bdd/plugin/pickle_runner/plugin/_plugin.py: imports or references `record_context_error`

        State and side effects:
            mutates error, self.last_error, self.run.last_error.

        Invariants:
            - `pytest_bdd.model.scenario_run.ScenarioRun.record_context_error` keeps its documented import path,
              ownership boundary, and observable behavior stable for callers.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=4

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
        """
        Handle set active set.

        Responsibility:
            Handle set active set. It directly owns the observable contract, local decisions, and maintenance boundary
            for this method. That boundary is intentionally stated in prose so maintainers can distinguish owned work
            from collaborators before editing.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.model.scenario_run.ScenarioRun.set_active_set` because
            it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - None, leaf-level implementation boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/model/run/lifecycle/_run.py: imports or references `set_active_set`
            - src/pytest_bdd/model/run_access.py: imports or references `set_active_set`
            - src/pytest_bdd/plugin/code_generator/collection.py: imports or references `set_active_set`
            - src/pytest_bdd/plugin/pickle_runner/plugin/_executor.py: imports or references `set_active_set`
            - src/pytest_bdd/plugin/pickle_runner/plugin/_plugin.py: imports or references `set_active_set`

        State and side effects:
            mutates self.active_set, self._active_kind_index.

        Invariants:
            - `pytest_bdd.model.scenario_run.ScenarioRun.set_active_set` keeps its documented import path, ownership
              boundary, and observable behavior stable for callers.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=2
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=4
        """
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

        Responsibility:
            Retrieve the active object reference for a specified lifecycle kind. It directly owns the observable
            contract, local decisions, and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.model.scenario_run.ScenarioRun.get_active_object`
            because it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - self._active_kind_index.get: collaborator call used by this boundary
            - Nothing.value_or: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/model/run/lifecycle/_run.py: imports or references `get_active_object`
            - src/pytest_bdd/model/run_access.py: imports or references `get_active_object`
            - src/pytest_bdd/plugin/code_generator/collection.py: imports or references `get_active_object`
            - src/pytest_bdd/plugin/pickle_runner/plugin/_executor.py: imports or references `get_active_object`
            - src/pytest_bdd/plugin/pickle_runner/plugin/_plugin.py: imports or references `get_active_object`

        State and side effects:
            mutates candidate.

        Invariants:
            - `pytest_bdd.model.scenario_run.ScenarioRun.get_active_object` keeps its documented import path, ownership
              boundary, and observable behavior stable for callers.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=4

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

        Responsibility:
            Fetch the current feature binding, verifying its availability in the active context. It directly owns the
            observable contract, local decisions, and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.model.scenario_run.ScenarioRun.require_feature_binding` because it keeps the nearest code, data
            shape, call signature, and failure knowledge together.

        Delegates:
            - self.record_context_error: collaborator call used by this boundary
            - RuntimeError: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/model/run/lifecycle/_run.py: imports or references `require_feature_binding`
            - src/pytest_bdd/model/run_access.py: imports or references `require_feature_binding`
            - src/pytest_bdd/plugin/code_generator/collection.py: imports or references `require_feature_binding`
            - src/pytest_bdd/plugin/pickle_runner/plugin/_executor.py: imports or references `require_feature_binding`
            - src/pytest_bdd/plugin/pickle_runner/plugin/_plugin.py: imports or references `require_feature_binding`

        State and side effects:
            mutates binding, error.

        Invariants:
            - `pytest_bdd.model.scenario_run.ScenarioRun.require_feature_binding` keeps its documented import path,
              ownership boundary, and observable behavior stable for callers.

        Failure semantics:
            Raises or re-raises RuntimeError; callers must treat these as boundary failures.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=4

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

        Responsibility:
            Fetch the active Gherkin document from the feature binding. It directly owns the observable contract, local
            decisions, and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.model.scenario_run.ScenarioRun.require_gherkin_document` because it keeps the nearest code, data
            shape, call signature, and failure knowledge together.

        Delegates:
            - self.record_context_error: collaborator call used by this boundary
            - RuntimeError: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/model/run/lifecycle/_run.py: imports or references `require_gherkin_document`
            - src/pytest_bdd/model/run_access.py: imports or references `require_gherkin_document`
            - src/pytest_bdd/plugin/code_generator/collection.py: imports or references `require_gherkin_document`
            - src/pytest_bdd/plugin/pickle_runner/plugin/_executor.py: imports or references `require_gherkin_document`
            - src/pytest_bdd/plugin/pickle_runner/plugin/_plugin.py: imports or references `require_gherkin_document`

        State and side effects:
            mutates binding, error.

        Invariants:
            - `pytest_bdd.model.scenario_run.ScenarioRun.require_gherkin_document` keeps its documented import path,
              ownership boundary, and observable behavior stable for callers.

        Failure semantics:
            Raises or re-raises RuntimeError; callers must treat these as boundary failures.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=4

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

        Responsibility:
            Fetch the active Pickle instance associated with the scenario run. It directly owns the observable contract,
            local decisions, and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.model.scenario_run.ScenarioRun.require_pickle` because
            it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - self.record_context_error: collaborator call used by this boundary
            - RuntimeError: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/model/run/lifecycle/_run.py: imports or references `require_pickle`
            - src/pytest_bdd/model/run_access.py: imports or references `require_pickle`
            - src/pytest_bdd/plugin/code_generator/collection.py: imports or references `require_pickle`
            - src/pytest_bdd/plugin/pickle_runner/plugin/_executor.py: imports or references `require_pickle`
            - src/pytest_bdd/plugin/pickle_runner/plugin/_plugin.py: imports or references `require_pickle`

        State and side effects:
            mutates error.

        Invariants:
            - `pytest_bdd.model.scenario_run.ScenarioRun.require_pickle` keeps its documented import path, ownership
              boundary, and observable behavior stable for callers.

        Failure semantics:
            Raises or re-raises RuntimeError; callers must treat these as boundary failures.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=4

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

        Responsibility:
            Fetch the active PickleStep instance for the current step execution. It directly owns the observable
            contract, local decisions, and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.model.scenario_run.ScenarioRun.require_step_object`
            because it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - self.record_context_error: collaborator call used by this boundary
            - RuntimeError: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/model/run/lifecycle/_run.py: imports or references `require_step_object`
            - src/pytest_bdd/model/run_access.py: imports or references `require_step_object`
            - src/pytest_bdd/plugin/code_generator/collection.py: imports or references `require_step_object`
            - src/pytest_bdd/plugin/gherkin_message_reporter/scenario_runtime.py: imports or references
              `require_step_object`
            - src/pytest_bdd/plugin/pickle_runner/plugin/_executor.py: imports or references `require_step_object`

        State and side effects:
            mutates error.

        Invariants:
            - `pytest_bdd.model.scenario_run.ScenarioRun.require_step_object` keeps its documented import path,
              ownership boundary, and observable behavior stable for callers.

        Failure semantics:
            Raises or re-raises RuntimeError; callers must treat these as boundary failures.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=4

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
        """
        Force the scenario run to a finished state during teardown or cleanup procedures.

        Responsibility:
            Force the scenario run to a finished state during teardown or cleanup procedures. It directly owns the
            observable contract, local decisions, and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.model.scenario_run.ScenarioRun.ensure_finished_for_cleanup` because it keeps the nearest code,
            data shape, call signature, and failure knowledge together.

        Delegates:
            - self.step_node.close: collaborator call used by this boundary
            - self.scenario_node.close: collaborator call used by this boundary
            - self.feature_node.close: collaborator call used by this boundary
            - _finished_feature_ref: collaborator call used by this boundary
            - _finished_scenario_ref: collaborator call used by this boundary
            - _finished_step_ref: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/model/run/lifecycle/_run.py: imports or references `ensure_finished_for_cleanup`
            - src/pytest_bdd/model/run_access.py: imports or references `ensure_finished_for_cleanup`
            - src/pytest_bdd/plugin/code_generator/collection.py: imports or references `ensure_finished_for_cleanup`
            - src/pytest_bdd/plugin/pickle_runner/plugin/_executor.py: imports or references
              `ensure_finished_for_cleanup`
            - src/pytest_bdd/plugin/pickle_runner/plugin/_plugin.py: imports or references `ensure_finished_for_cleanup`

        State and side effects:
            mutates self.feature_ref, self.scenario_ref, self.step_ref, self.previous_step_ref, self.step_object.

        Invariants:
            - `pytest_bdd.model.scenario_run.ScenarioRun.ensure_finished_for_cleanup` keeps its documented import path,
              ownership boundary, and observable behavior stable for callers.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=4
        """
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
        """
        Handle feature binding.

        Responsibility:
            Handle feature binding. It directly owns the observable contract, local decisions, and maintenance boundary
            for this method. That boundary is intentionally stated in prose so maintainers can distinguish owned work
            from collaborators before editing.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.model.scenario_run.ScenarioRun.feature_binding`
            because it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - self.run.feature_binding_for_uri: collaborator call used by this boundary
            - self.run.feature_binding_for_document: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/model/run/lifecycle/_run.py: imports or references `feature_binding`
            - src/pytest_bdd/model/run_access.py: imports or references `feature_binding`
            - src/pytest_bdd/model/scenario_report.py: imports or references `feature_binding`
            - src/pytest_bdd/plugin/code_generator/collection.py: imports or references `feature_binding`
            - src/pytest_bdd/plugin/pickle_runner/plugin/_executor.py: imports or references `feature_binding`

        State and side effects:
            keeps no local persistent state beyond call-local values.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=3
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=4
        """
        if self.feature_uri is not None:
            return self.run.feature_binding_for_uri(self.feature_uri)
        return self.run.feature_binding_for_document(self.gherkin_document)

    def as_dict(self) -> JSONObject:
        """
        Serialize the complete ScenarioRun state into a JSON-compatible dictionary format.

        Returns:
            A dictionary containing the scenario's IDs, nodes, references, and execution status.

        Responsibility:
            Serialize the complete ScenarioRun state into a JSON-compatible dictionary format. It directly owns the
            observable contract, local decisions, and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.model.scenario_run.ScenarioRun.as_dict` because it
            keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - self.run_ref.as_dict: collaborator call used by this boundary
            - self.feature_ref.as_dict: collaborator call used by this boundary
            - self.scenario_ref.as_dict: collaborator call used by this boundary
            - self.step_ref.as_dict: collaborator call used by this boundary
            - self.previous_step_ref.as_dict: collaborator call used by this boundary
            - self.active_set.as_dict: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/model/message_transport.py: imports or references `as_dict`
            - src/pytest_bdd/model/run/lifecycle/_run.py: imports or references `as_dict`
            - src/pytest_bdd/model/run/lifecycle/_snapshots.py: imports or references `as_dict`
            - src/pytest_bdd/model/run/lifecycle/_states.py: imports or references `as_dict`
            - src/pytest_bdd/model/run_access.py: imports or references `as_dict`

        State and side effects:
            keeps no local persistent state beyond call-local values.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=3
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=4

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
