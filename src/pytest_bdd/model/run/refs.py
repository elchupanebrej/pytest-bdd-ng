"""
Lifecycle object reference helpers for the run model.

Responsibility:
    Lifecycle object reference helpers for the run model. It directly owns the observable contract, local decisions, and
    maintenance boundary for this module.

Reason for existence:
    This entity is the information expert for `pytest_bdd.model.run.refs` because it keeps the nearest code, data shape,
    call signature, and failure knowledge together.

Delegates:
    - LifecycleObjectRef: owns nested behavior below this boundary
    - NoPreviousStep: owns nested behavior below this boundary
    - _inactive_feature_ref: owns nested behavior below this boundary
    - _inactive_scenario_ref: owns nested behavior below this boundary
    - _inactive_step_ref: owns nested behavior below this boundary
    - _no_previous_step_ref: owns nested behavior below this boundary

Cohesion:
    The implementation stays together because its imports, calls, state writes, and return contract describe one
    maintainable decision unit.

Separation:
    - module peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
      widening caller knowledge.

Main consumers:
    - src/pytest_bdd/model/run/__init__.py: imports or references `refs`
    - src/pytest_bdd/model/run/lifecycle/_run.py: imports or references `refs`
    - src/pytest_bdd/model/run/lifecycle/_states.py: imports or references `refs`
    - src/pytest_bdd/model/run/transitions.py: imports or references `refs`

State and side effects:
    mutates LifecycleKind, kind, object_id, name, source; depends on __future__.annotations, typing.TYPE_CHECKING,
    typing.Literal, attrs.define, pytest_bdd.compatibility.typing.Self.

Invariants:
    - `pytest_bdd.model.run.refs` keeps its documented import path, ownership boundary, and observable behavior stable
      for callers.

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

from attrs import define

if TYPE_CHECKING:
    from pytest_bdd.compatibility.typing import Self
    from pytest_bdd.types.json import JSONObject

LifecycleKind = Literal["run", "feature", "scenario", "step"]


@define(slots=True)
class LifecycleObjectRef:
    """
    Represent lifecycle object ref state.

    Responsibility:
        Represent lifecycle object ref state. It directly owns the observable contract, local decisions, and maintenance
        boundary for this class. That boundary is intentionally stated in prose so maintainers can distinguish owned
        work from collaborators before editing.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.model.run.refs.LifecycleObjectRef` because it keeps the
        nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - inactive: owns nested behavior below this boundary
        - as_dict: owns nested behavior below this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/model/__init__.py: imports or references `LifecycleObjectRef`
        - src/pytest_bdd/model/run/__init__.py: imports or references `LifecycleObjectRef`
        - src/pytest_bdd/model/run/lifecycle/_run.py: imports or references `LifecycleObjectRef`
        - src/pytest_bdd/model/run/lifecycle/_states.py: imports or references `LifecycleObjectRef`
        - src/pytest_bdd/model/run/transitions.py: imports or references `LifecycleObjectRef`

    State and side effects:
        mutates kind, object_id, name, source, is_active.

    Invariants:
        - `pytest_bdd.model.run.refs.LifecycleObjectRef` keeps its documented import path, ownership boundary, and
          observable behavior stable for callers.

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

    kind: LifecycleKind
    object_id: str
    name: str | None = None
    source: str | None = None
    is_active: bool = True
    empty_state_reason: str | None = None
    fail_fast_code: str | None = None

    @classmethod
    def inactive(
        cls,
        kind: LifecycleKind,
        *,
        reason: str,
        name: str | None = None,
        source: str | None = "lifecycle-slot",
        fail_fast_code: str | None = None,
    ) -> Self:
        """
        Create a LifecycleObjectRef representing an inactive state, indicating the object is not currently executing.

        Returns:
            A new LifecycleObjectRef instance marked as inactive.

        Responsibility:
            Create a LifecycleObjectRef representing an inactive state, indicating the object is not currently
            executing. It directly owns the observable contract, local decisions, and maintenance boundary for this
            method.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.model.run.refs.LifecycleObjectRef.inactive` because it
            keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - cls: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/model/run/__init__.py: imports or references `inactive`
            - src/pytest_bdd/model/run/lifecycle/_run.py: imports or references `inactive`
            - src/pytest_bdd/model/run/lifecycle/_states.py: imports or references `inactive`
            - src/pytest_bdd/model/run/transitions.py: imports or references `inactive`
            - src/pytest_bdd/plugin/pickle_runner/run_transitions.py: imports or references `inactive`

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
        return cls(
            kind=kind,
            object_id=f"{kind}:{reason}",
            name=name or kind,
            source=source,
            is_active=False,
            empty_state_reason=reason,
            fail_fast_code=fail_fast_code,
        )

    def as_dict(self) -> JSONObject:
        """
        Serialize the lifecycle object reference state into a dictionary representation.

        Returns:
            A dictionary containing the reference details.

        Responsibility:
            Serialize the lifecycle object reference state into a dictionary representation. It directly owns the
            observable contract, local decisions, and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.model.run.refs.LifecycleObjectRef.as_dict` because it
            keeps the nearest code, data shape, call signature, and failure knowledge together.

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
            - src/pytest_bdd/model/run/__init__.py: imports or references `as_dict`
            - src/pytest_bdd/model/run/lifecycle/_run.py: imports or references `as_dict`
            - src/pytest_bdd/model/run/lifecycle/_snapshots.py: imports or references `as_dict`
            - src/pytest_bdd/model/run/lifecycle/_states.py: imports or references `as_dict`

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
            "kind": self.kind,
            "object_id": self.object_id,
            "name": self.name,
            "source": self.source,
            "is_active": self.is_active,
            "empty_state_reason": self.empty_state_reason,
            "fail_fast_code": self.fail_fast_code,
        }


@define(slots=True)
class NoPreviousStep:
    """
    Represent no previous step state.

    Responsibility:
        Represent no previous step state. It directly owns the observable contract, local decisions, and maintenance
        boundary for this class. That boundary is intentionally stated in prose so maintainers can distinguish owned
        work from collaborators before editing.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.model.run.refs.NoPreviousStep` because it keeps the
        nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - define: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/model/run/__init__.py: imports or references `NoPreviousStep`
        - src/pytest_bdd/model/run/lifecycle/_run.py: imports or references `NoPreviousStep`
        - src/pytest_bdd/model/run/lifecycle/_states.py: imports or references `NoPreviousStep`
        - src/pytest_bdd/model/run/transitions.py: imports or references `NoPreviousStep`
        - src/pytest_bdd/model/scenario_run.py: imports or references `NoPreviousStep`

    State and side effects:
        mutates id, text, keyword.

    Invariants:
        - `pytest_bdd.model.run.refs.NoPreviousStep` keeps its documented import path, ownership boundary, and
          observable behavior stable for callers.

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

    id: str = "step:no_previous_step"
    text: str = ""
    keyword: str = ""


def _inactive_feature_ref() -> LifecycleObjectRef:
    """
    Responsibility:
        Responsibility: Responsibility: `pytest_bdd.model.run.refs._inactive_feature_ref` owns documented function
        behavior. It directly owns the observable contract, local decisions, and maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.model.run.refs._inactive_feature_ref` because it keeps the
        nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - LifecycleObjectRef.inactive: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/model/run/__init__.py: imports or references `_inactive_feature_ref`
        - src/pytest_bdd/model/run/lifecycle/_run.py: imports or references `_inactive_feature_ref`
        - src/pytest_bdd/model/run/lifecycle/_states.py: imports or references `_inactive_feature_ref`
        - src/pytest_bdd/model/run/transitions.py: imports or references `_inactive_feature_ref`
        - src/pytest_bdd/model/scenario_run.py: imports or references `_inactive_feature_ref`

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
    return LifecycleObjectRef.inactive("feature", reason="idle")


def _inactive_scenario_ref() -> LifecycleObjectRef:
    """
    Responsibility:
        Responsibility: Responsibility: `pytest_bdd.model.run.refs._inactive_scenario_ref` owns documented function
        behavior. It directly owns the observable contract, local decisions, and maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.model.run.refs._inactive_scenario_ref` because it keeps
        the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - LifecycleObjectRef.inactive: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/model/run/__init__.py: imports or references `_inactive_scenario_ref`
        - src/pytest_bdd/model/run/lifecycle/_run.py: imports or references `_inactive_scenario_ref`
        - src/pytest_bdd/model/run/lifecycle/_states.py: imports or references `_inactive_scenario_ref`
        - src/pytest_bdd/model/run/transitions.py: imports or references `_inactive_scenario_ref`
        - src/pytest_bdd/model/scenario_run.py: imports or references `_inactive_scenario_ref`

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
    return LifecycleObjectRef.inactive("scenario", reason="idle")


def _inactive_step_ref() -> LifecycleObjectRef:
    """
    Responsibility:
        Responsibility: Responsibility: `pytest_bdd.model.run.refs._inactive_step_ref` owns documented function
        behavior. It directly owns the observable contract, local decisions, and maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.model.run.refs._inactive_step_ref` because it keeps the
        nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - LifecycleObjectRef.inactive: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/model/run/__init__.py: imports or references `_inactive_step_ref`
        - src/pytest_bdd/model/run/lifecycle/_run.py: imports or references `_inactive_step_ref`
        - src/pytest_bdd/model/run/lifecycle/_states.py: imports or references `_inactive_step_ref`
        - src/pytest_bdd/model/run/transitions.py: imports or references `_inactive_step_ref`
        - src/pytest_bdd/model/scenario_run.py: imports or references `_inactive_step_ref`

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
    return LifecycleObjectRef.inactive("step", reason="idle", fail_fast_code="object_inactive")


def _no_previous_step_ref() -> LifecycleObjectRef:
    """
    Responsibility:
        Responsibility: Responsibility: `pytest_bdd.model.run.refs._no_previous_step_ref` owns documented function
        behavior. It directly owns the observable contract, local decisions, and maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.model.run.refs._no_previous_step_ref` because it keeps the
        nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - LifecycleObjectRef.inactive: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/model/run/__init__.py: imports or references `_no_previous_step_ref`
        - src/pytest_bdd/model/run/lifecycle/_run.py: imports or references `_no_previous_step_ref`
        - src/pytest_bdd/model/run/lifecycle/_states.py: imports or references `_no_previous_step_ref`
        - src/pytest_bdd/model/run/transitions.py: imports or references `_no_previous_step_ref`
        - src/pytest_bdd/model/scenario_run.py: imports or references `_no_previous_step_ref`

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
    return LifecycleObjectRef.inactive("step", reason="no_previous_step")


def _finished_feature_ref() -> LifecycleObjectRef:
    """
    Responsibility:
        Responsibility: Responsibility: `pytest_bdd.model.run.refs._finished_feature_ref` owns documented function
        behavior. It directly owns the observable contract, local decisions, and maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.model.run.refs._finished_feature_ref` because it keeps the
        nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - LifecycleObjectRef.inactive: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/model/run/__init__.py: imports or references `_finished_feature_ref`
        - src/pytest_bdd/model/run/lifecycle/_run.py: imports or references `_finished_feature_ref`
        - src/pytest_bdd/model/run/lifecycle/_states.py: imports or references `_finished_feature_ref`
        - src/pytest_bdd/model/run/transitions.py: imports or references `_finished_feature_ref`
        - src/pytest_bdd/model/scenario_run.py: imports or references `_finished_feature_ref`

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
    return LifecycleObjectRef.inactive("feature", reason="finished")


def _finished_scenario_ref() -> LifecycleObjectRef:
    """
    Responsibility:
        Responsibility: Responsibility: `pytest_bdd.model.run.refs._finished_scenario_ref` owns documented function
        behavior. It directly owns the observable contract, local decisions, and maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.model.run.refs._finished_scenario_ref` because it keeps
        the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - LifecycleObjectRef.inactive: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/model/run/__init__.py: imports or references `_finished_scenario_ref`
        - src/pytest_bdd/model/run/lifecycle/_run.py: imports or references `_finished_scenario_ref`
        - src/pytest_bdd/model/run/lifecycle/_states.py: imports or references `_finished_scenario_ref`
        - src/pytest_bdd/model/run/transitions.py: imports or references `_finished_scenario_ref`
        - src/pytest_bdd/model/scenario_run.py: imports or references `_finished_scenario_ref`

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
    return LifecycleObjectRef.inactive("scenario", reason="finished")


def _finished_step_ref() -> LifecycleObjectRef:
    """
    Responsibility:
        Responsibility: Responsibility: `pytest_bdd.model.run.refs._finished_step_ref` owns documented function
        behavior. It directly owns the observable contract, local decisions, and maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.model.run.refs._finished_step_ref` because it keeps the
        nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - LifecycleObjectRef.inactive: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/model/run/__init__.py: imports or references `_finished_step_ref`
        - src/pytest_bdd/model/run/lifecycle/_run.py: imports or references `_finished_step_ref`
        - src/pytest_bdd/model/run/lifecycle/_states.py: imports or references `_finished_step_ref`
        - src/pytest_bdd/model/run/transitions.py: imports or references `_finished_step_ref`
        - src/pytest_bdd/model/scenario_run.py: imports or references `_finished_step_ref`

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
    return LifecycleObjectRef.inactive("step", reason="finished", fail_fast_code="object_inactive")


def _finished_previous_step_ref() -> LifecycleObjectRef:
    """
    Responsibility:
        Responsibility: Responsibility: `pytest_bdd.model.run.refs._finished_previous_step_ref` owns documented function
        behavior. It directly owns the observable contract, local decisions, and maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.model.run.refs._finished_previous_step_ref` because it
        keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - LifecycleObjectRef.inactive: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/model/run/__init__.py: imports or references `_finished_previous_step_ref`
        - src/pytest_bdd/model/run/lifecycle/_run.py: imports or references `_finished_previous_step_ref`
        - src/pytest_bdd/model/run/lifecycle/_states.py: imports or references `_finished_previous_step_ref`
        - src/pytest_bdd/model/run/transitions.py: imports or references `_finished_previous_step_ref`
        - src/pytest_bdd/model/scenario_run.py: imports or references `_finished_previous_step_ref`

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
    return LifecycleObjectRef.inactive("step", reason="finished")
