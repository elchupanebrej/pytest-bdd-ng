"""Provide message converter helpers."""

from __future__ import annotations

from dataclasses import asdict as dataclass_asdict
from dataclasses import is_dataclass
from datetime import datetime
from typing import cast

from attrs import AttrsInstance
from attrs import asdict as attrs_asdict
from attrs import has as attrs_has
from cucumber_messages import Envelope as Message  # type:ignore[attr-defined, import-untyped]
from cucumber_messages import json_converter  # type:ignore[import-untyped]

from pytest_bdd.types.json import JSONObject, JSONValue

from . import message_extension
from .message_validation import validate_envelope_shape

message_converter: json_converter.JsonDataclassConverter = json_converter.JsonDataclassConverter(
    module_scope=message_extension
)


def envelope_to_dict(message: Message) -> JSONObject:
    """Handle envelope to dict."""
    validate_envelope_shape(message)
    return cast(JSONObject, message_converter.to_dict(message))


def envelope_from_dict(payload: JSONObject) -> Message:
    """Handle envelope from dict."""
    message = message_converter.from_dict(payload, Message)
    validate_envelope_shape(message)
    return message


def governance_value_to_dict(value: object) -> JSONValue:
    """Handle governance value to dict."""
    if attrs_has(type(value)) and not isinstance(value, type):
        return governance_value_to_dict(attrs_asdict(cast(AttrsInstance, value)))
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
