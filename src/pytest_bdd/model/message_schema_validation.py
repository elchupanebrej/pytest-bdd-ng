"""Provide cucumber message schema validation helpers."""

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
    from jsonschema.validators import validator_for  # noqa: PLC0415
    from referencing import Registry, Resource  # noqa: PLC0415 -- optional referencing dependency

    try:
        schema_dir, envelope_schema = load_envelope_schema()
    except (FileNotFoundError, OSError, TypeError, ValueError, json.JSONDecodeError) as exc:
        return Nothing.value_or(None), f"Unable to load Envelope.json schema: {exc}"

    registry = Registry()
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
    return _build_schema_validator()


def _schema_violation(error: ValidationError) -> MessageValidationViolation:
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
    if isinstance(value, dict):
        return {k: _strip_nones(v) for k, v in value.items() if v is not None}
    if isinstance(value, list):
        return [_strip_nones(v) for v in value if v is not None]
    return value


def validate_envelope_dict_against_schema(
    envelope_dict: Mapping[str, object],
) -> tuple[MessageValidationViolation, ...]:
    """
    Validate a raw dictionary representation of a message envelope against the loaded JSON schema.

    Returns:
        A tuple of MessageValidationViolation instances mapping to specific JSON schema violations, if any.

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
    return tuple(_schema_violation(error) for error in validator.iter_errors(clean_envelope_dict))


def validate_envelope_against_schema(
    envelope: EventEnvelope,
    *,
    serialization_profile: MessageSerializationProfile = MessageSerializationProfile.schema_compatible,
) -> tuple[MessageValidationViolation, ...]:
    """
    Serialize an EventEnvelope into its dictionary representation and validate it against the JSON schema.

    Returns:
        A tuple of MessageValidationViolation instances discovered during schema validation.

    """
    return validate_envelope_dict_against_schema(
        ExecutionMessageAdapter.serialize_to_dict(envelope, profile=serialization_profile),
    )
