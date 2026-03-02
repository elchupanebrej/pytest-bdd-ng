from __future__ import annotations

import json
from typing import TYPE_CHECKING, TypeVar

from cucumber_messages import Envelope as Message  # type:ignore[attr-defined]

from pytest_bdd.model.message_converter import message_converter
from pytest_bdd.model.message_outcome_mapping import OutcomeMappingRule, validate_outcome_mappings
from pytest_bdd.model.message_validation import collect_observed_outcomes

_MessagePayload = TypeVar("_MessagePayload")

if TYPE_CHECKING:
    from collections.abc import Iterable
    from pathlib import Path

UNFOLDABLE_ATTRS: tuple[str, ...] = (
    "attachment",
    "external_attachment",
    "gherkin_document",
    "hook",
    "meta",
    "parameter_type",
    "parse_error",
    "pickle",
    "source",
    "step_definition",
    "suggestion",
    "test_case",
    "test_case_finished",
    "test_case_started",
    "test_run_finished",
    "test_run_hook_finished",
    "test_run_hook_started",
    "test_run_started",
    "test_step_finished",
    "test_step_started",
    "undefined_parameter_type",
)


def parse_ndjson_messages(path: Path) -> list[Message]:
    return [
        message_converter.from_dict(json.loads(line), Message)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def unfold_message(message: Message):
    for attr in UNFOLDABLE_ATTRS:
        payload = getattr(message, attr)
        if payload is not None:
            return payload
    message_text = "Empty envelope was given"
    raise ValueError(message_text)


def unfold_messages(messages: Iterable[Message]) -> list[object]:
    return [unfold_message(message) for message in messages]


def filter_payloads(payloads: Iterable[object], payload_type: type[_MessagePayload]) -> list[_MessagePayload]:
    return [payload for payload in payloads if isinstance(payload, payload_type)]


def payload_ids(payloads: Iterable[object]) -> list[str]:
    result: list[str] = []
    for payload in payloads:
        payload_id = getattr(payload, "id", None)
        if isinstance(payload_id, str):
            result.append(payload_id)
    return result


def assert_unique_payload_ids(payloads: Iterable[object]) -> None:
    ids = payload_ids(payloads)
    assert len(ids) == len(set(ids))


def assert_fixed_matrix_mapping_is_valid(
    messages: Iterable[Message],
    mapping_rules: list[OutcomeMappingRule],
) -> None:
    observed_outcomes = collect_observed_outcomes(list(messages))
    result = validate_outcome_mappings(mapping_rules, observed_outcomes)
    assert result.status == "pass"
    assert result.ambiguous_outcomes == ()
    assert result.unmapped_outcomes == ()
    assert result.missing_required_matrix_cases == ()
