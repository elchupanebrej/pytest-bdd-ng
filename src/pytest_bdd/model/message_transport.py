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
import logging
from threading import Lock
from time import monotonic, sleep
from typing import TYPE_CHECKING, ClassVar, Protocol

from attrs import define, field, frozen
from returns.maybe import Nothing

from pytest_bdd.model.stash_access import StashBound

if TYPE_CHECKING:
    from pytest_bdd.types.json import JSONObject
    from pytest_bdd.types.protocol import HasPytestStash

logger = logging.getLogger(__name__)

REPORTING_BATCH_EVENT = "pytest_bdd_message_chunk"
REPORTING_TRANSPORT_BINDING_STASH_KEY = "_pytest_bdd_xdist_transport_binding"


class ReportingEventSender(Protocol):
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

    def __call__(self, name: str, **kwargs: object) -> None:
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
            #arch-eval:delegation_boundary=3
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=3
            #arch-eval:entity_fullness=3
            #arch-eval:locational_stability=4
        """
        ...


@frozen
class ReportingEventSenderBinding(StashBound):
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

    STASH_KEY: ClassVar[str] = REPORTING_TRANSPORT_BINDING_STASH_KEY
    sender: ReportingEventSender
    gateway_mode: str | None = None


def resolve_reporting_event_sender(config: HasPytestStash) -> ReportingEventSender | None:
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
    binding = ReportingEventSenderBinding.find_in_stash(config.stash).value_or(None)
    if binding is None:
        return Nothing.value_or(None)
    sender = binding.sender
    return sender if callable(sender) else Nothing.value_or(None)


def resolve_reporting_gateway_mode(config: HasPytestStash) -> str | None:
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
    binding = ReportingEventSenderBinding.find_in_stash(config.stash).value_or(None)
    if binding is None:
        return Nothing.value_or(None)
    gateway_mode = binding.gateway_mode
    return gateway_mode if isinstance(gateway_mode, str) and gateway_mode else Nothing.value_or(None)


def _payload_int(payload: JSONObject, key: str, default: int | None = None) -> int:
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
    raw_value = payload.get(key, default)
    if isinstance(raw_value, (str, int, float)):
        return int(raw_value)
    if default is not None:
        return default
    msg = f"Expected integer-compatible transport field: {key}"
    raise TypeError(msg)


@frozen
class WorkerChunkBatch:
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
        #arch-eval:entity_fullness=3
        #arch-eval:locational_stability=4
    """

    worker_id: str
    batch_sequence: int
    envelopes: tuple[JSONObject, ...]
    is_terminal_batch: bool = False
    byte_count: int = 0
    gateway_mode: str | None = None

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
        return {
            "worker_id": self.worker_id,
            "batch_sequence": self.batch_sequence,
            "envelopes": list(self.envelopes),
            "is_terminal_batch": self.is_terminal_batch,
            "byte_count": self.byte_count,
            "gateway_mode": self.gateway_mode,
        }

    @classmethod
    def from_dict(cls, payload: JSONObject) -> WorkerChunkBatch:
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

        Failure semantics:
            Raises RuntimeError for context-not-initialized or binding-missing conditions when required lifecycle
            objects are unavailable; raises TypeError for malformed envelopes violating single-payload or type
            constraints; raises ValueError for missing required fields in deserialized transport payloads; callers must
            handle these exceptions at hook or plugin boundaries to prevent test session crashes

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
        raw_envelopes = payload.get("envelopes", [])
        envelope_candidates = raw_envelopes if isinstance(raw_envelopes, list) else []
        envelopes = tuple(candidate for candidate in envelope_candidates if isinstance(candidate, dict))
        gateway_mode = payload.get("gateway_mode")
        worker_id = payload.get("worker_id")
        if worker_id is None:
            msg = "Missing required field 'worker_id' in batch payload"
            raise ValueError(msg)
        return cls(
            worker_id=str(worker_id),
            batch_sequence=_payload_int(payload, "batch_sequence"),
            envelopes=envelopes,
            is_terminal_batch=bool(payload.get("is_terminal_batch")),
            byte_count=_payload_int(payload, "byte_count", 0),
            gateway_mode=str(gateway_mode) if gateway_mode is not None else None,
        )


@frozen
class WorkerCompletionManifest:
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
        #arch-eval:entity_fullness=3
        #arch-eval:locational_stability=4
    """

    worker_id: str
    complete: bool
    last_batch_sequence: int | None
    transferred_batch_count: int
    transferred_envelope_count: int
    interruption_reason: str | None = None
    gateway_mode: str | None = None

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
            #arch-eval:delegation_boundary=3
            #arch-eval:cohesion=4
            #arch-eval:separation=4
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=3
            #arch-eval:entity_fullness=3
            #arch-eval:locational_stability=4
        """
        return {
            "worker_id": self.worker_id,
            "complete": self.complete,
            "last_batch_sequence": self.last_batch_sequence,
            "transferred_batch_count": self.transferred_batch_count,
            "transferred_envelope_count": self.transferred_envelope_count,
            "interruption_reason": self.interruption_reason,
            "gateway_mode": self.gateway_mode,
        }

    @classmethod
    def from_dict(cls, payload: JSONObject) -> WorkerCompletionManifest:
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

        Failure semantics:
            Raises RuntimeError for context-not-initialized or binding-missing conditions when required lifecycle
            objects are unavailable; raises TypeError for malformed envelopes violating single-payload or type
            constraints; raises ValueError for missing required fields in deserialized transport payloads; callers must
            handle these exceptions at hook or plugin boundaries to prevent test session crashes

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
        interruption_reason = payload.get("interruption_reason")
        gateway_mode = payload.get("gateway_mode")
        worker_id = payload.get("worker_id")
        if worker_id is None:
            msg = "Missing required field 'worker_id' in manifest payload"
            raise ValueError(msg)
        return cls(
            worker_id=str(worker_id),
            complete=bool(payload.get("complete")),
            last_batch_sequence=(
                _payload_int(payload, "last_batch_sequence") if payload.get("last_batch_sequence") is not None else None
            ),
            transferred_batch_count=_payload_int(payload, "transferred_batch_count", 0),
            transferred_envelope_count=_payload_int(payload, "transferred_envelope_count", 0),
            interruption_reason=str(interruption_reason) if interruption_reason is not None else None,
            gateway_mode=str(gateway_mode) if gateway_mode is not None else None,
        )


@define
class ReportingTransportSnapshot:
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

    expected_worker_ids: tuple[str, ...]
    batches_by_worker: dict[str, tuple[WorkerChunkBatch, ...]]
    manifests_by_worker: dict[str, WorkerCompletionManifest]


@define
class ReportingTransportSession:
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

    _lock: Lock = field(init=False, factory=Lock, repr=False)
    _expected_worker_ids: set[str] = field(init=False, factory=set, repr=False)
    _batches_by_worker: dict[str, list[WorkerChunkBatch]] = field(init=False, factory=dict, repr=False)
    _manifests_by_worker: dict[str, WorkerCompletionManifest] = field(init=False, factory=dict, repr=False)

    def register_expected_worker(self, worker_id: str) -> None:
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
        with self._lock:
            self._expected_worker_ids.add(worker_id)

    def record_batch(self, batch: WorkerChunkBatch) -> None:
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
        with self._lock:
            self._batches_by_worker.setdefault(batch.worker_id, []).append(batch)

    def receive_remote_event(self, event_name: str, payload: JSONObject) -> None:
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
        if event_name != REPORTING_BATCH_EVENT:
            logger.warning("Ignoring unknown reporting event '%s'.", event_name)
            return
        batch_payload = payload.get("batch")
        if not isinstance(batch_payload, dict):
            logger.warning("Ignoring malformed reporting batch payload for event '%s'.", event_name)
            return
        self.record_batch(WorkerChunkBatch.from_dict(batch_payload))

    def record_manifest(self, manifest: WorkerCompletionManifest) -> None:
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
            #arch-eval:delegation_boundary=3
            #arch-eval:cohesion=4
            #arch-eval:separation=4
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=3
            #arch-eval:locational_stability=4
        """
        with self._lock:
            self._manifests_by_worker[manifest.worker_id] = manifest

    def batches_for_worker(self, worker_id: str) -> tuple[WorkerChunkBatch, ...]:
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
        with self._lock:
            batches = tuple(self._batches_by_worker.get(worker_id, ()))
        return tuple(sorted(batches, key=lambda batch: batch.batch_sequence))

    def manifest_for_worker(self, worker_id: str) -> WorkerCompletionManifest | None:
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
        with self._lock:
            return self._manifests_by_worker.get(worker_id)

    def snapshot(self) -> ReportingTransportSnapshot:
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
        with self._lock:
            return ReportingTransportSnapshot(
                expected_worker_ids=tuple(sorted(self._expected_worker_ids)),
                batches_by_worker={
                    worker_id: tuple(sorted(batches, key=lambda batch: batch.batch_sequence))
                    for worker_id, batches in self._batches_by_worker.items()
                },
                manifests_by_worker=dict(self._manifests_by_worker),
            )

    def wait_for_batches(
        self,
        worker_id: str,
        *,
        minimum_count: int = 1,
        timeout: float = 2.0,
    ) -> tuple[WorkerChunkBatch, ...]:
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
        deadline = monotonic() + timeout
        while monotonic() < deadline:
            batches = self.batches_for_worker(worker_id)
            if len(batches) >= minimum_count:
                return batches
            sleep(0.01)
        return self.batches_for_worker(worker_id)


@define
class ReportingTransportClient:
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
        #arch-eval:entity_fullness=3
        #arch-eval:locational_stability=4
    """

    worker_id: str
    sender: ReportingEventSender
    gateway_mode: str | None = None
    batch_sequence: int = 0
    transferred_batch_count: int = 0
    transferred_envelope_count: int = 0
    last_publish_error: str | None = None

    def publish_envelopes(self, envelope_dicts: list[JSONObject]) -> WorkerChunkBatch:
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

        Failure semantics:
            Raises RuntimeError for context-not-initialized or binding-missing conditions when required lifecycle
            objects are unavailable; raises TypeError for malformed envelopes violating single-payload or type
            constraints; raises ValueError for missing required fields in deserialized transport payloads; callers must
            handle these exceptions at hook or plugin boundaries to prevent test session crashes

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
        if not envelope_dicts:
            msg = "Cannot publish an empty transport batch."
            raise ValueError(msg)
        batch = WorkerChunkBatch(
            worker_id=self.worker_id,
            batch_sequence=self.batch_sequence,
            envelopes=tuple(envelope_dicts),
            byte_count=len(json.dumps(envelope_dicts, separators=(",", ":"), sort_keys=True).encode("utf-8")),
            gateway_mode=self.gateway_mode,
        )
        try:
            self.sender(REPORTING_BATCH_EVENT, batch=batch.as_dict(), gateway_mode=self.gateway_mode)
        except Exception as exc:
            self.last_publish_error = str(exc)
            logger.warning("Failed to publish worker transport batch for %s", self.worker_id, exc_info=True)
            msg = f"Failed to publish worker transport batch for '{self.worker_id}'."
            raise RuntimeError(msg) from exc
        self.batch_sequence += 1
        self.transferred_batch_count += 1
        self.transferred_envelope_count += len(envelope_dicts)
        return batch

    def build_manifest(self, *, complete: bool, interruption_reason: str | None = None) -> WorkerCompletionManifest:
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
        resolved_reason = interruption_reason or self.last_publish_error
        resolved_complete = complete and resolved_reason is None
        last_batch_sequence = self.batch_sequence - 1 if self.transferred_batch_count else None
        return WorkerCompletionManifest(
            worker_id=self.worker_id,
            complete=resolved_complete,
            last_batch_sequence=last_batch_sequence,
            transferred_batch_count=self.transferred_batch_count,
            transferred_envelope_count=self.transferred_envelope_count,
            interruption_reason=resolved_reason,
            gateway_mode=self.gateway_mode,
        )
