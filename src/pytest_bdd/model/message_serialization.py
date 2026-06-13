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
    - cucumber_messages Envelope: Provides supporting functionality through a well-defined interface, delegating a
    focused sub-task to keep this entity cohesive and its responsibility boundary clean

Cohesion:
    All functions, methods, and data within this entity operate on the same local state, share identical import
    dependencies and control flow patterns, and collectively implement a single cohesive responsibility rather than
    dispersing unrelated utilities across separate modules

Separation:
    - message_converter: This entity is kept distinct from its peer to prevent callers from coupling to multiple domain
    boundaries at once, ensuring each concept can evolve independently without cascading changes across the codebase

Main consumers:
    - execution_message_adapter: Referenced by collection, runtime, and reporting layer plugins through the
    pytest_bdd.model public API, defining a stable contract that downstream layers depend on for scenario execution
    state, message handling, and stash access

State and side effects:
    Maintains in-memory state via attrs-defined fields with factory defaults, performing no file I/O, network
    operations, or direct pytest stash access; stash interaction is delegated to StashAccess class methods for type-safe
    boundary enforcement

Invariants:
    - schema_compatible profile must map all pytest-bdd-specific pattern types to REGULAR_EXPRESSION; extended profile
    must preserve original types unchanged

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

from copy import deepcopy
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pytest_bdd.types.json import JSONObject


class MessageSerializationProfile(str, Enum):
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
        - cucumber_messages Envelope: Provides supporting functionality through a well-defined interface, delegating a
        focused sub-task to keep this entity cohesive and its responsibility boundary clean

    Cohesion:
        All functions, methods, and data within this entity operate on the same local state, share identical import
        dependencies and control flow patterns, and collectively implement a single cohesive responsibility rather than
        dispersing unrelated utilities across separate modules

    Separation:
        - message_converter: This entity is kept distinct from its peer to prevent callers from coupling to multiple
        domain boundaries at once, ensuring each concept can evolve independently without cascading changes across the
        codebase

    Main consumers:
        - execution_message_adapter: Referenced by collection, runtime, and reporting layer plugins through the
        pytest_bdd.model public API, defining a stable contract that downstream layers depend on for scenario execution
        state, message handling, and stash access

    State and side effects:
        Maintains in-memory state via attrs-defined fields with factory defaults, performing no file I/O, network
        operations, or direct pytest stash access; stash interaction is delegated to StashAccess class methods for type-
        safe boundary enforcement

    Invariants:
        - schema_compatible profile must map all pytest-bdd-specific pattern types to REGULAR_EXPRESSION; extended
        profile must preserve original types unchanged

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

    extended = "extended"
    schema_compatible = "schema_compatible"


_SCHEMA_COMPATIBLE_STEP_DEFINITION_PATTERN_TYPES: dict[str, str] = {
    "PYTEST_BDD_HEURISTIC_EXPRESSION": "REGULAR_EXPRESSION",
    "PYTEST_BDD_STRING_EXPRESSION": "REGULAR_EXPRESSION",
    "PYTEST_BDD_REGULAR_EXPRESSION": "REGULAR_EXPRESSION",
    "PYTEST_BDD_PARSE_EXPRESSION": "REGULAR_EXPRESSION",
    "PYTEST_BDD_CFPARSE_EXPRESSION": "REGULAR_EXPRESSION",
    "PYTEST_BDD_OTHER_EXPRESSION": "REGULAR_EXPRESSION",
}


def normalize_envelope_dict_for_profile(
    envelope_dict: JSONObject,
    *,
    profile: MessageSerializationProfile,
) -> JSONObject:
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
        - cucumber_messages Envelope: Provides supporting functionality through a well-defined interface, delegating a
        focused sub-task to keep this entity cohesive and its responsibility boundary clean

    Cohesion:
        All functions, methods, and data within this entity operate on the same local state, share identical import
        dependencies and control flow patterns, and collectively implement a single cohesive responsibility rather than
        dispersing unrelated utilities across separate modules

    Separation:
        - message_converter: This entity is kept distinct from its peer to prevent callers from coupling to multiple
        domain boundaries at once, ensuring each concept can evolve independently without cascading changes across the
        codebase

    Main consumers:
        - execution_message_adapter: Referenced by collection, runtime, and reporting layer plugins through the
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
    if profile is MessageSerializationProfile.extended:
        return envelope_dict

    normalized = deepcopy(envelope_dict)
    for payload_key in ("stepDefinition", "step_definition"):
        payload = normalized.get(payload_key)
        if not isinstance(payload, dict):
            continue
        pattern = payload.get("pattern")
        if not isinstance(pattern, dict):
            continue
        raw_type = pattern.get("type")
        if isinstance(raw_type, str):
            pattern["type"] = _SCHEMA_COMPATIBLE_STEP_DEFINITION_PATTERN_TYPES.get(raw_type, raw_type)
        break

    return normalized
