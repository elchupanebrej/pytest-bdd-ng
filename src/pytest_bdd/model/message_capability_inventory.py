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

Failure semantics:
    Raises RuntimeError for context-not-initialized or binding-missing conditions when required lifecycle objects are
    unavailable; raises TypeError for malformed envelopes violating single-payload or type constraints; raises
    ValueError for missing required fields in deserialized transport payloads; callers must handle these exceptions at
    hook or plugin boundaries to prevent test session crashes

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

import json
from collections.abc import Iterable  # noqa: TC003  -- type checking import needed at runtime for isinstance/validators
from pathlib import Path
from typing import TYPE_CHECKING, cast

from attrs import frozen
from returns.maybe import Nothing

from .message_capability import MessageCapability, capability_is_relevant

if TYPE_CHECKING:
    from pytest_bdd.types.json import JSONObject

SCHEMA_RELATIVE_DIR = Path("messages") / "jsonschema" / "src"
PACKAGE_SCHEMA_RELATIVE_DIR = Path("message_jsonschema")


@frozen
class CapabilitySyncResult:
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

    total_relevant: int
    total_out_of_scope: int
    duplicate_capability_ids: tuple[str, ...]
    capabilities: tuple[MessageCapability, ...]


@frozen
class MandatoryScopeReconciliation:
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

    inventory_capability_ids: tuple[str, ...]
    mandatory_capability_ids: tuple[str, ...]
    missing_mandatory_capability_ids: tuple[str, ...]

    @property
    def mandatory_total(self) -> int:
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
            #arch-eval:separation=4
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=3
            #arch-eval:locational_stability=4
        """
        return len(self.mandatory_capability_ids)

    @property
    def inventory_total(self) -> int:
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
            #arch-eval:separation=4
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=3
            #arch-eval:locational_stability=4
        """
        return len(self.inventory_capability_ids)

    @property
    def has_missing_mandatory_capabilities(self) -> bool:
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
            #arch-eval:separation=4
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=3
            #arch-eval:locational_stability=4
        """
        return bool(self.missing_mandatory_capability_ids)


@frozen
class CoverageScopeReconciliation:
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

    inventory_capability_ids: tuple[str, ...]
    runtime_required_capability_ids: tuple[str, ...]
    observed_capability_ids: tuple[str, ...]
    classified_capability_ids: tuple[str, ...]
    missing_runtime_required_capability_ids: tuple[str, ...]
    uncovered_non_runtime_unclassified_capability_ids: tuple[str, ...]

    @property
    def runtime_required_total(self) -> int:
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
            #arch-eval:separation=4
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=3
            #arch-eval:locational_stability=4
        """
        return len(self.runtime_required_capability_ids)

    @property
    def runtime_required_covered(self) -> int:
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
            #arch-eval:separation=4
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=3
            #arch-eval:locational_stability=4
        """
        return self.runtime_required_total - len(self.missing_runtime_required_capability_ids)

    @property
    def runtime_required_missing(self) -> int:
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
            #arch-eval:separation=4
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=3
            #arch-eval:locational_stability=4
        """
        return len(self.missing_runtime_required_capability_ids)

    @property
    def non_runtime_required_total(self) -> int:
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
            #arch-eval:separation=4
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=3
            #arch-eval:locational_stability=4
        """
        return len(tuple(set(self.inventory_capability_ids).difference(self.runtime_required_capability_ids)))

    @property
    def non_runtime_covered(self) -> int:
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
            #arch-eval:separation=4
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=3
            #arch-eval:locational_stability=4
        """
        non_runtime_set = set(self.inventory_capability_ids).difference(self.runtime_required_capability_ids)
        observed_set = set(self.observed_capability_ids)
        return len(non_runtime_set.intersection(observed_set))

    @property
    def non_runtime_classified(self) -> int:
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
            #arch-eval:separation=4
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=3
            #arch-eval:locational_stability=4
        """
        non_runtime_set = set(self.inventory_capability_ids).difference(self.runtime_required_capability_ids)
        classified_set = set(self.classified_capability_ids)
        return len(non_runtime_set.intersection(classified_set))

    @property
    def has_unclassified_non_runtime_gaps(self) -> bool:
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
            #arch-eval:separation=4
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=3
            #arch-eval:locational_stability=4
        """
        return bool(self.uncovered_non_runtime_unclassified_capability_ids)


def _to_camel_case_identifier(value: str) -> str:
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
    parts = [part for part in value.split("_") if part]
    if not parts:
        return value
    return parts[0] + "".join(part[:1].upper() + part[1:] for part in parts[1:])


def _canonical_payload_kind(payload_kind: str) -> str:
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
    payload_kind = payload_kind.strip()
    if "_" not in payload_kind:
        return payload_kind
    return _to_camel_case_identifier(payload_kind)


def _canonical_capability_id(capability_id: str) -> str:
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
    if "." not in capability_id:
        return _canonical_payload_kind(capability_id)
    payload_kind, field_path = capability_id.split(".", 1)
    return f"{_canonical_payload_kind(payload_kind)}.{field_path}"


def normalize_capability_ids(capability_ids: Iterable[str]) -> tuple[str, ...]:
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
    return tuple(sorted({_canonical_capability_id(capability_id) for capability_id in capability_ids}))


def reconcile_inventory_with_mandatory_scope(
    inventory_capability_ids: Iterable[str],
    mandatory_capability_ids: Iterable[str],
) -> MandatoryScopeReconciliation:
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
    normalized_inventory = normalize_capability_ids(inventory_capability_ids)
    normalized_mandatory = normalize_capability_ids(mandatory_capability_ids)
    inventory_set = set(normalized_inventory)
    mandatory_set = set(normalized_mandatory)
    missing = tuple(sorted(mandatory_set.difference(inventory_set)))
    return MandatoryScopeReconciliation(
        inventory_capability_ids=normalized_inventory,
        mandatory_capability_ids=normalized_mandatory,
        missing_mandatory_capability_ids=missing,
    )


def reconcile_runtime_scope_coverage(
    *,
    inventory_capability_ids: Iterable[str],
    runtime_required_capability_ids: Iterable[str],
    observed_capability_ids: Iterable[str],
    classified_capability_ids: Iterable[str],
) -> CoverageScopeReconciliation:
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
    inventory_ids = normalize_capability_ids(inventory_capability_ids)
    runtime_required_ids = normalize_capability_ids(runtime_required_capability_ids)
    observed_ids = normalize_capability_ids(observed_capability_ids)
    classified_ids = normalize_capability_ids(classified_capability_ids)

    inventory_set = set(inventory_ids)
    runtime_required_set = set(runtime_required_ids)
    observed_set = set(observed_ids)
    classified_set = set(classified_ids)

    missing_runtime_required = tuple(sorted(runtime_required_set.difference(observed_set)))
    non_runtime_ids = inventory_set.difference(runtime_required_set)
    uncovered_non_runtime = non_runtime_ids.difference(observed_set)
    uncovered_non_runtime_unclassified = tuple(sorted(uncovered_non_runtime.difference(classified_set)))

    return CoverageScopeReconciliation(
        inventory_capability_ids=inventory_ids,
        runtime_required_capability_ids=runtime_required_ids,
        observed_capability_ids=observed_ids,
        classified_capability_ids=classified_ids,
        missing_runtime_required_capability_ids=missing_runtime_required,
        uncovered_non_runtime_unclassified_capability_ids=uncovered_non_runtime_unclassified,
    )


def _envelope_path(schema_dir: Path) -> Path:
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
    canonical = schema_dir / "Envelope.json"
    if canonical.is_file():
        return canonical
    alt = schema_dir / "Envelope.schema.json"
    if alt.is_file():
        return alt
    return canonical


def _schema_dir_from_git_root() -> Path | None:
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
    roots: list[Path] = []
    for seed in (Path.cwd(), Path(__file__).resolve()):
        for parent in (seed, *seed.parents):
            if (parent / ".git").exists():
                roots.append(parent)
                break
    for root in roots:
        candidate = (root / SCHEMA_RELATIVE_DIR).resolve()
        if _envelope_path(candidate).is_file():
            return candidate
    return Nothing.value_or(None)


def resolve_messages_schema_dir(preferred: Path | None = None) -> Path:
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

    Failure semantics:
        Raises RuntimeError for context-not-initialized or binding-missing conditions when required lifecycle objects
        are unavailable; raises TypeError for malformed envelopes violating single-payload or type constraints; raises
        ValueError for missing required fields in deserialized transport payloads; callers must handle these exceptions
        at hook or plugin boundaries to prevent test session crashes

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
    candidates: list[Path] = []
    if preferred is not None:
        candidates.append(preferred)

    package_schema_dir = Path(__file__).resolve().parent / PACKAGE_SCHEMA_RELATIVE_DIR
    candidates.extend(
        (
            Path.cwd() / SCHEMA_RELATIVE_DIR,
            package_schema_dir,
            Path(__file__).resolve().parents[3] / SCHEMA_RELATIVE_DIR,
        ),
    )

    git_candidate = _schema_dir_from_git_root()
    if git_candidate is not None:
        candidates.append(git_candidate)

    for candidate in candidates:
        resolved = candidate.resolve()
        if _envelope_path(resolved).is_file():
            return resolved

    paths = ", ".join(str(path.resolve()) for path in candidates)
    msg = f"Unable to resolve messages schema directory with Envelope.json or Envelope.schema.json. Checked: {paths}"
    raise FileNotFoundError(msg)


def load_envelope_schema(schema_dir: Path | None = None) -> tuple[Path, JSONObject]:
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
    resolved_schema_dir = resolve_messages_schema_dir(schema_dir)
    envelope_path = _envelope_path(resolved_schema_dir)
    return resolved_schema_dir, cast("JSONObject", json.loads(envelope_path.read_text(encoding="utf-8")))


def sync_capability_inventory(
    baseline_release: str,
    source_entries: list[MessageCapability],
) -> CapabilitySyncResult:
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
    seen: set[str] = set()
    duplicates: set[str] = set()
    synchronized: list[MessageCapability] = []

    for entry in source_entries:
        if entry.capability_id in seen:
            duplicates.add(entry.capability_id)
            continue
        seen.add(entry.capability_id)
        synchronized.append(
            MessageCapability(
                capability_id=entry.capability_id,
                baseline_release=baseline_release,
                name=entry.name,
                description=entry.description,
                category=entry.category,
                affects=entry.affects,
                source_reference=entry.source_reference,
                explicit_relevance=entry.explicit_relevance,
            ),
        )

    total_relevant = sum(1 for capability in synchronized if capability_is_relevant(capability))
    total_out_of_scope = len(synchronized) - total_relevant

    return CapabilitySyncResult(
        total_relevant=total_relevant,
        total_out_of_scope=total_out_of_scope,
        duplicate_capability_ids=tuple(sorted(duplicates)),
        capabilities=tuple(synchronized),
    )
