from __future__ import annotations

from enum import Enum
from typing import Final, TypeAlias

from attrs import frozen

from messages import Envelope
from messages import ExpressionType as _BaseExpressionType

StepDefinitionPatternType = Enum(
    "StepDefinitionPatternType",
    {
        **{n: m.value for n, m in _BaseExpressionType.__members__.items()},
        "pytest_bdd_heuristic_expression": "PYTEST_BDD_HEURISTIC_EXPRESSION",
        "pytest_bdd_string_expression": "PYTEST_BDD_STRING_EXPRESSION",
        "pytest_bdd_regular_expression": "PYTEST_BDD_REGULAR_EXPRESSION",
        "pytest_bdd_parse_expression": "PYTEST_BDD_PARSE_EXPRESSION",
        "pytest_bdd_cfparse_expression": "PYTEST_BDD_CFPARSE_EXPRESSION",
        "pytest_bdd_other_expression": "PYTEST_BDD_OTHER_EXPRESSION",
    },
)
ExpressionType = StepDefinitionPatternType
EventEnvelope: TypeAlias = Envelope
PayloadKind: TypeAlias = str
PAYLOAD_KINDS: Final[tuple[str, ...]] = tuple(Envelope.model_fields.keys())

CONTROLLER_SINGULAR_PAYLOAD_KINDS: Final[tuple[PayloadKind, ...]] = ("meta", "test_run_started", "test_run_finished")
STRUCTURAL_DEDUPLICATED_PAYLOAD_KINDS: Final[tuple[PayloadKind, ...]] = (
    "source",
    "gherkin_document",
    "pickle",
    "step_definition",
    "parameter_type",
    "hook",
    "test_case",
)
EXECUTION_PRESERVED_PAYLOAD_KINDS: Final[tuple[PayloadKind, ...]] = tuple(
    k for k in PAYLOAD_KINDS if k not in CONTROLLER_SINGULAR_PAYLOAD_KINDS + STRUCTURAL_DEDUPLICATED_PAYLOAD_KINDS
)


@frozen
class LifecycleCorrelation:
    run_id: str
    scenario_attempt_id: str
    worker_id: str
    attempt_index: int
    step_id: str | None = None


@frozen
class EnvelopeStatus:
    implementation_status: str | None = None
    implementation_comment: str | None = None
    comment_present: bool = False
    hook_origin: str | None = None


def get_payload_kind(message: EventEnvelope) -> PayloadKind | None:
    matched = [k for k in PAYLOAD_KINDS if getattr(message, k, None) is not None]
    return matched[0] if len(matched) == 1 else None


def has_single_payload(message: EventEnvelope) -> bool:
    return get_payload_kind(message) is not None


def get_payload_merge_class(payload_kind: PayloadKind | None) -> str | None:
    if payload_kind is None:
        return None
    if payload_kind in CONTROLLER_SINGULAR_PAYLOAD_KINDS:
        return "controller_singular"
    if payload_kind in STRUCTURAL_DEDUPLICATED_PAYLOAD_KINDS:
        return "structural_deduplicated"
    if payload_kind in EXECUTION_PRESERVED_PAYLOAD_KINDS:
        return "execution_preserved"
    return None


__all__ = [
    "CONTROLLER_SINGULAR_PAYLOAD_KINDS",
    "EXECUTION_PRESERVED_PAYLOAD_KINDS",
    "PAYLOAD_KINDS",
    "STRUCTURAL_DEDUPLICATED_PAYLOAD_KINDS",
    "EnvelopeStatus",
    "EventEnvelope",
    "ExpressionType",
    "LifecycleCorrelation",
    "PayloadKind",
    "StepDefinitionPatternType",
    "get_payload_kind",
    "get_payload_merge_class",
    "has_single_payload",
]
