from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Final, TypeAlias, get_args, get_type_hints

from cucumber_messages import *  # type:ignore[import-untyped]  # noqa: F403 This module patches the cucumber_messages module to extend it with pytest_bdd specific types
from cucumber_messages import Envelope as _BaseEnvelope
from cucumber_messages import StepDefinitionPattern as _BaseStepDefinitionPattern
from cucumber_messages import StepDefinitionPatternType as _BaseStepDefinitionPatternType

StepDefinitionPatternType = Enum(  # type:ignore[misc]
    "StepDefinitionPatternType",
    dict(
        **{name: member.value for name, member in _BaseStepDefinitionPatternType.__members__.items()},
        pytest_bdd_heuristic_expression="PYTEST_BDD_HEURISTIC_EXPRESSION",
        pytest_bdd_string_expression="PYTEST_BDD_STRING_EXPRESSION",
        pytest_bdd_regular_expression="PYTEST_BDD_REGULAR_EXPRESSION",
        pytest_bdd_parse_expression="PYTEST_BDD_PARSE_EXPRESSION",
        pytest_bdd_cfparse_expression="PYTEST_BDD_CFPARSE_EXPRESSION",
        pytest_bdd_other_expression="PYTEST_BDD_OTHER_EXPRESSION",
    ),
)


@dataclass
class StepDefinitionPattern(_BaseStepDefinitionPattern):
    type: StepDefinitionPatternType


EventEnvelope: TypeAlias = _BaseEnvelope

# Keep payload kinds auto-synced with cucumber-messages Envelope schema to
# avoid manual maintenance on library upgrades.
PAYLOAD_KINDS: Final[tuple[str, ...]] = tuple(_BaseEnvelope.__annotations__.keys())
PayloadKind: TypeAlias = str

_GOVERNANCE_STATUS_FIELDS: Final[tuple[str, ...]] = (
    "implementation_status",
    "implementation_comment",
    "hook_origin",
)

_ENVELOPE_HINTS: Final[dict[str, object]] = get_type_hints(_BaseEnvelope, globalns=globals())


def _is_optional_type(value: object) -> bool:
    return any(option is type(None) for option in get_args(value))


def _unwrap_optional(value: object) -> object:
    args = tuple(option for option in get_args(value) if option is not type(None))
    if len(args) == 1:
        return args[0]
    return value


def _payload_field_hints(payload_kind: PayloadKind) -> dict[str, object]:
    payload_annotation = _ENVELOPE_HINTS.get(payload_kind)
    if payload_annotation is None:
        return {}
    payload_type = _unwrap_optional(payload_annotation)
    if not isinstance(payload_type, type):
        return {}
    return get_type_hints(payload_type, globalns=globals())


_PAYLOAD_HINTS_BY_KIND: Final[dict[PayloadKind, dict[str, object]]] = {
    payload_kind: _payload_field_hints(payload_kind) for payload_kind in PAYLOAD_KINDS
}

STATUS_CAPABLE_PAYLOAD_KINDS: Final[tuple[PayloadKind, ...]] = tuple(
    payload_kind
    for payload_kind in PAYLOAD_KINDS
    if any(field_name in _PAYLOAD_HINTS_BY_KIND[payload_kind] for field_name in _GOVERNANCE_STATUS_FIELDS)
)

REQUIRED_STATUS_PAYLOAD_KINDS: Final[tuple[PayloadKind, ...]] = tuple(
    payload_kind
    for payload_kind in STATUS_CAPABLE_PAYLOAD_KINDS
    if (
        "implementation_status" in _PAYLOAD_HINTS_BY_KIND[payload_kind]
        and not _is_optional_type(_PAYLOAD_HINTS_BY_KIND[payload_kind]["implementation_status"])
    )
)

OPTIONAL_STATUS_PAYLOAD_KINDS: Final[tuple[PayloadKind, ...]] = tuple(
    payload_kind for payload_kind in STATUS_CAPABLE_PAYLOAD_KINDS if payload_kind not in REQUIRED_STATUS_PAYLOAD_KINDS
)

NOT_APPLICABLE_STATUS_PAYLOAD_KINDS: Final[tuple[PayloadKind, ...]] = tuple(
    payload_kind for payload_kind in PAYLOAD_KINDS if payload_kind not in STATUS_CAPABLE_PAYLOAD_KINDS
)


@dataclass(frozen=True, slots=True)
class LifecycleCorrelation:
    run_id: str
    scenario_attempt_id: str
    worker_id: str
    attempt_index: int
    step_id: str | None = None


@dataclass(frozen=True, slots=True)
class EnvelopeStatus:
    implementation_status: str | None
    implementation_comment: str | None
    comment_present: bool
    hook_origin: str | None


def get_payload_kind(message: EventEnvelope) -> PayloadKind | None:
    matched_payload_kinds = [
        payload_kind for payload_kind in PAYLOAD_KINDS if getattr(message, payload_kind, None) is not None
    ]
    if len(matched_payload_kinds) != 1:
        return None
    return matched_payload_kinds[0]


def has_single_payload(message: EventEnvelope) -> bool:
    return get_payload_kind(message) is not None
