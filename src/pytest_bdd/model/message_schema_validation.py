"""
Provide cucumber message schema validation helpers.

Responsibility:
    Provide cucumber message schema validation helpers. It directly owns the observable contract, local decisions, and
    maintenance boundary for this module.

Reason for existence:
    This entity is the information expert for `pytest_bdd.model.message_schema_validation` because it keeps the nearest
    code, data shape, call signature, and failure knowledge together.

Delegates:
    - _build_schema_validator: owns nested behavior below this boundary
    - _schema_validator_state: owns nested behavior below this boundary
    - _schema_violation: owns nested behavior below this boundary
    - _strip_nones: owns nested behavior below this boundary
    - validate_envelope_dict_against_schema: owns nested behavior below this boundary
    - validate_envelope_against_schema: owns nested behavior below this boundary

Cohesion:
    The implementation stays together because its imports, calls, state writes, and return contract describe one
    maintainable decision unit.

Separation:
    - module peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
      widening caller knowledge.

Main consumers:
    - src/pytest_bdd/message_stream_validation/pipeline.py: imports or references `message_schema_validation`
    - src/pytest_bdd/model/message_validation.py: imports or references `message_schema_validation`
    - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_core.py: imports or references
      `message_schema_validation`

State and side effects:
    mutates registry, validator, schema_dir, envelope_schema, contents; depends on __future__.annotations, json,
    functools.cache, typing.TYPE_CHECKING, typing.cast.

Invariants:
    - `pytest_bdd.model.message_schema_validation` keeps its documented import path, ownership boundary, and observable
      behavior stable for callers.

Architecture score:
    #arch-eval:reason_for_existence=4
    #arch-eval:owned_responsibility=4
    #arch-eval:delegation_boundary=4
    #arch-eval:cohesion=3
    #arch-eval:separation=3
    #arch-eval:consumer_clarity=4
    #arch-eval:state_invariants=4
    #arch-eval:entity_fullness=4
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
    Responsibility:
        Responsibility: Responsibility: `pytest_bdd.model.message_schema_validation._build_schema_validator` owns
        documented function behavior. It directly owns the observable contract, local decisions, and maintenance
        boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.model.message_schema_validation._build_schema_validator`
        because it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - registry.with_resource: collaborator call used by this boundary
        - load_envelope_schema: collaborator call used by this boundary
        - Nothing.value_or: collaborator call used by this boundary
        - Registry: collaborator call used by this boundary
        - sorted: collaborator call used by this boundary
        - schema_dir.glob: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/message_stream_validation/pipeline.py: imports or references `_build_schema_validator`
        - src/pytest_bdd/model/message_validation.py: imports or references `_build_schema_validator`
        - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_core.py: imports or references
          `_build_schema_validator`

    State and side effects:
        mutates registry, schema_dir, envelope_schema, contents, resource; depends on
        jsonschema.validators.validator_for, referencing.Registry, referencing.Resource.

    Invariants:
        - `pytest_bdd.model.message_schema_validation._build_schema_validator` keeps its documented import path,
          ownership boundary, and observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=4
    """
    from jsonschema.validators import validator_for  # noqa: PLC0415
    from referencing import Registry, Resource  # noqa: PLC0415 -- optional referencing dependency

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
    Responsibility:
        Responsibility: Responsibility: `pytest_bdd.model.message_schema_validation._schema_validator_state` owns
        documented function behavior. It directly owns the observable contract, local decisions, and maintenance
        boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.model.message_schema_validation._schema_validator_state`
        because it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - _build_schema_validator: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/message_stream_validation/pipeline.py: imports or references `_schema_validator_state`
        - src/pytest_bdd/model/message_validation.py: imports or references `_schema_validator_state`
        - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_core.py: imports or references
          `_schema_validator_state`

    State and side effects:
        keeps no local persistent state beyond call-local values.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=4
    """
    return _build_schema_validator()


def _schema_violation(error: ValidationError) -> MessageValidationViolation:
    """
    Responsibility:
        Responsibility: Responsibility: `pytest_bdd.model.message_schema_validation._schema_violation` owns documented
        function behavior. It directly owns the observable contract, local decisions, and maintenance boundary for this
        function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.model.message_schema_validation._schema_violation` because
        it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - str: collaborator call used by this boundary
        - tuple: collaborator call used by this boundary
        - MessageValidationViolation: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/message_stream_validation/pipeline.py: imports or references `_schema_violation`
        - src/pytest_bdd/model/message_validation.py: imports or references `_schema_violation`
        - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_core.py: imports or references
          `_schema_violation`

    State and side effects:
        mutates json_path, schema_path.

    Invariants:
        - `pytest_bdd.model.message_schema_validation._schema_violation` keeps its documented import path, ownership
          boundary, and observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
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
    Responsibility:
        Responsibility: Responsibility: `pytest_bdd.model.message_schema_validation._strip_nones` owns documented
        function behavior. It directly owns the observable contract, local decisions, and maintenance boundary for this
        function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.model.message_schema_validation._strip_nones` because it
        keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - isinstance: collaborator call used by this boundary
        - _strip_nones: collaborator call used by this boundary
        - value.items: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/message_stream_validation/pipeline.py: imports or references `_strip_nones`
        - src/pytest_bdd/model/message_validation.py: imports or references `_strip_nones`
        - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_core.py: imports or references
          `_strip_nones`

    State and side effects:
        keeps no local persistent state beyond call-local values.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=3
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
    Validate a raw dictionary representation of a message envelope against the loaded JSON schema.

    Returns:
        A tuple of MessageValidationViolation instances mapping to specific JSON schema violations, if any.

    Responsibility:
        Validate a raw dictionary representation of a message envelope against the loaded JSON schema. It directly owns
        the observable contract, local decisions, and maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.model.message_schema_validation.validate_envelope_dict_against_schema` because it keeps the nearest
        code, data shape, call signature, and failure knowledge together.

    Delegates:
        - cast: collaborator call used by this boundary
        - _strip_nones: collaborator call used by this boundary
        - _schema_validator_state: collaborator call used by this boundary
        - MessageValidationViolation: collaborator call used by this boundary
        - tuple: collaborator call used by this boundary
        - _schema_violation: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/message_stream_validation/pipeline.py: imports or references
          `validate_envelope_dict_against_schema`
        - src/pytest_bdd/model/__init__.py: imports or references `validate_envelope_dict_against_schema`
        - src/pytest_bdd/model/message_validation.py: imports or references `validate_envelope_dict_against_schema`
        - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_core.py: imports or references
          `validate_envelope_dict_against_schema`

    State and side effects:
        mutates clean_envelope_dict, validator, validator_init_error; depends on typing.Any.

    Invariants:
        - `pytest_bdd.model.message_schema_validation.validate_envelope_dict_against_schema` keeps its documented import
          path, ownership boundary, and observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
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
    from typing import Any  # noqa: PLC0415

    return tuple(_schema_violation(error) for error in cast("Any", validator).iter_errors(clean_envelope_dict))


def validate_envelope_against_schema(
    envelope: EventEnvelope,
    *,
    serialization_profile: MessageSerializationProfile = MessageSerializationProfile.schema_compatible,
) -> tuple[MessageValidationViolation, ...]:
    """
    Serialize an EventEnvelope into its dictionary representation and validate it against the JSON schema.

    Returns:
        A tuple of MessageValidationViolation instances discovered during schema validation.

    Responsibility:
        Serialize an EventEnvelope into its dictionary representation and validate it against the JSON schema. It
        directly owns the observable contract, local decisions, and maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.model.message_schema_validation.validate_envelope_against_schema` because it keeps the nearest code,
        data shape, call signature, and failure knowledge together.

    Delegates:
        - validate_envelope_dict_against_schema: collaborator call used by this boundary
        - ExecutionMessageAdapter.serialize_to_dict: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/message_stream_validation/pipeline.py: imports or references `validate_envelope_against_schema`
        - src/pytest_bdd/model/__init__.py: imports or references `validate_envelope_against_schema`
        - src/pytest_bdd/model/message_validation.py: imports or references `validate_envelope_against_schema`
        - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_core.py: imports or references
          `validate_envelope_against_schema`

    State and side effects:
        keeps no local persistent state beyond call-local values.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=4

    """
    return validate_envelope_dict_against_schema(
        ExecutionMessageAdapter.serialize_to_dict(envelope, profile=serialization_profile),
    )
