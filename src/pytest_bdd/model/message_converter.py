"""
Provide message converter helpers.

Responsibility:
    Provide message converter helpers. It directly owns the observable contract, local decisions, and maintenance
    boundary for this module. That boundary is intentionally stated in prose so maintainers can distinguish owned work
    from collaborators before editing.

Reason for existence:
    This entity is the information expert for `pytest_bdd.model.message_converter` because it keeps the nearest code,
    data shape, call signature, and failure knowledge together.

Delegates:
    - envelope_to_dict: owns nested behavior below this boundary
    - envelope_from_dict: owns nested behavior below this boundary
    - governance_value_to_dict: owns nested behavior below this boundary
    - validate_envelope_shape: owns nested behavior below this boundary

Cohesion:
    The implementation stays together because its imports, calls, state writes, and return contract describe one
    maintainable decision unit.

Separation:
    - module peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
      widening caller knowledge.

Main consumers:
    - src/pytest_bdd/collector_batch.py: imports or references `message_converter`
    - src/pytest_bdd/model/__init__.py: imports or references `message_converter`
    - src/pytest_bdd/model/feature_binding.py: imports or references `message_converter`
    - src/pytest_bdd/model/message_validation.py: imports or references `message_converter`
    - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_ci.py: imports or references `message_converter`

State and side effects:
    mutates message, message_converter; depends on __future__.annotations, dataclasses.asdict, dataclasses.is_dataclass,
    datetime.datetime, typing.TYPE_CHECKING.

Invariants:
    - `pytest_bdd.model.message_converter` keeps its documented import path, ownership boundary, and observable behavior
      stable for callers.

Failure semantics:
    Raises or re-raises TypeError; callers must treat these as boundary failures.

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
    Serialize a validated EventEnvelope to a raw JSON-compatible dictionary using the cucumber message converter.

    Returns:
        A dictionary representation of the envelope suitable for JSON serialization.

    Responsibility:
        Serialize a validated EventEnvelope to a raw JSON-compatible dictionary using the cucumber message converter. It
        directly owns the observable contract, local decisions, and maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.model.message_converter.envelope_to_dict` because it keeps
        the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - validate_envelope_shape: collaborator call used by this boundary
        - cast: collaborator call used by this boundary
        - message_converter.to_dict: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/model/execution_message_adapter.py: imports or references `envelope_to_dict`
        - src/pytest_bdd/model/feature_binding.py: imports or references `envelope_to_dict`
        - src/pytest_bdd/model/message_validation.py: imports or references `envelope_to_dict`
        - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_ci.py: imports or references
          `envelope_to_dict`
        - src/pytest_bdd/plugin/gherkin_message_reporter/transport_runtime.py: imports or references `envelope_to_dict`

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
    validate_envelope_shape(message)
    return cast("JSONObject", message_converter.to_dict(message))


def envelope_from_dict(payload: JSONObject) -> Message:
    """
    Deserialize a raw dictionary payload into an EventEnvelope and verify its shape constraints.

    Returns:
        The populated EventEnvelope instance.

    Responsibility:
        Deserialize a raw dictionary payload into an EventEnvelope and verify its shape constraints. It directly owns
        the observable contract, local decisions, and maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.model.message_converter.envelope_from_dict` because it
        keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - message_converter.from_dict: collaborator call used by this boundary
        - validate_envelope_shape: collaborator call used by this boundary
        - cast: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/model/execution_message_adapter.py: imports or references `envelope_from_dict`
        - src/pytest_bdd/model/feature_binding.py: imports or references `envelope_from_dict`
        - src/pytest_bdd/model/message_consolidation.py: imports or references `envelope_from_dict`
        - src/pytest_bdd/model/message_validation.py: imports or references `envelope_from_dict`
        - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_ci.py: imports or references
          `envelope_from_dict`

    State and side effects:
        mutates message.

    Invariants:
        - `pytest_bdd.model.message_converter.envelope_from_dict` keeps its documented import path, ownership boundary,
          and observable behavior stable for callers.

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
    message = message_converter.from_dict(payload, Message)
    validate_envelope_shape(message)
    return cast("Message", message)


def governance_value_to_dict(value: object) -> JSONValue:  # noqa: PLR0911
    """
    Recursively convert an arbitrary governance value into a JSON-serializable primitive representation.

    Handles attrs instances, dataclasses, datetimes, nested collections, and all JSON primitives. Falls back to
    string conversion for any type not natively serializable.

    Returns:
        A JSON-compatible value (str, int, float, bool, None, dict, or list).

    Responsibility:
        Recursively convert an arbitrary governance value into a JSON-serializable primitive representation. It directly
        owns the observable contract, local decisions, and maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.model.message_converter.governance_value_to_dict` because
        it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - isinstance: collaborator call used by this boundary
        - governance_value_to_dict: collaborator call used by this boundary
        - str: collaborator call used by this boundary
        - attrs_has: collaborator call used by this boundary
        - type: collaborator call used by this boundary
        - attrs_asdict: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/model/__init__.py: imports or references `governance_value_to_dict`
        - src/pytest_bdd/model/feature_binding.py: imports or references `governance_value_to_dict`
        - src/pytest_bdd/model/message_validation.py: imports or references `governance_value_to_dict`
        - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_ci.py: imports or references
          `governance_value_to_dict`
        - src/pytest_bdd/plugin/gherkin_message_reporter/transport_runtime.py: imports or references
          `governance_value_to_dict`

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
    Verify that an EventEnvelope strictly adheres to the oneof payload constraint defined by the cucumber protocol.

    Raises:
        TypeError: If the envelope is missing a payload or contains multiple contradictory payloads.

    Responsibility:
        Verify that an EventEnvelope strictly adheres to the oneof payload constraint defined by the cucumber protocol.
        It directly owns the observable contract, local decisions, and maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.model.message_converter.validate_envelope_shape` because
        it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - has_single_payload: collaborator call used by this boundary
        - TypeError: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/model/__init__.py: imports or references `validate_envelope_shape`
        - src/pytest_bdd/model/feature_binding.py: imports or references `validate_envelope_shape`
        - src/pytest_bdd/model/message_validation.py: imports or references `validate_envelope_shape`
        - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_ci.py: imports or references
          `validate_envelope_shape`
        - src/pytest_bdd/plugin/gherkin_message_reporter/transport_runtime.py: imports or references
          `validate_envelope_shape`

    State and side effects:
        mutates message.

    Invariants:
        - `pytest_bdd.model.message_converter.validate_envelope_shape` keeps its documented import path, ownership
          boundary, and observable behavior stable for callers.

    Failure semantics:
        Raises or re-raises TypeError; callers must treat these as boundary failures.

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
    if not has_single_payload(envelope):
        message = "Envelope must include exactly one payload field"
        raise TypeError(message)
