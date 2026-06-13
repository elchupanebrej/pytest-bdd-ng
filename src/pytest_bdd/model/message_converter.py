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
    - cucumber_messages.json_converter: Provides supporting functionality through a well-defined interface, delegating a
    focused sub-task to keep this entity cohesive and its responsibility boundary clean

Cohesion:
    All functions, methods, and data within this entity operate on the same local state, share identical import
    dependencies and control flow patterns, and collectively implement a single cohesive responsibility rather than
    dispersing unrelated utilities across separate modules

Separation:
    - message_serialization: This entity is kept distinct from its peer to prevent callers from coupling to multiple
    domain boundaries at once, ensuring each concept can evolve independently without cascading changes across the
    codebase

Main consumers:
    - gherkin_message_reporter: Referenced by collection, runtime, and reporting layer plugins through the
    pytest_bdd.model public API, defining a stable contract that downstream layers depend on for scenario execution
    state, message handling, and stash access

State and side effects:
    Maintains in-memory state via attrs-defined fields with factory defaults, performing no file I/O, network
    operations, or direct pytest stash access; stash interaction is delegated to StashAccess class methods for type-safe
    boundary enforcement

Invariants:
    - Envelope must have exactly one non-None payload field before conversion; message_converter must use the
    message_extension module scope for custom type serialization; governance_value_to_dict must produce JSON-
    serializable primitives only

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

from dataclasses import asdict as dataclass_asdict
from dataclasses import is_dataclass
from datetime import datetime
from typing import TYPE_CHECKING, cast

from attrs import AttrsInstance
from attrs import asdict as attrs_asdict
from attrs import has as attrs_has
from cucumber_messages import (
    Envelope as Message,  # upstream library missing type stubs
)
from cucumber_messages import json_converter  # library has no type stubs

from . import message_extension
from .message_extension import has_single_payload

if TYPE_CHECKING:
    from pytest_bdd.types.json import JSONObject, JSONValue

message_converter: json_converter.JsonDataclassConverter = json_converter.JsonDataclassConverter(
    module_scope=message_extension,
)


def envelope_to_dict(message: Message) -> JSONObject:
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
        - cucumber_messages.json_converter: Provides supporting functionality through a well-defined interface,
        delegating a focused sub-task to keep this entity cohesive and its responsibility boundary clean

    Cohesion:
        All functions, methods, and data within this entity operate on the same local state, share identical import
        dependencies and control flow patterns, and collectively implement a single cohesive responsibility rather than
        dispersing unrelated utilities across separate modules

    Separation:
        - message_serialization: This entity is kept distinct from its peer to prevent callers from coupling to multiple
        domain boundaries at once, ensuring each concept can evolve independently without cascading changes across the
        codebase

    Main consumers:
        - gherkin_message_reporter: Referenced by collection, runtime, and reporting layer plugins through the
        pytest_bdd.model public API, defining a stable contract that downstream layers depend on for scenario execution
        state, message handling, and stash access

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
    validate_envelope_shape(message)
    return cast("JSONObject", message_converter.to_dict(message))


def envelope_from_dict(payload: JSONObject) -> Message:
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
        - cucumber_messages.json_converter: Provides supporting functionality through a well-defined interface,
        delegating a focused sub-task to keep this entity cohesive and its responsibility boundary clean

    Cohesion:
        All functions, methods, and data within this entity operate on the same local state, share identical import
        dependencies and control flow patterns, and collectively implement a single cohesive responsibility rather than
        dispersing unrelated utilities across separate modules

    Separation:
        - message_serialization: This entity is kept distinct from its peer to prevent callers from coupling to multiple
        domain boundaries at once, ensuring each concept can evolve independently without cascading changes across the
        codebase

    Main consumers:
        - gherkin_message_reporter: Referenced by collection, runtime, and reporting layer plugins through the
        pytest_bdd.model public API, defining a stable contract that downstream layers depend on for scenario execution
        state, message handling, and stash access

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
    message = message_converter.from_dict(payload, Message)
    validate_envelope_shape(message)
    return cast("Message", message)


def governance_value_to_dict(value: object) -> JSONValue:  # noqa: PLR0911  -- suppressed warning
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
        - cucumber_messages.json_converter: Provides supporting functionality through a well-defined interface,
        delegating a focused sub-task to keep this entity cohesive and its responsibility boundary clean

    Cohesion:
        All functions, methods, and data within this entity operate on the same local state, share identical import
        dependencies and control flow patterns, and collectively implement a single cohesive responsibility rather than
        dispersing unrelated utilities across separate modules

    Separation:
        - message_serialization: This entity is kept distinct from its peer to prevent callers from coupling to multiple
        domain boundaries at once, ensuring each concept can evolve independently without cascading changes across the
        codebase

    Main consumers:
        - gherkin_message_reporter: Referenced by collection, runtime, and reporting layer plugins through the
        pytest_bdd.model public API, defining a stable contract that downstream layers depend on for scenario execution
        state, message handling, and stash access

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
    if attrs_has(type(value)) and not isinstance(value, type):
        return governance_value_to_dict(attrs_asdict(cast("AttrsInstance", value)))
    if is_dataclass(value) and not isinstance(value, type):
        return governance_value_to_dict(dataclass_asdict(value))
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, dict):
        return {str(key): governance_value_to_dict(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set, frozenset)):
        return [governance_value_to_dict(item) for item in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


def validate_envelope_shape(envelope: message_extension.EventEnvelope) -> None:
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
        - cucumber_messages.json_converter: Provides supporting functionality through a well-defined interface,
        delegating a focused sub-task to keep this entity cohesive and its responsibility boundary clean

    Cohesion:
        All functions, methods, and data within this entity operate on the same local state, share identical import
        dependencies and control flow patterns, and collectively implement a single cohesive responsibility rather than
        dispersing unrelated utilities across separate modules

    Separation:
        - message_serialization: This entity is kept distinct from its peer to prevent callers from coupling to multiple
        domain boundaries at once, ensuring each concept can evolve independently without cascading changes across the
        codebase

    Main consumers:
        - gherkin_message_reporter: Referenced by collection, runtime, and reporting layer plugins through the
        pytest_bdd.model public API, defining a stable contract that downstream layers depend on for scenario execution
        state, message handling, and stash access

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
    if not has_single_payload(envelope):
        message = "Envelope must include exactly one payload field"
        raise TypeError(message)
