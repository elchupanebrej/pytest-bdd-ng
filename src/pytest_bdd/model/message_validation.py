"""
Provide public message validation helpers.

Responsibility:
    Provide public message validation helpers. It directly owns the observable contract, local decisions, and
    maintenance boundary for this module.

Reason for existence:
    This entity is the information expert for `pytest_bdd.model.message_validation` because it keeps the nearest code,
    data shape, call signature, and failure knowledge together.

Delegates:
    - parse_message_dict: owns nested behavior below this boundary

Cohesion:
    The implementation stays together because its imports, calls, state writes, and return contract describe one
    maintainable decision unit.

Separation:
    - module peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
      widening caller knowledge.

Main consumers:
    - None found by static import/name scan; verify dynamic use before refactor

State and side effects:
    mutates message; depends on __future__.annotations, typing.TYPE_CHECKING, cucumber_messages.Envelope,
    pytest_bdd.model.message_converter.validate_envelope_shape,
    pytest_bdd.model.message_schema_validation.validate_envelope_against_schema.

Invariants:
    - `pytest_bdd.model.message_validation` keeps its documented import path, ownership boundary, and observable
      behavior stable for callers.

Architecture score:
    #arch-eval:reason_for_existence=4
    #arch-eval:owned_responsibility=4
    #arch-eval:delegation_boundary=4
    #arch-eval:cohesion=3
    #arch-eval:separation=3
    #arch-eval:consumer_clarity=2
    #arch-eval:state_invariants=4
    #arch-eval:entity_fullness=3
    #arch-eval:locational_stability=2
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from cucumber_messages import (
    Envelope as Message,  # upstream library missing type stubs
)

from pytest_bdd.model.message_converter import validate_envelope_shape
from pytest_bdd.model.message_schema_validation import (  # noqa: F401
    validate_envelope_against_schema,
    validate_envelope_dict_against_schema,
)
from pytest_bdd.model.message_stream_validation import (  # noqa: F401
    ALLOWED_IMPLEMENTATION_STATUSES,
    collect_observed_capability_ids,
    collect_observed_outcomes,
    default_outcome_mapping_rules,
    observed_outcome_from_envelope,
    validate_message_stream,
)
from pytest_bdd.model.message_validation_result import (  # noqa: F401
    AllowedImplementationStatus,
    MessageValidationResult,
    MessageValidationViolation,
    SchemaValidationResult,
    ValidationCode,
)
from pytest_bdd.model.message_validation_xdist import (  # noqa: F401
    XdistReportingCompatibilityResult,
    format_xdist_transport_compatibility_error,
    validate_execnet_serializable_payload,
    validate_xdist_reporting_compatibility,
)

if TYPE_CHECKING:
    from pytest_bdd.model.message_extension import EventEnvelope


def parse_message_dict(payload: dict[str, object]) -> EventEnvelope:
    """
    Instantiate an EventEnvelope from a raw dictionary while ensuring strict payload shape enforcement.

    Returns:
        The instantiated EventEnvelope object.

    Responsibility:
        Instantiate an EventEnvelope from a raw dictionary while ensuring strict payload shape enforcement. It directly
        owns the observable contract, local decisions, and maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.model.message_validation.parse_message_dict` because it
        keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - Message: collaborator call used by this boundary
        - validate_envelope_shape: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - None found by static import/name scan; verify dynamic use before refactor

    State and side effects:
        mutates message.

    Invariants:
        - `pytest_bdd.model.message_validation.parse_message_dict` keeps its documented import path, ownership boundary,
          and observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=2
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=2

    """
    message = Message(**payload)
    validate_envelope_shape(message)
    return message
