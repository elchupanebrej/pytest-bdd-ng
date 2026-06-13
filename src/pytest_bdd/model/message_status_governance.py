"""
Validate, convert, transport, and govern Cucumber Messages protocol envelopes within the pytest-bdd execution pipeline.

Responsibility:
    Validates, converts, transports, and governs Cucumber Messages protocol envelopes within the pytest-bdd execution
    pipeline. This module is the authoritative boundary for all envelope-level concerns including serialization
    profiles, schema validation via jsonschema, cross-worker xdist transport, status governance, capability
    classification, outcome mapping, baseline diffing, formatter adaptation, and heading validation. It enforces
    protocol correctness and ensures that all message producers and consumers operate on well-formed, compliant envelope
    data.

Reason for existence:
    This code is the authoritative information expert for its domain boundary within the pytest-bdd model layer. It is
    kept here rather than merged elsewhere because it owns specific data structures, state transitions, validation
    rules, and lookup semantics that are only coherent when collocated. Analyzing imports and control flow confirms this
    module is the single source of truth for its owned concepts

Delegates:
    - StashAccess: Provides supporting functionality through a well-defined interface, delegating a focused sub-task to
    keep this entity cohesive and its responsibility boundary clean

Cohesion:
    All functions, methods, and data within this entity operate on the same local state, share identical import
    dependencies and control flow patterns, and collectively implement a single cohesive responsibility rather than
    dispersing unrelated utilities across separate modules

Separation:
    - feature_binding: This entity is kept distinct from its peer to prevent callers from coupling to multiple domain
    boundaries at once, ensuring each concept can evolve independently without cascading changes across the codebase

Main consumers:
    - pickle_runner: Referenced by collection, runtime, and reporting layer plugins through the pytest_bdd.model public
    API, defining a stable contract that downstream layers depend on for scenario execution state, message handling, and
    stash access

State and side effects:
    Maintains in-memory state via attrs-defined fields with factory defaults, performing no file I/O, network
    operations, or direct pytest stash access; stash interaction is delegated to StashAccess class methods for type-safe
    boundary enforcement

Invariants:
    - Envelope payloads must contain exactly one non-None field matching a known PAYLOAD_KIND; stash keys must be unique
    per StashBound subclass; LifecycleObjectRef is_active flags must correctly reflect runtime state at all lifecycle
    stages

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

from typing import TYPE_CHECKING, Final, Literal

from attrs import frozen

if TYPE_CHECKING:
    from datetime import datetime

CapabilityStatus = Literal[
    "Implemented",
    "Partly-Applicable",
    "Non-Implementable",
    "Not-Acceptable",
    "Not-Applicable",
    "Pending",
]
LegacyCapabilityStatus = Literal[
    "done",
    "partly-applicable",
    "partially-applicable",
    "non-implementable",
    "not-acceptable",
    "not-applicable",
    "pending",
]
CapabilityStatusLike = CapabilityStatus | LegacyCapabilityStatus | str

CAPABILITY_STATUSES: Final[tuple[CapabilityStatus, ...]] = (
    "Implemented",
    "Partly-Applicable",
    "Non-Implementable",
    "Not-Acceptable",
    "Not-Applicable",
    "Pending",
)

NON_IMPLEMENTED_STATUSES: Final[set[CapabilityStatus]] = {
    "Partly-Applicable",
    "Non-Implementable",
    "Not-Acceptable",
    "Not-Applicable",
    "Pending",
}

MANDATORY_SCOPE_FORBIDDEN_STATUSES: Final[set[CapabilityStatus]] = {
    "Partly-Applicable",
    "Non-Implementable",
    "Not-Acceptable",
    "Not-Applicable",
}

MANDATORY_EVIDENCE_FIELDS: Final[tuple[str, ...]] = (
    "rationale",
    "decision_owner",
    "evidence_refs",
    "reviewed_at",
)

NON_IMPLEMENTABLE_REQUIRED_FIELDS: Final[tuple[str, ...]] = (
    "recheck_trigger",
    "hard_limitation",
)

FORBIDDEN_NON_IMPLEMENTABLE_PATTERNS: Final[tuple[str, ...]] = (
    "not implemented yet",
    "future work",
    "not observed in this test only",
)

RELEASE_BLOCKER_STATUSES: Final[set[CapabilityStatus]] = {
    "Pending",
    "Not-Acceptable",
}

LEGACY_STATUS_ALIASES: Final[dict[str, CapabilityStatus]] = {
    "done": "Implemented",
    "partly-applicable": "Partly-Applicable",
    "partially-applicable": "Partly-Applicable",
    "non-implementable": "Non-Implementable",
    "not-acceptable": "Not-Acceptable",
    "not-applicable": "Not-Applicable",
    "pending": "Pending",
}


@frozen
class CapabilityDecision:
    """
    Validate, convert, transport, and govern Cucumber Messages protocol envelopes within the pytest-bdd execution pipeline.

    Responsibility:
        Validates, converts, transports, and governs Cucumber Messages protocol envelopes within the pytest-bdd
        execution pipeline. This module is the authoritative boundary for all envelope-level concerns including
        serialization profiles, schema validation via jsonschema, cross-worker xdist transport, status governance,
        capability classification, outcome mapping, baseline diffing, formatter adaptation, and heading validation. It
        enforces protocol correctness and ensures that all message producers and consumers operate on well-formed,
        compliant envelope data.

    Reason for existence:
        This code is the authoritative information expert for its domain boundary within the pytest-bdd model layer. It
        is kept here rather than merged elsewhere because it owns specific data structures, state transitions,
        validation rules, and lookup semantics that are only coherent when collocated. Analyzing imports and control
        flow confirms this module is the single source of truth for its owned concepts

    Delegates:
        - StashAccess: Provides supporting functionality through a well-defined interface, delegating a focused sub-task
        to keep this entity cohesive and its responsibility boundary clean

    Cohesion:
        All functions, methods, and data within this entity operate on the same local state, share identical import
        dependencies and control flow patterns, and collectively implement a single cohesive responsibility rather than
        dispersing unrelated utilities across separate modules

    Separation:
        - feature_binding: This entity is kept distinct from its peer to prevent callers from coupling to multiple
        domain boundaries at once, ensuring each concept can evolve independently without cascading changes across the
        codebase

    Main consumers:
        - pickle_runner: Referenced by collection, runtime, and reporting layer plugins through the pytest_bdd.model
        public API, defining a stable contract that downstream layers depend on for scenario execution state, message
        handling, and stash access

    State and side effects:
        Maintains in-memory state via attrs-defined fields with factory defaults, performing no file I/O, network
        operations, or direct pytest stash access; stash interaction is delegated to StashAccess class methods for type-
        safe boundary enforcement

    Invariants:
        - Envelope payloads must contain exactly one non-None field matching a known PAYLOAD_KIND; stash keys must be
        unique per StashBound subclass; LifecycleObjectRef is_active flags must correctly reflect runtime state at all
        lifecycle stages

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

    capability_id: str
    status: CapabilityStatus
    release_target: str
    rationale: str | None = None
    hard_limitation: str | None = None
    decision_owner: str | None = None
    evidence_refs: tuple[str, ...] = ()
    reviewed_at: datetime | None = None
    recheck_trigger: str | None = None


@frozen
class DecisionValidationResult:
    """
    Validate, convert, transport, and govern Cucumber Messages protocol envelopes within the pytest-bdd execution pipeline.

    Responsibility:
        Validates, converts, transports, and governs Cucumber Messages protocol envelopes within the pytest-bdd
        execution pipeline. This module is the authoritative boundary for all envelope-level concerns including
        serialization profiles, schema validation via jsonschema, cross-worker xdist transport, status governance,
        capability classification, outcome mapping, baseline diffing, formatter adaptation, and heading validation. It
        enforces protocol correctness and ensures that all message producers and consumers operate on well-formed,
        compliant envelope data.

    Reason for existence:
        This code is the authoritative information expert for its domain boundary within the pytest-bdd model layer. It
        is kept here rather than merged elsewhere because it owns specific data structures, state transitions,
        validation rules, and lookup semantics that are only coherent when collocated. Analyzing imports and control
        flow confirms this module is the single source of truth for its owned concepts

    Delegates:
        - StashAccess: Provides supporting functionality through a well-defined interface, delegating a focused sub-task
        to keep this entity cohesive and its responsibility boundary clean

    Cohesion:
        All functions, methods, and data within this entity operate on the same local state, share identical import
        dependencies and control flow patterns, and collectively implement a single cohesive responsibility rather than
        dispersing unrelated utilities across separate modules

    Separation:
        - feature_binding: This entity is kept distinct from its peer to prevent callers from coupling to multiple
        domain boundaries at once, ensuring each concept can evolve independently without cascading changes across the
        codebase

    Main consumers:
        - pickle_runner: Referenced by collection, runtime, and reporting layer plugins through the pytest_bdd.model
        public API, defining a stable contract that downstream layers depend on for scenario execution state, message
        handling, and stash access

    State and side effects:
        Maintains in-memory state via attrs-defined fields with factory defaults, performing no file I/O, network
        operations, or direct pytest stash access; stash interaction is delegated to StashAccess class methods for type-
        safe boundary enforcement

    Invariants:
        - Envelope payloads must contain exactly one non-None field matching a known PAYLOAD_KIND; stash keys must be
        unique per StashBound subclass; LifecycleObjectRef is_active flags must correctly reflect runtime state at all
        lifecycle stages

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

    accepted: bool
    missing_required_evidence_fields: tuple[str, ...]
    violations: tuple[str, ...]


@frozen
class StatusUniquenessResult:
    """
    Validate, convert, transport, and govern Cucumber Messages protocol envelopes within the pytest-bdd execution pipeline.

    Responsibility:
        Validates, converts, transports, and governs Cucumber Messages protocol envelopes within the pytest-bdd
        execution pipeline. This module is the authoritative boundary for all envelope-level concerns including
        serialization profiles, schema validation via jsonschema, cross-worker xdist transport, status governance,
        capability classification, outcome mapping, baseline diffing, formatter adaptation, and heading validation. It
        enforces protocol correctness and ensures that all message producers and consumers operate on well-formed,
        compliant envelope data.

    Reason for existence:
        This code is the authoritative information expert for its domain boundary within the pytest-bdd model layer. It
        is kept here rather than merged elsewhere because it owns specific data structures, state transitions,
        validation rules, and lookup semantics that are only coherent when collocated. Analyzing imports and control
        flow confirms this module is the single source of truth for its owned concepts

    Delegates:
        - StashAccess: Provides supporting functionality through a well-defined interface, delegating a focused sub-task
        to keep this entity cohesive and its responsibility boundary clean

    Cohesion:
        All functions, methods, and data within this entity operate on the same local state, share identical import
        dependencies and control flow patterns, and collectively implement a single cohesive responsibility rather than
        dispersing unrelated utilities across separate modules

    Separation:
        - feature_binding: This entity is kept distinct from its peer to prevent callers from coupling to multiple
        domain boundaries at once, ensuring each concept can evolve independently without cascading changes across the
        codebase

    Main consumers:
        - pickle_runner: Referenced by collection, runtime, and reporting layer plugins through the pytest_bdd.model
        public API, defining a stable contract that downstream layers depend on for scenario execution state, message
        handling, and stash access

    State and side effects:
        Maintains in-memory state via attrs-defined fields with factory defaults, performing no file I/O, network
        operations, or direct pytest stash access; stash interaction is delegated to StashAccess class methods for type-
        safe boundary enforcement

    Invariants:
        - Envelope payloads must contain exactly one non-None field matching a known PAYLOAD_KIND; stash keys must be
        unique per StashBound subclass; LifecycleObjectRef is_active flags must correctly reflect runtime state at all
        lifecycle stages

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

    is_unique: bool
    duplicates: tuple[str, ...]


@frozen
class BlockerEvaluationResult:
    """
    Validate, convert, transport, and govern Cucumber Messages protocol envelopes within the pytest-bdd execution pipeline.

    Responsibility:
        Validates, converts, transports, and governs Cucumber Messages protocol envelopes within the pytest-bdd
        execution pipeline. This module is the authoritative boundary for all envelope-level concerns including
        serialization profiles, schema validation via jsonschema, cross-worker xdist transport, status governance,
        capability classification, outcome mapping, baseline diffing, formatter adaptation, and heading validation. It
        enforces protocol correctness and ensures that all message producers and consumers operate on well-formed,
        compliant envelope data.

    Reason for existence:
        This code is the authoritative information expert for its domain boundary within the pytest-bdd model layer. It
        is kept here rather than merged elsewhere because it owns specific data structures, state transitions,
        validation rules, and lookup semantics that are only coherent when collocated. Analyzing imports and control
        flow confirms this module is the single source of truth for its owned concepts

    Delegates:
        - StashAccess: Provides supporting functionality through a well-defined interface, delegating a focused sub-task
        to keep this entity cohesive and its responsibility boundary clean

    Cohesion:
        All functions, methods, and data within this entity operate on the same local state, share identical import
        dependencies and control flow patterns, and collectively implement a single cohesive responsibility rather than
        dispersing unrelated utilities across separate modules

    Separation:
        - feature_binding: This entity is kept distinct from its peer to prevent callers from coupling to multiple
        domain boundaries at once, ensuring each concept can evolve independently without cascading changes across the
        codebase

    Main consumers:
        - pickle_runner: Referenced by collection, runtime, and reporting layer plugins through the pytest_bdd.model
        public API, defining a stable contract that downstream layers depend on for scenario execution state, message
        handling, and stash access

    State and side effects:
        Maintains in-memory state via attrs-defined fields with factory defaults, performing no file I/O, network
        operations, or direct pytest stash access; stash interaction is delegated to StashAccess class methods for type-
        safe boundary enforcement

    Invariants:
        - Envelope payloads must contain exactly one non-None field matching a known PAYLOAD_KIND; stash keys must be
        unique per StashBound subclass; LifecycleObjectRef is_active flags must correctly reflect runtime state at all
        lifecycle stages

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

    unresolved_blocker_capability_ids: tuple[str, ...]
    deferred_capability_ids: tuple[str, ...]
    missing_decision_capability_ids: tuple[str, ...]

    @property
    def blocker_count(self) -> int:
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
            - StashAccess: Provides supporting functionality through a well-defined interface, delegating a focused sub-
            task to keep this entity cohesive and its responsibility boundary clean

        Cohesion:
            All functions, methods, and data within this entity operate on the same local state, share identical import
            dependencies and control flow patterns, and collectively implement a single cohesive responsibility rather
            than dispersing unrelated utilities across separate modules

        Separation:
            - feature_binding: This entity is kept distinct from its peer to prevent callers from coupling to multiple
            domain boundaries at once, ensuring each concept can evolve independently without cascading changes across
            the codebase

        Main consumers:
            - pickle_runner: Referenced by collection, runtime, and reporting layer plugins through the pytest_bdd.model
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
        return len(self.unresolved_blocker_capability_ids)


def _is_non_empty_text(value: object) -> bool:
    """
    Validate, convert, transport, and govern Cucumber Messages protocol envelopes within the pytest-bdd execution pipeline.

    Responsibility:
        Validates, converts, transports, and governs Cucumber Messages protocol envelopes within the pytest-bdd
        execution pipeline. This module is the authoritative boundary for all envelope-level concerns including
        serialization profiles, schema validation via jsonschema, cross-worker xdist transport, status governance,
        capability classification, outcome mapping, baseline diffing, formatter adaptation, and heading validation. It
        enforces protocol correctness and ensures that all message producers and consumers operate on well-formed,
        compliant envelope data.

    Reason for existence:
        This code is the authoritative information expert for its domain boundary within the pytest-bdd model layer. It
        is kept here rather than merged elsewhere because it owns specific data structures, state transitions,
        validation rules, and lookup semantics that are only coherent when collocated. Analyzing imports and control
        flow confirms this module is the single source of truth for its owned concepts

    Delegates:
        - StashAccess: Provides supporting functionality through a well-defined interface, delegating a focused sub-task
        to keep this entity cohesive and its responsibility boundary clean

    Cohesion:
        All functions, methods, and data within this entity operate on the same local state, share identical import
        dependencies and control flow patterns, and collectively implement a single cohesive responsibility rather than
        dispersing unrelated utilities across separate modules

    Separation:
        - feature_binding: This entity is kept distinct from its peer to prevent callers from coupling to multiple
        domain boundaries at once, ensuring each concept can evolve independently without cascading changes across the
        codebase

    Main consumers:
        - pickle_runner: Referenced by collection, runtime, and reporting layer plugins through the pytest_bdd.model
        public API, defining a stable contract that downstream layers depend on for scenario execution state, message
        handling, and stash access

    State and side effects:
        Maintains in-memory state via attrs-defined fields with factory defaults, performing no file I/O, network
        operations, or direct pytest stash access; stash interaction is delegated to StashAccess class methods for type-
        safe boundary enforcement

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=5
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=4
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=4
    """
    return isinstance(value, str) and bool(value.strip())


def normalize_capability_status(status: CapabilityStatusLike) -> CapabilityStatus | None:
    """
    Validate, convert, transport, and govern Cucumber Messages protocol envelopes within the pytest-bdd execution pipeline.

    Responsibility:
        Validates, converts, transports, and governs Cucumber Messages protocol envelopes within the pytest-bdd
        execution pipeline. This module is the authoritative boundary for all envelope-level concerns including
        serialization profiles, schema validation via jsonschema, cross-worker xdist transport, status governance,
        capability classification, outcome mapping, baseline diffing, formatter adaptation, and heading validation. It
        enforces protocol correctness and ensures that all message producers and consumers operate on well-formed,
        compliant envelope data.

    Reason for existence:
        This code is the authoritative information expert for its domain boundary within the pytest-bdd model layer. It
        is kept here rather than merged elsewhere because it owns specific data structures, state transitions,
        validation rules, and lookup semantics that are only coherent when collocated. Analyzing imports and control
        flow confirms this module is the single source of truth for its owned concepts

    Delegates:
        - StashAccess: Provides supporting functionality through a well-defined interface, delegating a focused sub-task
        to keep this entity cohesive and its responsibility boundary clean

    Cohesion:
        All functions, methods, and data within this entity operate on the same local state, share identical import
        dependencies and control flow patterns, and collectively implement a single cohesive responsibility rather than
        dispersing unrelated utilities across separate modules

    Separation:
        - feature_binding: This entity is kept distinct from its peer to prevent callers from coupling to multiple
        domain boundaries at once, ensuring each concept can evolve independently without cascading changes across the
        codebase

    Main consumers:
        - pickle_runner: Referenced by collection, runtime, and reporting layer plugins through the pytest_bdd.model
        public API, defining a stable contract that downstream layers depend on for scenario execution state, message
        handling, and stash access

    State and side effects:
        Maintains in-memory state via attrs-defined fields with factory defaults, performing no file I/O, network
        operations, or direct pytest stash access; stash interaction is delegated to StashAccess class methods for type-
        safe boundary enforcement

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=5
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=4
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=4
    """
    if status in CAPABILITY_STATUSES:
        return CAPABILITY_STATUSES[CAPABILITY_STATUSES.index(status)]
    return LEGACY_STATUS_ALIASES.get(str(status).strip().lower())


def missing_required_evidence_fields(decision: CapabilityDecision) -> tuple[str, ...]:
    """
    Validate, convert, transport, and govern Cucumber Messages protocol envelopes within the pytest-bdd execution pipeline.

    Responsibility:
        Validates, converts, transports, and governs Cucumber Messages protocol envelopes within the pytest-bdd
        execution pipeline. This module is the authoritative boundary for all envelope-level concerns including
        serialization profiles, schema validation via jsonschema, cross-worker xdist transport, status governance,
        capability classification, outcome mapping, baseline diffing, formatter adaptation, and heading validation. It
        enforces protocol correctness and ensures that all message producers and consumers operate on well-formed,
        compliant envelope data.

    Reason for existence:
        This code is the authoritative information expert for its domain boundary within the pytest-bdd model layer. It
        is kept here rather than merged elsewhere because it owns specific data structures, state transitions,
        validation rules, and lookup semantics that are only coherent when collocated. Analyzing imports and control
        flow confirms this module is the single source of truth for its owned concepts

    Delegates:
        - StashAccess: Provides supporting functionality through a well-defined interface, delegating a focused sub-task
        to keep this entity cohesive and its responsibility boundary clean

    Cohesion:
        All functions, methods, and data within this entity operate on the same local state, share identical import
        dependencies and control flow patterns, and collectively implement a single cohesive responsibility rather than
        dispersing unrelated utilities across separate modules

    Separation:
        - feature_binding: This entity is kept distinct from its peer to prevent callers from coupling to multiple
        domain boundaries at once, ensuring each concept can evolve independently without cascading changes across the
        codebase

    Main consumers:
        - pickle_runner: Referenced by collection, runtime, and reporting layer plugins through the pytest_bdd.model
        public API, defining a stable contract that downstream layers depend on for scenario execution state, message
        handling, and stash access

    State and side effects:
        Maintains in-memory state via attrs-defined fields with factory defaults, performing no file I/O, network
        operations, or direct pytest stash access; stash interaction is delegated to StashAccess class methods for type-
        safe boundary enforcement

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=5
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=4
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=4
    """
    status = normalize_capability_status(decision.status)
    if status is None or status not in NON_IMPLEMENTED_STATUSES:
        return ()

    missing: list[str] = []
    if not _is_non_empty_text(decision.rationale):
        missing.append("rationale")
    if not _is_non_empty_text(decision.decision_owner):
        missing.append("decision_owner")
    if not decision.evidence_refs:
        missing.append("evidence_refs")
    if decision.reviewed_at is None:
        missing.append("reviewed_at")
    if status == "Non-Implementable":
        if not _is_non_empty_text(decision.recheck_trigger):
            missing.append("recheck_trigger")
        if not _is_non_empty_text(decision.hard_limitation):
            missing.append("hard_limitation")
    return tuple(missing)


def validate_non_implementable_policy(decision: CapabilityDecision) -> tuple[str, ...]:
    """
    Validate, convert, transport, and govern Cucumber Messages protocol envelopes within the pytest-bdd execution pipeline.

    Responsibility:
        Validates, converts, transports, and governs Cucumber Messages protocol envelopes within the pytest-bdd
        execution pipeline. This module is the authoritative boundary for all envelope-level concerns including
        serialization profiles, schema validation via jsonschema, cross-worker xdist transport, status governance,
        capability classification, outcome mapping, baseline diffing, formatter adaptation, and heading validation. It
        enforces protocol correctness and ensures that all message producers and consumers operate on well-formed,
        compliant envelope data.

    Reason for existence:
        This code is the authoritative information expert for its domain boundary within the pytest-bdd model layer. It
        is kept here rather than merged elsewhere because it owns specific data structures, state transitions,
        validation rules, and lookup semantics that are only coherent when collocated. Analyzing imports and control
        flow confirms this module is the single source of truth for its owned concepts

    Delegates:
        - StashAccess: Provides supporting functionality through a well-defined interface, delegating a focused sub-task
        to keep this entity cohesive and its responsibility boundary clean

    Cohesion:
        All functions, methods, and data within this entity operate on the same local state, share identical import
        dependencies and control flow patterns, and collectively implement a single cohesive responsibility rather than
        dispersing unrelated utilities across separate modules

    Separation:
        - feature_binding: This entity is kept distinct from its peer to prevent callers from coupling to multiple
        domain boundaries at once, ensuring each concept can evolve independently without cascading changes across the
        codebase

    Main consumers:
        - pickle_runner: Referenced by collection, runtime, and reporting layer plugins through the pytest_bdd.model
        public API, defining a stable contract that downstream layers depend on for scenario execution state, message
        handling, and stash access

    State and side effects:
        Maintains in-memory state via attrs-defined fields with factory defaults, performing no file I/O, network
        operations, or direct pytest stash access; stash interaction is delegated to StashAccess class methods for type-
        safe boundary enforcement

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=5
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=4
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=4
    """
    status = normalize_capability_status(decision.status)
    if status != "Non-Implementable":
        return ()

    rationale = decision.rationale or ""
    hard_limitation = decision.hard_limitation or ""
    combined_text = f"{rationale}\n{hard_limitation}".lower()

    return tuple(
        f"non-implementable rationale uses forbidden phrase: '{pattern}'"
        for pattern in FORBIDDEN_NON_IMPLEMENTABLE_PATTERNS
        if pattern in combined_text
    )


def validate_partly_applicable_policy(decision: CapabilityDecision) -> tuple[str, ...]:
    """
    Validate, convert, transport, and govern Cucumber Messages protocol envelopes within the pytest-bdd execution pipeline.

    Responsibility:
        Validates, converts, transports, and governs Cucumber Messages protocol envelopes within the pytest-bdd
        execution pipeline. This module is the authoritative boundary for all envelope-level concerns including
        serialization profiles, schema validation via jsonschema, cross-worker xdist transport, status governance,
        capability classification, outcome mapping, baseline diffing, formatter adaptation, and heading validation. It
        enforces protocol correctness and ensures that all message producers and consumers operate on well-formed,
        compliant envelope data.

    Reason for existence:
        This code is the authoritative information expert for its domain boundary within the pytest-bdd model layer. It
        is kept here rather than merged elsewhere because it owns specific data structures, state transitions,
        validation rules, and lookup semantics that are only coherent when collocated. Analyzing imports and control
        flow confirms this module is the single source of truth for its owned concepts

    Delegates:
        - StashAccess: Provides supporting functionality through a well-defined interface, delegating a focused sub-task
        to keep this entity cohesive and its responsibility boundary clean

    Cohesion:
        All functions, methods, and data within this entity operate on the same local state, share identical import
        dependencies and control flow patterns, and collectively implement a single cohesive responsibility rather than
        dispersing unrelated utilities across separate modules

    Separation:
        - feature_binding: This entity is kept distinct from its peer to prevent callers from coupling to multiple
        domain boundaries at once, ensuring each concept can evolve independently without cascading changes across the
        codebase

    Main consumers:
        - pickle_runner: Referenced by collection, runtime, and reporting layer plugins through the pytest_bdd.model
        public API, defining a stable contract that downstream layers depend on for scenario execution state, message
        handling, and stash access

    State and side effects:
        Maintains in-memory state via attrs-defined fields with factory defaults, performing no file I/O, network
        operations, or direct pytest stash access; stash interaction is delegated to StashAccess class methods for type-
        safe boundary enforcement

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=5
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=4
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=4
    """
    status = normalize_capability_status(decision.status)
    if status != "Partly-Applicable":
        return ()

    rationale = (decision.rationale or "").lower()
    if "language" in rationale and ("model" in rationale or "runtime" in rationale):
        return ()
    return (
        (
            "partly-applicable rationale must explain language/runtime model mismatch "
            "(for example: no native language-equivalent model in current runtime)"
        ),
    )


def validate_capability_decision(decision: CapabilityDecision) -> DecisionValidationResult:
    """
    Validate, convert, transport, and govern Cucumber Messages protocol envelopes within the pytest-bdd execution pipeline.

    Responsibility:
        Validates, converts, transports, and governs Cucumber Messages protocol envelopes within the pytest-bdd
        execution pipeline. This module is the authoritative boundary for all envelope-level concerns including
        serialization profiles, schema validation via jsonschema, cross-worker xdist transport, status governance,
        capability classification, outcome mapping, baseline diffing, formatter adaptation, and heading validation. It
        enforces protocol correctness and ensures that all message producers and consumers operate on well-formed,
        compliant envelope data.

    Reason for existence:
        This code is the authoritative information expert for its domain boundary within the pytest-bdd model layer. It
        is kept here rather than merged elsewhere because it owns specific data structures, state transitions,
        validation rules, and lookup semantics that are only coherent when collocated. Analyzing imports and control
        flow confirms this module is the single source of truth for its owned concepts

    Delegates:
        - StashAccess: Provides supporting functionality through a well-defined interface, delegating a focused sub-task
        to keep this entity cohesive and its responsibility boundary clean

    Cohesion:
        All functions, methods, and data within this entity operate on the same local state, share identical import
        dependencies and control flow patterns, and collectively implement a single cohesive responsibility rather than
        dispersing unrelated utilities across separate modules

    Separation:
        - feature_binding: This entity is kept distinct from its peer to prevent callers from coupling to multiple
        domain boundaries at once, ensuring each concept can evolve independently without cascading changes across the
        codebase

    Main consumers:
        - pickle_runner: Referenced by collection, runtime, and reporting layer plugins through the pytest_bdd.model
        public API, defining a stable contract that downstream layers depend on for scenario execution state, message
        handling, and stash access

    State and side effects:
        Maintains in-memory state via attrs-defined fields with factory defaults, performing no file I/O, network
        operations, or direct pytest stash access; stash interaction is delegated to StashAccess class methods for type-
        safe boundary enforcement

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=5
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=4
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=4
    """
    violations: list[str] = []
    status = normalize_capability_status(decision.status)
    if status is None:
        violations.append(f"Unknown status: {decision.status}")
    violations.extend(validate_non_implementable_policy(decision))
    violations.extend(validate_partly_applicable_policy(decision))
    missing = missing_required_evidence_fields(decision)
    accepted = not violations and not missing
    return DecisionValidationResult(
        accepted=accepted,
        missing_required_evidence_fields=missing,
        violations=tuple(violations),
    )


def validate_mandatory_scope_decision(
    decision: CapabilityDecision,
    *,
    mandatory_capability_ids: set[str],
) -> tuple[str, ...]:
    """
    Validate, convert, transport, and govern Cucumber Messages protocol envelopes within the pytest-bdd execution pipeline.

    Responsibility:
        Validates, converts, transports, and governs Cucumber Messages protocol envelopes within the pytest-bdd
        execution pipeline. This module is the authoritative boundary for all envelope-level concerns including
        serialization profiles, schema validation via jsonschema, cross-worker xdist transport, status governance,
        capability classification, outcome mapping, baseline diffing, formatter adaptation, and heading validation. It
        enforces protocol correctness and ensures that all message producers and consumers operate on well-formed,
        compliant envelope data.

    Reason for existence:
        This code is the authoritative information expert for its domain boundary within the pytest-bdd model layer. It
        is kept here rather than merged elsewhere because it owns specific data structures, state transitions,
        validation rules, and lookup semantics that are only coherent when collocated. Analyzing imports and control
        flow confirms this module is the single source of truth for its owned concepts

    Delegates:
        - StashAccess: Provides supporting functionality through a well-defined interface, delegating a focused sub-task
        to keep this entity cohesive and its responsibility boundary clean

    Cohesion:
        All functions, methods, and data within this entity operate on the same local state, share identical import
        dependencies and control flow patterns, and collectively implement a single cohesive responsibility rather than
        dispersing unrelated utilities across separate modules

    Separation:
        - feature_binding: This entity is kept distinct from its peer to prevent callers from coupling to multiple
        domain boundaries at once, ensuring each concept can evolve independently without cascading changes across the
        codebase

    Main consumers:
        - pickle_runner: Referenced by collection, runtime, and reporting layer plugins through the pytest_bdd.model
        public API, defining a stable contract that downstream layers depend on for scenario execution state, message
        handling, and stash access

    State and side effects:
        Maintains in-memory state via attrs-defined fields with factory defaults, performing no file I/O, network
        operations, or direct pytest stash access; stash interaction is delegated to StashAccess class methods for type-
        safe boundary enforcement

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=5
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=4
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=4
    """
    if decision.capability_id not in mandatory_capability_ids:
        return ()
    status = normalize_capability_status(decision.status)
    if status in MANDATORY_SCOPE_FORBIDDEN_STATUSES:
        message = (
            "mandatory scope capabilities cannot use deferred statuses "
            f"({', '.join(sorted(MANDATORY_SCOPE_FORBIDDEN_STATUSES))}): {decision.capability_id} -> {status}"
        )
        return (message,)
    return ()


def ensure_single_status_per_capability(decisions: list[CapabilityDecision]) -> StatusUniquenessResult:
    """
    Validate, convert, transport, and govern Cucumber Messages protocol envelopes within the pytest-bdd execution pipeline.

    Responsibility:
        Validates, converts, transports, and governs Cucumber Messages protocol envelopes within the pytest-bdd
        execution pipeline. This module is the authoritative boundary for all envelope-level concerns including
        serialization profiles, schema validation via jsonschema, cross-worker xdist transport, status governance,
        capability classification, outcome mapping, baseline diffing, formatter adaptation, and heading validation. It
        enforces protocol correctness and ensures that all message producers and consumers operate on well-formed,
        compliant envelope data.

    Reason for existence:
        This code is the authoritative information expert for its domain boundary within the pytest-bdd model layer. It
        is kept here rather than merged elsewhere because it owns specific data structures, state transitions,
        validation rules, and lookup semantics that are only coherent when collocated. Analyzing imports and control
        flow confirms this module is the single source of truth for its owned concepts

    Delegates:
        - StashAccess: Provides supporting functionality through a well-defined interface, delegating a focused sub-task
        to keep this entity cohesive and its responsibility boundary clean

    Cohesion:
        All functions, methods, and data within this entity operate on the same local state, share identical import
        dependencies and control flow patterns, and collectively implement a single cohesive responsibility rather than
        dispersing unrelated utilities across separate modules

    Separation:
        - feature_binding: This entity is kept distinct from its peer to prevent callers from coupling to multiple
        domain boundaries at once, ensuring each concept can evolve independently without cascading changes across the
        codebase

    Main consumers:
        - pickle_runner: Referenced by collection, runtime, and reporting layer plugins through the pytest_bdd.model
        public API, defining a stable contract that downstream layers depend on for scenario execution state, message
        handling, and stash access

    State and side effects:
        Maintains in-memory state via attrs-defined fields with factory defaults, performing no file I/O, network
        operations, or direct pytest stash access; stash interaction is delegated to StashAccess class methods for type-
        safe boundary enforcement

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=5
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=4
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=4
    """
    seen: set[tuple[str, str]] = set()
    duplicates: list[str] = []
    for decision in decisions:
        uniqueness_key = (decision.capability_id, decision.release_target)
        if uniqueness_key in seen:
            duplicates.append(f"{decision.capability_id}@{decision.release_target}")
        else:
            seen.add(uniqueness_key)
    return StatusUniquenessResult(is_unique=not duplicates, duplicates=tuple(sorted(set(duplicates))))


def is_release_blocker_status(status: CapabilityStatus) -> bool:
    """
    Validate, convert, transport, and govern Cucumber Messages protocol envelopes within the pytest-bdd execution pipeline.

    Responsibility:
        Validates, converts, transports, and governs Cucumber Messages protocol envelopes within the pytest-bdd
        execution pipeline. This module is the authoritative boundary for all envelope-level concerns including
        serialization profiles, schema validation via jsonschema, cross-worker xdist transport, status governance,
        capability classification, outcome mapping, baseline diffing, formatter adaptation, and heading validation. It
        enforces protocol correctness and ensures that all message producers and consumers operate on well-formed,
        compliant envelope data.

    Reason for existence:
        This code is the authoritative information expert for its domain boundary within the pytest-bdd model layer. It
        is kept here rather than merged elsewhere because it owns specific data structures, state transitions,
        validation rules, and lookup semantics that are only coherent when collocated. Analyzing imports and control
        flow confirms this module is the single source of truth for its owned concepts

    Delegates:
        - StashAccess: Provides supporting functionality through a well-defined interface, delegating a focused sub-task
        to keep this entity cohesive and its responsibility boundary clean

    Cohesion:
        All functions, methods, and data within this entity operate on the same local state, share identical import
        dependencies and control flow patterns, and collectively implement a single cohesive responsibility rather than
        dispersing unrelated utilities across separate modules

    Separation:
        - feature_binding: This entity is kept distinct from its peer to prevent callers from coupling to multiple
        domain boundaries at once, ensuring each concept can evolve independently without cascading changes across the
        codebase

    Main consumers:
        - pickle_runner: Referenced by collection, runtime, and reporting layer plugins through the pytest_bdd.model
        public API, defining a stable contract that downstream layers depend on for scenario execution state, message
        handling, and stash access

    State and side effects:
        Maintains in-memory state via attrs-defined fields with factory defaults, performing no file I/O, network
        operations, or direct pytest stash access; stash interaction is delegated to StashAccess class methods for type-
        safe boundary enforcement

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=5
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=4
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=4
    """
    return status in RELEASE_BLOCKER_STATUSES


def evaluate_release_blockers(
    decisions: list[CapabilityDecision],
    *,
    relevant_capability_ids: tuple[str, ...] = (),
) -> BlockerEvaluationResult:
    """
    Validate, convert, transport, and govern Cucumber Messages protocol envelopes within the pytest-bdd execution pipeline.

    Responsibility:
        Validates, converts, transports, and governs Cucumber Messages protocol envelopes within the pytest-bdd
        execution pipeline. This module is the authoritative boundary for all envelope-level concerns including
        serialization profiles, schema validation via jsonschema, cross-worker xdist transport, status governance,
        capability classification, outcome mapping, baseline diffing, formatter adaptation, and heading validation. It
        enforces protocol correctness and ensures that all message producers and consumers operate on well-formed,
        compliant envelope data.

    Reason for existence:
        This code is the authoritative information expert for its domain boundary within the pytest-bdd model layer. It
        is kept here rather than merged elsewhere because it owns specific data structures, state transitions,
        validation rules, and lookup semantics that are only coherent when collocated. Analyzing imports and control
        flow confirms this module is the single source of truth for its owned concepts

    Delegates:
        - StashAccess: Provides supporting functionality through a well-defined interface, delegating a focused sub-task
        to keep this entity cohesive and its responsibility boundary clean

    Cohesion:
        All functions, methods, and data within this entity operate on the same local state, share identical import
        dependencies and control flow patterns, and collectively implement a single cohesive responsibility rather than
        dispersing unrelated utilities across separate modules

    Separation:
        - feature_binding: This entity is kept distinct from its peer to prevent callers from coupling to multiple
        domain boundaries at once, ensuring each concept can evolve independently without cascading changes across the
        codebase

    Main consumers:
        - pickle_runner: Referenced by collection, runtime, and reporting layer plugins through the pytest_bdd.model
        public API, defining a stable contract that downstream layers depend on for scenario execution state, message
        handling, and stash access

    State and side effects:
        Maintains in-memory state via attrs-defined fields with factory defaults, performing no file I/O, network
        operations, or direct pytest stash access; stash interaction is delegated to StashAccess class methods for type-
        safe boundary enforcement

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=5
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=4
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=4
    """
    index = {decision.capability_id: decision for decision in decisions}
    blocker_ids: set[str] = set()
    deferred_ids: set[str] = set()
    missing_ids: set[str] = set()

    for decision in decisions:
        status = normalize_capability_status(decision.status)
        if status is None:
            blocker_ids.add(decision.capability_id)
            continue
        if is_release_blocker_status(status):
            blocker_ids.add(decision.capability_id)
        elif status in {"Partly-Applicable", "Non-Implementable", "Not-Applicable"}:
            deferred_ids.add(decision.capability_id)

    for capability_id in relevant_capability_ids:
        if capability_id not in index:
            missing_ids.add(capability_id)
            blocker_ids.add(capability_id)

    return BlockerEvaluationResult(
        unresolved_blocker_capability_ids=tuple(sorted(blocker_ids)),
        deferred_capability_ids=tuple(sorted(deferred_ids)),
        missing_decision_capability_ids=tuple(sorted(missing_ids)),
    )
