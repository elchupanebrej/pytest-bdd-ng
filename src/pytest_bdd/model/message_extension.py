from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Final, Literal, TypeAlias

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


PayloadKind: TypeAlias = Literal[
    "attachment",
    "gherkin_document",
    "hook",
    "meta",
    "parameter_type",
    "pickle",
    "source",
    "step_definition",
    "test_case",
    "test_case_finished",
    "test_case_started",
    "test_run_finished",
    "test_run_started",
    "test_step_finished",
    "test_step_started",
]

EventEnvelope: TypeAlias = _BaseEnvelope

PAYLOAD_KINDS: Final[tuple[PayloadKind, ...]] = (
    "attachment",
    "gherkin_document",
    "hook",
    "meta",
    "parameter_type",
    "pickle",
    "source",
    "step_definition",
    "test_case",
    "test_case_finished",
    "test_case_started",
    "test_run_finished",
    "test_run_started",
    "test_step_finished",
    "test_step_started",
)

STATUS_CAPABLE_PAYLOAD_KINDS: Final[tuple[PayloadKind, ...]] = (
    "test_step_finished",
    "test_case_finished",
    "test_run_finished",
    "attachment",
)

REQUIRED_STATUS_PAYLOAD_KINDS: Final[tuple[PayloadKind, ...]] = (
    "test_step_finished",
    "test_case_finished",
)

OPTIONAL_STATUS_PAYLOAD_KINDS: Final[tuple[PayloadKind, ...]] = (
    "test_run_finished",
    "attachment",
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
