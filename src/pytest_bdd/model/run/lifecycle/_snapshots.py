"""
Snapshot and compatibility record classes for the run lifecycle.

Responsibility:
    Snapshot and compatibility record classes for the run lifecycle. It directly owns the observable contract, local
    decisions, and maintenance boundary for this module.

Reason for existence:
    This entity is the information expert for `pytest_bdd.model.run.lifecycle._snapshots` because it keeps the nearest
    code, data shape, call signature, and failure knowledge together.

Delegates:
    - ReportingContextSnapshot: owns nested behavior below this boundary
    - ExternalApiCompatibilityRecord: owns nested behavior below this boundary

Cohesion:
    The implementation stays together because its imports, calls, state writes, and return contract describe one
    maintainable decision unit.

Separation:
    - module peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
      widening caller knowledge.

Main consumers:
    - src/pytest_bdd/model/run/lifecycle/facade.py: imports or references `_snapshots`

State and side effects:
    mutates run_id, active_set, stage, resolved_from_hierarchy, fallback_reason; depends on __future__.annotations,
    typing.TYPE_CHECKING, typing.cast, attrs.define, pytest_bdd.model.run.stages.RunStage.

Invariants:
    - `pytest_bdd.model.run.lifecycle._snapshots` keeps its documented import path, ownership boundary, and observable
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

from typing import TYPE_CHECKING, cast

from attrs import define

if TYPE_CHECKING:
    from pytest_bdd.model.run.stages import RunStage
    from pytest_bdd.types.json import JSONArray, JSONObject

    from ._states import ActiveObjectSet


@define(slots=True)
class ReportingContextSnapshot:
    """
    Capture an immutable, point-in-time snapshot of the active execution context for reporting purposes.

    Responsibility:
        Capture an immutable, point-in-time snapshot of the active execution context for reporting purposes. It directly
        owns the observable contract, local decisions, and maintenance boundary for this class.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.model.run.lifecycle._snapshots.ReportingContextSnapshot`
        because it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - as_dict: owns nested behavior below this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/model/__init__.py: imports or references `ReportingContextSnapshot`
        - src/pytest_bdd/model/run/__init__.py: imports or references `ReportingContextSnapshot`
        - src/pytest_bdd/model/run/lifecycle/facade.py: imports or references `ReportingContextSnapshot`
        - src/pytest_bdd/model/run_access.py: imports or references `ReportingContextSnapshot`
        - src/pytest_bdd/model/scenario_report.py: imports or references `ReportingContextSnapshot`

    State and side effects:
        mutates run_id, active_set, stage, resolved_from_hierarchy, fallback_reason.

    Invariants:
        - `pytest_bdd.model.run.lifecycle._snapshots.ReportingContextSnapshot` keeps its documented import path,
          ownership boundary, and observable behavior stable for callers.

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

    run_id: str
    active_set: ActiveObjectSet
    stage: RunStage
    resolved_from_hierarchy: bool
    fallback_reason: str | None = None

    def as_dict(self) -> JSONObject:
        """
        Serialize the reporting context snapshot into a dictionary format.

        Returns:
            A dictionary containing the active object references and resolution metadata.

        Responsibility:
            Serialize the reporting context snapshot into a dictionary format. It directly owns the observable contract,
            local decisions, and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.model.run.lifecycle._snapshots.ReportingContextSnapshot.as_dict` because it keeps the nearest
            code, data shape, call signature, and failure knowledge together.

        Delegates:
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
            - src/pytest_bdd/model/run/lifecycle/_states.py: imports or references `as_dict`
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
            "run_id": self.run_id,
            "active_set": self.active_set.as_dict(),
            "stage": self.stage.value,
            "resolved_from_hierarchy": self.resolved_from_hierarchy,
            "fallback_reason": self.fallback_reason,
        }


@define(slots=True)
class ExternalApiCompatibilityRecord:
    """
    Log structural changes and migration requirements for an exposed API surface relative to a baseline.

    Responsibility:
        Log structural changes and migration requirements for an exposed API surface relative to a baseline. It directly
        owns the observable contract, local decisions, and maintenance boundary for this class.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.model.run.lifecycle._snapshots.ExternalApiCompatibilityRecord` because it keeps the nearest code,
        data shape, call signature, and failure knowledge together.

    Delegates:
        - as_dict: owns nested behavior below this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/model/__init__.py: imports or references `ExternalApiCompatibilityRecord`
        - src/pytest_bdd/model/run/__init__.py: imports or references `ExternalApiCompatibilityRecord`
        - src/pytest_bdd/model/run/lifecycle/facade.py: imports or references `ExternalApiCompatibilityRecord`
        - src/pytest_bdd/plugin/pickle_runner/api_compatibility.py: imports or references
          `ExternalApiCompatibilityRecord`

    State and side effects:
        mutates api_surface_id, baseline_reference, changed_symbols, removed_symbols, renamed_symbols.

    Invariants:
        - `pytest_bdd.model.run.lifecycle._snapshots.ExternalApiCompatibilityRecord` keeps its documented import path,
          ownership boundary, and observable behavior stable for callers.

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

    api_surface_id: str
    baseline_reference: str
    changed_symbols: list[str]
    removed_symbols: list[str]
    renamed_symbols: list[str]
    additive_symbols: list[str]
    consumer_migration_required: bool

    def as_dict(self) -> JSONObject:
        """
        Serialize the compatibility record into a dictionary format.

        Returns:
            A dictionary detailing the symbol changes and consumer migration requirements.

        Responsibility:
            Serialize the compatibility record into a dictionary format. It directly owns the observable contract, local
            decisions, and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.model.run.lifecycle._snapshots.ExternalApiCompatibilityRecord.as_dict` because it keeps the
            nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - cast: collaborator call used by this boundary
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
            - src/pytest_bdd/model/run/lifecycle/_states.py: imports or references `as_dict`
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
            "api_surface_id": self.api_surface_id,
            "baseline_reference": self.baseline_reference,
            "changed_symbols": cast("JSONArray", list(self.changed_symbols)),
            "removed_symbols": cast("JSONArray", list(self.removed_symbols)),
            "renamed_symbols": cast("JSONArray", list(self.renamed_symbols)),
            "additive_symbols": cast("JSONArray", list(self.additive_symbols)),
            "consumer_migration_required": self.consumer_migration_required,
        }
