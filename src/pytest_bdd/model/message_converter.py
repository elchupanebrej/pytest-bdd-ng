from __future__ import annotations

from typing import Any, cast

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
