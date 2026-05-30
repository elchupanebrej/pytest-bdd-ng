"""Provide public message validation helpers."""

from __future__ import annotations

from typing import TYPE_CHECKING

from cucumber_messages import Envelope as Message  # type:ignore[attr-defined, import-untyped]

from pytest_bdd.model.message_converter import validate_envelope_shape
from pytest_bdd.model.message_schema_validation import (
    validate_envelope_against_schema,
    validate_envelope_dict_against_schema,
)
from pytest_bdd.model.message_stream_validation import (
    ALLOWED_IMPLEMENTATION_STATUSES,
    collect_observed_capability_ids,
    collect_observed_outcomes,
    default_outcome_mapping_rules,
    observed_outcome_from_envelope,
    validate_message_stream,
)
from pytest_bdd.model.message_validation_result import (
    AllowedImplementationStatus,
    MessageValidationResult,
    MessageValidationViolation,
    SchemaValidationResult,
    ValidationCode,
)
from pytest_bdd.model.message_validation_xdist import (
    XdistReportingCompatibilityResult,
    format_xdist_transport_compatibility_error,
    validate_execnet_serializable_payload,
    validate_xdist_reporting_compatibility,
)

if TYPE_CHECKING:
    from pytest_bdd.model.message_extension import EventEnvelope


def parse_message_dict(payload: dict) -> EventEnvelope:
    """
    Instantiate an EventEnvelope from a raw dictionary while ensuring strict payload shape enforcement.

    Returns:
        The instantiated EventEnvelope object.

    """
    message = Message(**payload)
    validate_envelope_shape(message)
    return message


__all__ = [
    "ALLOWED_IMPLEMENTATION_STATUSES",
    "AllowedImplementationStatus",
    "MessageValidationResult",
    "MessageValidationViolation",
    "SchemaValidationResult",
    "ValidationCode",
    "XdistReportingCompatibilityResult",
    "collect_observed_capability_ids",
    "collect_observed_outcomes",
    "default_outcome_mapping_rules",
    "format_xdist_transport_compatibility_error",
    "observed_outcome_from_envelope",
    "parse_message_dict",
    "validate_envelope_against_schema",
    "validate_envelope_dict_against_schema",
    "validate_execnet_serializable_payload",
    "validate_message_stream",
    "validate_xdist_reporting_compatibility",
]
