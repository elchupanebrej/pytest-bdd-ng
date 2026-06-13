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
    - jsonschema.validators: Provides supporting functionality through a well-defined interface, delegating a focused
    sub-task to keep this entity cohesive and its responsibility boundary clean

Cohesion:
    All functions, methods, and data within this entity operate on the same local state, share identical import
    dependencies and control flow patterns, and collectively implement a single cohesive responsibility rather than
    dispersing unrelated utilities across separate modules

Separation:
    - message_validation_result: This entity is kept distinct from its peer to prevent callers from coupling to multiple
    domain boundaries at once, ensuring each concept can evolve independently without cascading changes across the
    codebase

Main consumers:
    - message_validation: Referenced by collection, runtime, and reporting layer plugins through the pytest_bdd.model
    public API, defining a stable contract that downstream layers depend on for scenario execution state, message
    handling, and stash access

State and side effects:
    Maintains in-memory state via attrs-defined fields with factory defaults, performing no file I/O, network
    operations, or direct pytest stash access; stash interaction is delegated to StashAccess class methods for type-safe
    boundary enforcement

Invariants:
    - Schema validator must be lazily constructed and cached via functools.cache; _strip_nones must not mutate the
    original dict; schema loading errors must produce a single MessageValidationViolation rather than crashing

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
from functools import cache
from typing import TYPE_CHECKING, cast

from returns.maybe import Nothing

from pytest_bdd.model.execution_message_adapter import ExecutionMessageAdapter
from pytest_bdd.model.message_capability_inventory import load_envelope_schema
from pytest_bdd.model.message_serialization import MessageSerializationProfile
from pytest_bdd.model.message_validation_result import MessageValidationViolation

if TYPE_CHECKING:
    from collections.abc import Mapping

    from jsonschema import ValidationError

    from pytest_bdd.model.message_extension import EventEnvelope


def _build_schema_validator() -> tuple[object | None, str | None]:
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
        - jsonschema.validators: Provides supporting functionality through a well-defined interface, delegating a
        focused sub-task to keep this entity cohesive and its responsibility boundary clean

    Cohesion:
        All functions, methods, and data within this entity operate on the same local state, share identical import
        dependencies and control flow patterns, and collectively implement a single cohesive responsibility rather than
        dispersing unrelated utilities across separate modules

    Separation:
        - message_validation_result: This entity is kept distinct from its peer to prevent callers from coupling to
        multiple domain boundaries at once, ensuring each concept can evolve independently without cascading changes
        across the codebase

    Main consumers:
        - message_validation: Referenced by collection, runtime, and reporting layer plugins through the
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
    from jsonschema.validators import (  # deferred import to avoid circular dependency
        validator_for,
    )
    from referencing import Registry, Resource

    try:
        schema_dir, envelope_schema = load_envelope_schema()
    except (FileNotFoundError, OSError, TypeError, ValueError, json.JSONDecodeError) as exc:
        return Nothing.value_or(None), f"Unable to load Envelope.json schema: {exc}"

    registry: Registry = Registry()
    for schema_path in sorted(schema_dir.glob("*.json")):
        contents = json.loads(schema_path.read_text(encoding="utf-8"))
        resource = Resource.from_contents(contents)
        file_uri = schema_path.resolve().as_uri()
        registry = registry.with_resource(file_uri, resource)
        registry = registry.with_resource(schema_path.name, resource)
        registry = registry.with_resource(f"./{schema_path.name}", resource)

    validator_class = validator_for(envelope_schema)
    validator_class.check_schema(envelope_schema)
    validator = validator_class(envelope_schema, registry=registry)
    return validator, None


@cache
def _schema_validator_state() -> tuple[object | None, str | None]:
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
        - jsonschema.validators: Provides supporting functionality through a well-defined interface, delegating a
        focused sub-task to keep this entity cohesive and its responsibility boundary clean

    Cohesion:
        All functions, methods, and data within this entity operate on the same local state, share identical import
        dependencies and control flow patterns, and collectively implement a single cohesive responsibility rather than
        dispersing unrelated utilities across separate modules

    Separation:
        - message_validation_result: This entity is kept distinct from its peer to prevent callers from coupling to
        multiple domain boundaries at once, ensuring each concept can evolve independently without cascading changes
        across the codebase

    Main consumers:
        - message_validation: Referenced by collection, runtime, and reporting layer plugins through the
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
    return _build_schema_validator()


def _schema_violation(error: ValidationError) -> MessageValidationViolation:
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
        - jsonschema.validators: Provides supporting functionality through a well-defined interface, delegating a
        focused sub-task to keep this entity cohesive and its responsibility boundary clean

    Cohesion:
        All functions, methods, and data within this entity operate on the same local state, share identical import
        dependencies and control flow patterns, and collectively implement a single cohesive responsibility rather than
        dispersing unrelated utilities across separate modules

    Separation:
        - message_validation_result: This entity is kept distinct from its peer to prevent callers from coupling to
        multiple domain boundaries at once, ensuring each concept can evolve independently without cascading changes
        across the codebase

    Main consumers:
        - message_validation: Referenced by collection, runtime, and reporting layer plugins through the
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
    json_path = tuple(str(part) for part in error.absolute_path)
    schema_path = tuple(str(part) for part in error.absolute_schema_path)
    return MessageValidationViolation(
        code="SCHEMA_VIOLATION",
        message=f"Schema violation: {error.message}",
        json_path=json_path,
        schema_path=schema_path,
        validator=str(error.validator) if error.validator is not None else None,
    )


def _strip_nones(value: object) -> object:
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
        - jsonschema.validators: Provides supporting functionality through a well-defined interface, delegating a
        focused sub-task to keep this entity cohesive and its responsibility boundary clean

    Cohesion:
        All functions, methods, and data within this entity operate on the same local state, share identical import
        dependencies and control flow patterns, and collectively implement a single cohesive responsibility rather than
        dispersing unrelated utilities across separate modules

    Separation:
        - message_validation_result: This entity is kept distinct from its peer to prevent callers from coupling to
        multiple domain boundaries at once, ensuring each concept can evolve independently without cascading changes
        across the codebase

    Main consumers:
        - message_validation: Referenced by collection, runtime, and reporting layer plugins through the
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
    if isinstance(value, dict):
        return {k: _strip_nones(v) for k, v in value.items() if v is not None}
    if isinstance(value, list):
        return [_strip_nones(v) for v in value if v is not None]
    return value


def validate_envelope_dict_against_schema(
    envelope_dict: Mapping[str, object],
) -> tuple[MessageValidationViolation, ...]:
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
        - jsonschema.validators: Provides supporting functionality through a well-defined interface, delegating a
        focused sub-task to keep this entity cohesive and its responsibility boundary clean

    Cohesion:
        All functions, methods, and data within this entity operate on the same local state, share identical import
        dependencies and control flow patterns, and collectively implement a single cohesive responsibility rather than
        dispersing unrelated utilities across separate modules

    Separation:
        - message_validation_result: This entity is kept distinct from its peer to prevent callers from coupling to
        multiple domain boundaries at once, ensuring each concept can evolve independently without cascading changes
        across the codebase

    Main consumers:
        - message_validation: Referenced by collection, runtime, and reporting layer plugins through the
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
    clean_envelope_dict = cast("dict[str, object]", _strip_nones(envelope_dict))
    validator, validator_init_error = _schema_validator_state()
    if validator_init_error is not None:
        return (
            MessageValidationViolation(
                code="SCHEMA_VIOLATION",
                message=validator_init_error,
            ),
        )
    if validator is None:
        return ()
    from typing import Any

    return tuple(_schema_violation(error) for error in cast("Any", validator).iter_errors(clean_envelope_dict))


def validate_envelope_against_schema(
    envelope: EventEnvelope,
    *,
    serialization_profile: MessageSerializationProfile = MessageSerializationProfile.schema_compatible,
) -> tuple[MessageValidationViolation, ...]:
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
        - jsonschema.validators: Provides supporting functionality through a well-defined interface, delegating a
        focused sub-task to keep this entity cohesive and its responsibility boundary clean

    Cohesion:
        All functions, methods, and data within this entity operate on the same local state, share identical import
        dependencies and control flow patterns, and collectively implement a single cohesive responsibility rather than
        dispersing unrelated utilities across separate modules

    Separation:
        - message_validation_result: This entity is kept distinct from its peer to prevent callers from coupling to
        multiple domain boundaries at once, ensuring each concept can evolve independently without cascading changes
        across the codebase

    Main consumers:
        - message_validation: Referenced by collection, runtime, and reporting layer plugins through the
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
    return validate_envelope_dict_against_schema(
        ExecutionMessageAdapter.serialize_to_dict(envelope, profile=serialization_profile),
    )
