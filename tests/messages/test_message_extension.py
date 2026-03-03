from __future__ import annotations

from typing import get_args, get_type_hints

import cucumber_messages as cucumber_messages_module
from cucumber_messages import Envelope

from pytest_bdd.model.message_extension import (
    OPTIONAL_STATUS_PAYLOAD_KINDS,
    PAYLOAD_KINDS,
    REQUIRED_STATUS_PAYLOAD_KINDS,
    STATUS_CAPABLE_PAYLOAD_KINDS,
)


def _unwrap_optional(value: object) -> object:
    args = tuple(option for option in get_args(value) if option is not type(None))
    if len(args) == 1:
        return args[0]
    return value


def _is_optional(value: object) -> bool:
    return any(option is type(None) for option in get_args(value))


def test_payload_kinds_are_derived_from_protocol_envelope() -> None:
    envelope_hints = get_type_hints(Envelope, globalns=vars(cucumber_messages_module))
    assert PAYLOAD_KINDS == tuple(envelope_hints.keys())


def test_status_capable_payload_kinds_are_protocol_derived() -> None:
    envelope_hints = get_type_hints(Envelope, globalns=vars(cucumber_messages_module))
    governance_fields = {"implementation_status", "implementation_comment", "hook_origin"}

    expected_status_capable: list[str] = []
    expected_required: list[str] = []

    for payload_kind, payload_annotation in envelope_hints.items():
        payload_type = _unwrap_optional(payload_annotation)
        if not isinstance(payload_type, type):
            continue
        payload_hints = get_type_hints(payload_type, globalns=vars(cucumber_messages_module))
        if not governance_fields.intersection(payload_hints.keys()):
            continue
        expected_status_capable.append(payload_kind)
        implementation_status_hint = payload_hints.get("implementation_status")
        if implementation_status_hint is not None and not _is_optional(implementation_status_hint):
            expected_required.append(payload_kind)

    assert STATUS_CAPABLE_PAYLOAD_KINDS == tuple(expected_status_capable)
    assert REQUIRED_STATUS_PAYLOAD_KINDS == tuple(expected_required)
    optional_from_protocol = tuple(
        payload for payload in STATUS_CAPABLE_PAYLOAD_KINDS if payload not in REQUIRED_STATUS_PAYLOAD_KINDS
    )
    assert optional_from_protocol == OPTIONAL_STATUS_PAYLOAD_KINDS
