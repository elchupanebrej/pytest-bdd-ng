"""Provide message stream assertions helpers."""

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
    """Parse ndjson messages."""
    return [
        message_converter.from_dict(json.loads(line), Message)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def unfold_message(message: Message):
    """
    Handle unfold message.

    Raises:
        ValueError: If the operation cannot be completed.

    """
    for attr in UNFOLDABLE_ATTRS:
        payload = getattr(message, attr)
        if payload is not None:
            return payload
    message_text = "Empty envelope was given"
    raise ValueError(message_text)


def unfold_messages(messages: Iterable[Message]) -> list[object]:
    """Handle unfold messages."""
    return [unfold_message(message) for message in messages]


def filter_payloads(payloads: Iterable[object], payload_type: type[_MessagePayload]) -> list[_MessagePayload]:
    """Handle filter payloads."""
    return [payload for payload in payloads if isinstance(payload, payload_type)]


def payload_ids(payloads: Iterable[object]) -> list[str]:
    """Handle payload ids."""
    result: list[str] = []
    for payload in payloads:
        payload_id = getattr(payload, "id", None)
        if isinstance(payload_id, str):
            result.append(payload_id)
    return result


def assert_unique_payload_ids(payloads: Iterable[object]) -> None:
    """Assert unique payload ids."""
    ids = payload_ids(payloads)
    assert len(ids) == len(set(ids))


def assert_fixed_matrix_mapping_is_valid(
    messages: Iterable[Message],
    mapping_rules: list[OutcomeMappingRule],
) -> None:
    """Assert fixed matrix mapping is valid."""
    observed_outcomes = collect_observed_outcomes(list(messages))
    result = validate_outcome_mappings(mapping_rules, observed_outcomes)
    assert result.status == "pass"
    assert result.ambiguous_outcomes == ()
    assert result.unmapped_outcomes == ()
    assert result.missing_required_matrix_cases == ()


def payload_kinds(messages: Iterable[Message]) -> list[str]:
    """Handle payload kinds."""
    result: list[str] = []
    for message in messages:
        for attr in UNFOLDABLE_ATTRS:
            if getattr(message, attr, None) is not None:
                result.append(attr)
                break
    return result


def count_payload_kinds(messages: Iterable[Message]) -> dict[str, int]:
    """Handle count payload kinds."""
    counts: dict[str, int] = {}
    for payload_kind in payload_kinds(messages):
        counts[payload_kind] = counts.get(payload_kind, 0) + 1
    return counts


def payload_attr_values(
    messages: Iterable[Message],
    payload_type: type[_MessagePayload],
    attr_name: str,
) -> set[str]:
    """Handle payload attr values."""
    values: set[str] = set()
    for payload in filter_payloads(unfold_messages(messages), payload_type):
        value = getattr(payload, attr_name, None)
        if isinstance(value, str) and value:
            values.add(value)
    return values


def _split_worker_gateway(worker_id: str) -> tuple[str | None, str]:
    gateway_mode, separator, normalized_worker_id = worker_id.partition(":")
    if separator and gateway_mode in {"socket", "via", "ssh", "popen"} and normalized_worker_id:
        return gateway_mode, normalized_worker_id
    return None, worker_id


def worker_ids_for_payloads(messages: Iterable[Message], payload_type: type[_MessagePayload]) -> set[str]:
    """Handle worker ids for payloads."""
    worker_ids: set[str] = set()
    for worker_id in payload_attr_values(messages, payload_type, "worker_id"):
        _gateway_mode, normalized_worker_id = _split_worker_gateway(worker_id)
        worker_ids.add(normalized_worker_id)
    return worker_ids


def gateway_modes_for_payloads(messages: Iterable[Message], payload_type: type[_MessagePayload]) -> set[str]:
    """Handle gateway modes for payloads."""
    gateway_modes = payload_attr_values(messages, payload_type, "gateway_mode")
    if gateway_modes:
        return gateway_modes
    derived_gateway_modes: set[str] = set()
    for worker_id in payload_attr_values(messages, payload_type, "worker_id"):
        gateway_mode, _normalized_worker_id = _split_worker_gateway(worker_id)
        if gateway_mode is not None:
            derived_gateway_modes.add(gateway_mode)
    return derived_gateway_modes


def worker_ids_with_prefix(messages: Iterable[Message], payload_type: type[_MessagePayload], prefix: str) -> set[str]:
    """Handle worker ids with prefix."""
    return {worker_id for worker_id in worker_ids_for_payloads(messages, payload_type) if worker_id.startswith(prefix)}


def assert_single_output_file(paths: Iterable[Path]) -> Path:
    """Assert single output file."""
    concrete_paths = [path for path in paths if path.exists()]
    assert len(concrete_paths) == 1
    return concrete_paths[0]


def message_json_lines(path: Path) -> list[dict[str, object]]:
    """Handle message json lines."""
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def diagnostic_messages(lines: Iterable[dict[str, object]]) -> list[str]:
    """Handle diagnostic messages."""
    messages: list[str] = []
    for line in lines:
        diagnostic_message = line.get("diagnosticMessage")
        if isinstance(diagnostic_message, str):
            messages.append(diagnostic_message)
    return messages
