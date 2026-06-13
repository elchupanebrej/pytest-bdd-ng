"""
Defines snapshot value objects for capturing runtime reporting context: ReportingContextSnapshot (records run_id, act.

Responsibility:
    Defines snapshot value objects for capturing runtime reporting context: ReportingContextSnapshot (records run_id,
    active_set, stage, resolution source, and fallback reason for reporters) and ExternalApiCompatibilityRecord (tracks
    API surface changes across versions with changed/removed/renamed/additive symbol lists). Both are attrs-defined with
    slots=True and include as_dict() serialization for JSON output.

Reason for existence:
    This code is the authoritative information expert for its domain boundary within the pytest-bdd model layer. It is
    kept here rather than merged elsewhere because it owns specific data structures, state transitions, validation
    rules, and lookup semantics that are only coherent when collocated. Analyzing imports and control flow confirms this
    module is the single source of truth for its owned concepts

Delegates:
    - ActiveObjectSet: Provides supporting functionality through a well-defined interface, delegating a focused sub-task
    to keep this entity cohesive and its responsibility boundary clean

Cohesion:
    All functions, methods, and data within this entity operate on the same local state, share identical import
    dependencies and control flow patterns, and collectively implement a single cohesive responsibility rather than
    dispersing unrelated utilities across separate modules

Separation:
    - _states: This entity is kept distinct from its peer to prevent callers from coupling to multiple domain boundaries
    at once, ensuring each concept can evolve independently without cascading changes across the codebase

Main consumers:
    - run_access: Referenced by collection, runtime, and reporting layer plugins through the pytest_bdd.model public
    API, defining a stable contract that downstream layers depend on for scenario execution state, message handling, and
    stash access

State and side effects:
    Maintains in-memory state via attrs-defined fields with factory defaults, performing no file I/O, network
    operations, or direct pytest stash access; stash interaction is delegated to StashAccess class methods for type-safe
    boundary enforcement

Invariants:
    - ReportingContextSnapshot.resolved_from_hierarchy must be true when resolved from Run hierarchy; fallback_reason
    must be set when resolution_from_hierarchy is false; ExternalApiCompatibilityRecord symbol lists must be non-
    overlapping

Architecture score:
    #arch-eval:reason_for_existence=4
    #arch-eval:owned_responsibility=5
    #arch-eval:delegation_boundary=4
    #arch-eval:cohesion=4
    #arch-eval:separation=4
    #arch-eval:consumer_clarity=4
    #arch-eval:state_invariants=4
    #arch-eval:entity_fullness=3
    #arch-eval:locational_stability=4
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
    Defines snapshot value objects for capturing runtime reporting context: ReportingContextSnapshot (records run_id, act.

    Responsibility:
        Defines snapshot value objects for capturing runtime reporting context: ReportingContextSnapshot (records
        run_id, active_set, stage, resolution source, and fallback reason for reporters) and
        ExternalApiCompatibilityRecord (tracks API surface changes across versions with changed/removed/renamed/additive
        symbol lists). Both are attrs-defined with slots=True and include as_dict() serialization for JSON output.

    Reason for existence:
        This code is the authoritative information expert for its domain boundary within the pytest-bdd model layer. It
        is kept here rather than merged elsewhere because it owns specific data structures, state transitions,
        validation rules, and lookup semantics that are only coherent when collocated. Analyzing imports and control
        flow confirms this module is the single source of truth for its owned concepts

    Delegates:
        - ActiveObjectSet: Provides supporting functionality through a well-defined interface, delegating a focused sub-
        task to keep this entity cohesive and its responsibility boundary clean

    Cohesion:
        All functions, methods, and data within this entity operate on the same local state, share identical import
        dependencies and control flow patterns, and collectively implement a single cohesive responsibility rather than
        dispersing unrelated utilities across separate modules

    Separation:
        - _states: This entity is kept distinct from its peer to prevent callers from coupling to multiple domain
        boundaries at once, ensuring each concept can evolve independently without cascading changes across the codebase

    Main consumers:
        - run_access: Referenced by collection, runtime, and reporting layer plugins through the pytest_bdd.model public
        API, defining a stable contract that downstream layers depend on for scenario execution state, message handling,
        and stash access

    State and side effects:
        Maintains in-memory state via attrs-defined fields with factory defaults, performing no file I/O, network
        operations, or direct pytest stash access; stash interaction is delegated to StashAccess class methods for type-
        safe boundary enforcement

    Invariants:
        - ReportingContextSnapshot.resolved_from_hierarchy must be true when resolved from Run hierarchy;
        fallback_reason must be set when resolution_from_hierarchy is false; ExternalApiCompatibilityRecord symbol lists
        must be non-overlapping

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=5
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=4
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
        Perform a specific, focused operation within its owning class boundary.

        Responsibility:
            Performs a specific, focused operation within its owning class boundary. This method is the authoritative
            implementation for this piece of logic, ensuring callers access state or trigger behavior through a well-
            defined contract rather than manipulating internals directly.

        Reason for existence:
            This method is the information expert for this operation because it directly owns the relevant state fields
            and encapsulates all validation, error recording, and side-effect logic. Merging it elsewhere would scatter
            related concerns and force callers to duplicate precondition checks and error handling.

        Delegates:
            - ActiveObjectSet: Provides supporting functionality through a well-defined interface, delegating a focused
            sub-task to keep this entity cohesive and its responsibility boundary clean

        Cohesion:
            All functions, methods, and data within this entity operate on the same local state, share identical import
            dependencies and control flow patterns, and collectively implement a single cohesive responsibility rather
            than dispersing unrelated utilities across separate modules

        Separation:
            - _states: This entity is kept distinct from its peer to prevent callers from coupling to multiple domain
            boundaries at once, ensuring each concept can evolve independently without cascading changes across the
            codebase

        Main consumers:
            - run_access: Referenced by collection, runtime, and reporting layer plugins through the pytest_bdd.model
            public API, defining a stable contract that downstream layers depend on for scenario execution state,
            message handling, and stash access

        State and side effects:
            Maintains in-memory state via attrs-defined fields with factory defaults, performing no file I/O, network
            operations, or direct pytest stash access; stash interaction is delegated to StashAccess class methods for
            type-safe boundary enforcement

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=5
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=3
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
    Defines snapshot value objects for capturing runtime reporting context: ReportingContextSnapshot (records run_id, act.

    Responsibility:
        Defines snapshot value objects for capturing runtime reporting context: ReportingContextSnapshot (records
        run_id, active_set, stage, resolution source, and fallback reason for reporters) and
        ExternalApiCompatibilityRecord (tracks API surface changes across versions with changed/removed/renamed/additive
        symbol lists). Both are attrs-defined with slots=True and include as_dict() serialization for JSON output.

    Reason for existence:
        This code is the authoritative information expert for its domain boundary within the pytest-bdd model layer. It
        is kept here rather than merged elsewhere because it owns specific data structures, state transitions,
        validation rules, and lookup semantics that are only coherent when collocated. Analyzing imports and control
        flow confirms this module is the single source of truth for its owned concepts

    Delegates:
        - ActiveObjectSet: Provides supporting functionality through a well-defined interface, delegating a focused sub-
        task to keep this entity cohesive and its responsibility boundary clean

    Cohesion:
        All functions, methods, and data within this entity operate on the same local state, share identical import
        dependencies and control flow patterns, and collectively implement a single cohesive responsibility rather than
        dispersing unrelated utilities across separate modules

    Separation:
        - _states: This entity is kept distinct from its peer to prevent callers from coupling to multiple domain
        boundaries at once, ensuring each concept can evolve independently without cascading changes across the codebase

    Main consumers:
        - run_access: Referenced by collection, runtime, and reporting layer plugins through the pytest_bdd.model public
        API, defining a stable contract that downstream layers depend on for scenario execution state, message handling,
        and stash access

    State and side effects:
        Maintains in-memory state via attrs-defined fields with factory defaults, performing no file I/O, network
        operations, or direct pytest stash access; stash interaction is delegated to StashAccess class methods for type-
        safe boundary enforcement

    Invariants:
        - ReportingContextSnapshot.resolved_from_hierarchy must be true when resolved from Run hierarchy;
        fallback_reason must be set when resolution_from_hierarchy is false; ExternalApiCompatibilityRecord symbol lists
        must be non-overlapping

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=5
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=4
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
        Perform a specific, focused operation within its owning class boundary.

        Responsibility:
            Performs a specific, focused operation within its owning class boundary. This method is the authoritative
            implementation for this piece of logic, ensuring callers access state or trigger behavior through a well-
            defined contract rather than manipulating internals directly.

        Reason for existence:
            This method is the information expert for this operation because it directly owns the relevant state fields
            and encapsulates all validation, error recording, and side-effect logic. Merging it elsewhere would scatter
            related concerns and force callers to duplicate precondition checks and error handling.

        Delegates:
            - ActiveObjectSet: Provides supporting functionality through a well-defined interface, delegating a focused
            sub-task to keep this entity cohesive and its responsibility boundary clean

        Cohesion:
            All functions, methods, and data within this entity operate on the same local state, share identical import
            dependencies and control flow patterns, and collectively implement a single cohesive responsibility rather
            than dispersing unrelated utilities across separate modules

        Separation:
            - _states: This entity is kept distinct from its peer to prevent callers from coupling to multiple domain
            boundaries at once, ensuring each concept can evolve independently without cascading changes across the
            codebase

        Main consumers:
            - run_access: Referenced by collection, runtime, and reporting layer plugins through the pytest_bdd.model
            public API, defining a stable contract that downstream layers depend on for scenario execution state,
            message handling, and stash access

        State and side effects:
            Maintains in-memory state via attrs-defined fields with factory defaults, performing no file I/O, network
            operations, or direct pytest stash access; stash interaction is delegated to StashAccess class methods for
            type-safe boundary enforcement

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=5
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=3
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
