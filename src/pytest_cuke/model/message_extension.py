from __future__ import annotations

from dataclasses import replace
from enum import Enum
from pathlib import PurePosixPath
from typing import Final, TypeAlias
from urllib.parse import urlsplit

from attrs import frozen

from pytest_cuke.const import (  # noqa: F401 - re-exported for existing imports
    PYTEST_OUTCOME_MEDIA_TYPE,
    PYTEST_SOURCE_MEDIA_TYPE,
    PYTEST_STEP_OUTCOME_MEDIA_TYPE,
)
from pytest_cuke.model.message_types import (
    Attachment,
    AttachmentContentEncoding,
    Envelope,
    message_field_names,
)

REFERENCE_MEDIA_TYPE: Final[str] = "text/uri-list"


class StepDefinitionPatternType(Enum):
    cucumber_expression = "CUCUMBER_EXPRESSION"
    regular_expression = "REGULAR_EXPRESSION"
    pytest_cuke_heuristic_expression = "PYTEST_BDD_HEURISTIC_EXPRESSION"
    pytest_cuke_string_expression = "PYTEST_BDD_STRING_EXPRESSION"
    pytest_cuke_regular_expression = "PYTEST_BDD_REGULAR_EXPRESSION"
    pytest_cuke_parse_expression = "PYTEST_BDD_PARSE_EXPRESSION"
    pytest_cuke_cfparse_expression = "PYTEST_BDD_CFPARSE_EXPRESSION"
    pytest_cuke_other_expression = "PYTEST_BDD_OTHER_EXPRESSION"


ExpressionType = StepDefinitionPatternType
EventEnvelope: TypeAlias = Envelope
PayloadKind: TypeAlias = str
PAYLOAD_KINDS: Final[tuple[str, ...]] = message_field_names(Envelope)
IDE_LAUNCH_MEDIA_TYPE: Final = "application/vnd.pytest-bdd.launch+json"
IDE_STEP_BINDING_MEDIA_TYPE: Final = "application/vnd.pytest-bdd.step-binding+json"
IDE_DIAGNOSTIC_MEDIA_TYPE: Final = "application/vnd.pytest-bdd.diagnostic+json"

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


def external_attachment_reference(envelope: Envelope) -> Envelope:
    """Replace an external attachment with a link-only regular attachment."""
    external = envelope.external_attachment
    if external is None:
        return envelope
    name = PurePosixPath(urlsplit(external.url).path).name
    if not name or name in {".", ".."}:
        name = "external-attachment.txt"
    return replace(
        envelope,
        external_attachment=None,
        attachment=Attachment(
            body=external.url,
            content_encoding=AttachmentContentEncoding.identity,
            media_type=REFERENCE_MEDIA_TYPE,
            file_name=name,
            test_case_started_id=external.test_case_started_id,
            test_run_hook_started_id=external.test_run_hook_started_id,
            test_step_id=external.test_step_id,
            timestamp=external.timestamp,
        ),
    )


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
    "IDE_DIAGNOSTIC_MEDIA_TYPE",
    "IDE_LAUNCH_MEDIA_TYPE",
    "IDE_STEP_BINDING_MEDIA_TYPE",
    "PAYLOAD_KINDS",
    "REFERENCE_MEDIA_TYPE",
    "STRUCTURAL_DEDUPLICATED_PAYLOAD_KINDS",
    "EnvelopeStatus",
    "EventEnvelope",
    "ExpressionType",
    "LifecycleCorrelation",
    "PayloadKind",
    "StepDefinitionPatternType",
    "external_attachment_reference",
    "get_payload_kind",
    "get_payload_merge_class",
    "has_single_payload",
]
