from __future__ import annotations

from dataclasses import asdict as dataclass_asdict
from dataclasses import is_dataclass
from datetime import datetime
from typing import Any, cast

from attrs import asdict as attrs_asdict
from attrs import has as attrs_has
from cucumber_messages import Envelope as Message  # type:ignore[attr-defined, import-untyped]
from cucumber_messages import json_converter  # type:ignore[import-untyped]

from . import message_extension
from .message_validation import validate_envelope_shape

message_converter: json_converter.JsonDataclassConverter = json_converter.JsonDataclassConverter(
    module_scope=message_extension
)


def envelope_to_dict(message: Message) -> dict[str, Any]:
    validate_envelope_shape(message)
    return cast(dict[str, Any], message_converter.to_dict(message))


def envelope_from_dict(payload: dict[str, Any]) -> Message:
    message = message_converter.from_dict(payload, Message)
    validate_envelope_shape(message)
    return message


def governance_value_to_dict(value: Any) -> Any:
    if attrs_has(type(value)) and not isinstance(value, type):
        return governance_value_to_dict(attrs_asdict(value))
    if is_dataclass(value) and not isinstance(value, type):
        return governance_value_to_dict(dataclass_asdict(value))
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, dict):
        return {key: governance_value_to_dict(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set, frozenset)):
        return [governance_value_to_dict(item) for item in value]
    return value
