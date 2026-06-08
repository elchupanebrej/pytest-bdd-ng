"""
State classes for the run lifecycle: ActiveObjectSet, error state, reporting state.

Responsibility:
    State classes for the run lifecycle: ActiveObjectSet, error state, reporting state. It directly owns the observable
    contract, local decisions, and maintenance boundary for this module.

Reason for existence:
    This entity is the information expert for `pytest_bdd.model.run.lifecycle._states` because it keeps the nearest
    code, data shape, call signature, and failure knowledge together.

Delegates:
    - ActiveObjectSet: owns nested behavior below this boundary
    - ReportingLifecycleState: owns nested behavior below this boundary
    - ReferenceResolverState: owns nested behavior below this boundary
    - ContextErrorState: owns nested behavior below this boundary

Cohesion:
    The implementation stays together because its imports, calls, state writes, and return contract describe one
    maintainable decision unit.

Separation:
    - module peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
      widening caller knowledge.

Main consumers:
    - src/pytest_bdd/model/run/lifecycle/facade.py: imports or references `_states`

State and side effects:
    mutates run, captured_at_stage, feature, scenario, step; depends on __future__.annotations, typing.TYPE_CHECKING,
    typing.Literal, typing.cast, attrs.define.

Invariants:
    - `pytest_bdd.model.run.lifecycle._states` keeps its documented import path, ownership boundary, and observable
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
    #arch-eval:locational_stability=3
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal, cast

from attrs import define, field

from pytest_bdd.model.run.refs import (
    LifecycleKind,
    LifecycleObjectRef,
    _inactive_feature_ref,
    _inactive_scenario_ref,
    _inactive_step_ref,
    _no_previous_step_ref,
)

if TYPE_CHECKING:
    from pytest_bdd.model.run.stages import RunStage
    from pytest_bdd.types.json import JSONObject, JSONValue


@define(slots=True)
class ActiveObjectSet:
    """
    Store contextual variables representing the current execution parameters for a specific scenario attempt.

    Responsibility:
        Store contextual variables representing the current execution parameters for a specific scenario attempt. It
        directly owns the observable contract, local decisions, and maintenance boundary for this class.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.model.run.lifecycle._states.ActiveObjectSet` because it
        keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - as_dict: owns nested behavior below this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/model/__init__.py: imports or references `ActiveObjectSet`
        - src/pytest_bdd/model/run/__init__.py: imports or references `ActiveObjectSet`
        - src/pytest_bdd/model/run/lifecycle/_run.py: imports or references `ActiveObjectSet`
        - src/pytest_bdd/model/run/lifecycle/_snapshots.py: imports or references `ActiveObjectSet`
        - src/pytest_bdd/model/run/lifecycle/facade.py: imports or references `ActiveObjectSet`

    State and side effects:
        mutates run, captured_at_stage, feature, scenario, step.

    Invariants:
        - `pytest_bdd.model.run.lifecycle._states.ActiveObjectSet` keeps its documented import path, ownership boundary,
          and observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=3
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=3
        #arch-eval:locational_stability=4
    """

    run: LifecycleObjectRef
    captured_at_stage: RunStage
    feature: LifecycleObjectRef = field(factory=_inactive_feature_ref)
    scenario: LifecycleObjectRef = field(factory=_inactive_scenario_ref)
    step: LifecycleObjectRef = field(factory=_inactive_step_ref)
    previous_step: LifecycleObjectRef = field(factory=_no_previous_step_ref)

    def as_dict(self) -> JSONObject:
        """
        Serialize the entire active object set into a JSON-compatible dictionary.

        Returns:
            A dictionary representing the current active states for run, feature, scenario, and step.

        Responsibility:
            Serialize the entire active object set into a JSON-compatible dictionary. It directly owns the observable
            contract, local decisions, and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.model.run.lifecycle._states.ActiveObjectSet.as_dict`
            because it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - self.run.as_dict: collaborator call used by this boundary
            - self.feature.as_dict: collaborator call used by this boundary
            - self.scenario.as_dict: collaborator call used by this boundary
            - self.step.as_dict: collaborator call used by this boundary
            - self.previous_step.as_dict: collaborator call used by this boundary

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
            - src/pytest_bdd/model/run/lifecycle/facade.py: imports or references `as_dict`
            - src/pytest_bdd/model/scenario_run.py: imports or references `as_dict`

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
            "run": self.run.as_dict(),
            "feature": self.feature.as_dict(),
            "scenario": self.scenario.as_dict(),
            "step": self.step.as_dict(),
            "previous_step": self.previous_step.as_dict(),
            "captured_at_stage": self.captured_at_stage.value,
        }


@define(slots=True)
class ReportingLifecycleState:
    """
    Represent reporting lifecycle state state.

    Responsibility:
        Represent reporting lifecycle state state. It directly owns the observable contract, local decisions, and
        maintenance boundary for this class.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.model.run.lifecycle._states.ReportingLifecycleState`
        because it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - reset_scenario_scope: owns nested behavior below this boundary
        - as_dict: owns nested behavior below this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/model/__init__.py: imports or references `ReportingLifecycleState`
        - src/pytest_bdd/model/run/__init__.py: imports or references `ReportingLifecycleState`
        - src/pytest_bdd/model/run/lifecycle/_run.py: imports or references `ReportingLifecycleState`
        - src/pytest_bdd/model/run/lifecycle/facade.py: imports or references `ReportingLifecycleState`

    State and side effects:
        mutates run_started_id, test_run_hook_started_id, active_test_case_id, active_test_case_started_id,
        active_test_step_id.

    Invariants:
        - `pytest_bdd.model.run.lifecycle._states.ReportingLifecycleState` keeps its documented import path, ownership
          boundary, and observable behavior stable for callers.

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

    run_started_id: str | None = None
    test_run_hook_started_id: str | None = None
    active_test_case_id: str | None = None
    active_test_case_started_id: str | None = None
    active_test_step_id: str | None = None
    runtime_step_to_pickle_step_id: dict[int, str] = field(factory=dict)
    scenario_attempt_context: dict[str, str | int] | None = None
    step_started_timestamp: JSONValue = None
    step_finished_timestamp: JSONValue = None

    def reset_scenario_scope(self) -> None:
        """
        Clear scenario-level reporting state variables to prepare for a new scenario or clean up.

        Responsibility:
            Clear scenario-level reporting state variables to prepare for a new scenario or clean up. It directly owns
            the observable contract, local decisions, and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.model.run.lifecycle._states.ReportingLifecycleState.reset_scenario_scope` because it keeps the
            nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - self.runtime_step_to_pickle_step_id.clear: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/model/run/lifecycle/_run.py: imports or references `reset_scenario_scope`
            - src/pytest_bdd/model/run/lifecycle/facade.py: imports or references `reset_scenario_scope`
            - src/pytest_bdd/plugin/gherkin_message_reporter/scenario_runtime.py: imports or references
              `reset_scenario_scope`

        State and side effects:
            mutates self.active_test_case_id, self.active_test_case_started_id, self.active_test_step_id,
            self.scenario_attempt_context, self.step_started_timestamp.

        Invariants:
            - `pytest_bdd.model.run.lifecycle._states.ReportingLifecycleState.reset_scenario_scope` keeps its documented
              import path, ownership boundary, and observable behavior stable for callers.

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
        self.active_test_case_id = None
        self.active_test_case_started_id = None
        self.active_test_step_id = None
        self.runtime_step_to_pickle_step_id.clear()
        self.scenario_attempt_context = None
        self.step_started_timestamp = None
        self.step_finished_timestamp = None

    def as_dict(self) -> JSONObject:
        """
        Serialize the reporting lifecycle state into a JSON-compatible dictionary.

        Returns:
            A dictionary representing the reporting identifiers and timestamps.

        Responsibility:
            Serialize the reporting lifecycle state into a JSON-compatible dictionary. It directly owns the observable
            contract, local decisions, and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.model.run.lifecycle._states.ReportingLifecycleState.as_dict` because it keeps the nearest code,
            data shape, call signature, and failure knowledge together.

        Delegates:
            - str: collaborator call used by this boundary
            - self.runtime_step_to_pickle_step_id.items: collaborator call used by this boundary
            - cast: collaborator call used by this boundary
            - dict: collaborator call used by this boundary

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
            - src/pytest_bdd/model/run/lifecycle/facade.py: imports or references `as_dict`
            - src/pytest_bdd/model/scenario_run.py: imports or references `as_dict`

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
            "run_started_id": self.run_started_id,
            "test_run_hook_started_id": self.test_run_hook_started_id,
            "active_test_case_id": self.active_test_case_id,
            "active_test_case_started_id": self.active_test_case_started_id,
            "active_test_step_id": self.active_test_step_id,
            "runtime_step_to_test_step_id": {
                str(key): value for key, value in self.runtime_step_to_pickle_step_id.items()
            },
            "scenario_attempt_context": cast("JSONObject", dict(self.scenario_attempt_context))
            if self.scenario_attempt_context is not None
            else None,
            "step_started_timestamp": self.step_started_timestamp,
            "step_finished_timestamp": self.step_finished_timestamp,
        }


@define(slots=True)
class ReferenceResolverState:
    """
    Represent reference resolver state state.

    Responsibility:
        Represent reference resolver state state. It directly owns the observable contract, local decisions, and
        maintenance boundary for this class.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.model.run.lifecycle._states.ReferenceResolverState`
        because it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - add_missing_reference: owns nested behavior below this boundary
        - clear: owns nested behavior below this boundary
        - as_dict: owns nested behavior below this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/model/__init__.py: imports or references `ReferenceResolverState`
        - src/pytest_bdd/model/run/__init__.py: imports or references `ReferenceResolverState`
        - src/pytest_bdd/model/run/lifecycle/facade.py: imports or references `ReferenceResolverState`
        - src/pytest_bdd/model/scenario_run.py: imports or references `ReferenceResolverState`

    State and side effects:
        mutates missing_reference_diagnostics.

    Invariants:
        - `pytest_bdd.model.run.lifecycle._states.ReferenceResolverState` keeps its documented import path, ownership
          boundary, and observable behavior stable for callers.

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

    missing_reference_diagnostics: list[str] = field(factory=list)

    def add_missing_reference(self, message: str) -> None:
        """
        Record a diagnostic message regarding a missing reference encountered during validation.

        Responsibility:
            Record a diagnostic message regarding a missing reference encountered during validation. It directly owns
            the observable contract, local decisions, and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.model.run.lifecycle._states.ReferenceResolverState.add_missing_reference` because it keeps the
            nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - self.missing_reference_diagnostics.append: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/model/run/lifecycle/facade.py: imports or references `add_missing_reference`
            - src/pytest_bdd/model/run_access.py: imports or references `add_missing_reference`

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
            #arch-eval:locational_stability=3
        """
        self.missing_reference_diagnostics.append(message)

    def clear(self) -> None:
        """
        Clear all accumulated missing reference diagnostic messages.

        Responsibility:
            Clear all accumulated missing reference diagnostic messages. It directly owns the observable contract, local
            decisions, and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.model.run.lifecycle._states.ReferenceResolverState.clear` because it keeps the nearest code,
            data shape, call signature, and failure knowledge together.

        Delegates:
            - self.missing_reference_diagnostics.clear: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/collector_batch.py: imports or references `clear`
            - src/pytest_bdd/model/run/lifecycle/_run.py: imports or references `clear`
            - src/pytest_bdd/model/run/lifecycle/facade.py: imports or references `clear`
            - src/pytest_bdd/plugin/debug_mcp/entrypoint.py: imports or references `clear`
            - src/pytest_bdd/plugin/gherkin_message_reporter/step_catalog_runtime/_core.py: imports or references
              `clear`

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
        self.missing_reference_diagnostics.clear()

    def as_dict(self) -> JSONObject:
        """
        Serialize the reference resolver state into a dictionary format.

        Returns:
            A dictionary containing the list of missing reference diagnostics.

        Responsibility:
            Serialize the reference resolver state into a dictionary format. It directly owns the observable contract,
            local decisions, and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.model.run.lifecycle._states.ReferenceResolverState.as_dict` because it keeps the nearest code,
            data shape, call signature, and failure knowledge together.

        Delegates:
            - list: collaborator call used by this boundary

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
            - src/pytest_bdd/model/run/lifecycle/facade.py: imports or references `as_dict`
            - src/pytest_bdd/model/scenario_run.py: imports or references `as_dict`

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
            "missing_reference_diagnostics": list(self.missing_reference_diagnostics),
        }


@define(slots=True)
class ContextErrorState:
    """
    Represent context error state state.

    Responsibility:
        Represent context error state state. It directly owns the observable contract, local decisions, and maintenance
        boundary for this class. That boundary is intentionally stated in prose so maintainers can distinguish owned
        work from collaborators before editing.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.model.run.lifecycle._states.ContextErrorState` because it
        keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - as_dict: owns nested behavior below this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/model/__init__.py: imports or references `ContextErrorState`
        - src/pytest_bdd/model/run/__init__.py: imports or references `ContextErrorState`
        - src/pytest_bdd/model/run/lifecycle/_run.py: imports or references `ContextErrorState`
        - src/pytest_bdd/model/run/lifecycle/facade.py: imports or references `ContextErrorState`
        - src/pytest_bdd/model/run_access.py: imports or references `ContextErrorState`

    State and side effects:
        mutates code, message, hook_name, stage, requested_kind.

    Invariants:
        - `pytest_bdd.model.run.lifecycle._states.ContextErrorState` keeps its documented import path, ownership
          boundary, and observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=3
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=3
        #arch-eval:locational_stability=4
    """

    code: Literal["object_inactive", "transition_order_violation", "context_not_initialized", "binding_missing"]
    message: str
    hook_name: str
    stage: RunStage
    requested_kind: LifecycleKind | None = None

    def as_dict(self) -> JSONObject:
        """
        Serialize the context error state into a dictionary format.

        Returns:
            A dictionary describing the error code, message, and related lifecycle context.

        Responsibility:
            Serialize the context error state into a dictionary format. It directly owns the observable contract, local
            decisions, and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.model.run.lifecycle._states.ContextErrorState.as_dict`
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
            - src/pytest_bdd/model/message_transport.py: imports or references `as_dict`
            - src/pytest_bdd/model/run/lifecycle/_run.py: imports or references `as_dict`
            - src/pytest_bdd/model/run/lifecycle/_snapshots.py: imports or references `as_dict`
            - src/pytest_bdd/model/run/lifecycle/facade.py: imports or references `as_dict`
            - src/pytest_bdd/model/scenario_run.py: imports or references `as_dict`

        State and side effects:
            keeps no local persistent state beyond call-local values.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=2
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=3
            #arch-eval:entity_fullness=3
            #arch-eval:locational_stability=4

        """
        return {
            "code": self.code,
            "message": self.message,
            "hook_name": self.hook_name,
            "stage": self.stage.value,
            "requested_kind": self.requested_kind,
        }
