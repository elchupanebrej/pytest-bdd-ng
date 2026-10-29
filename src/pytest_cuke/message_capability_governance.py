"""Govern Cucumber Messages schema fields against runtime observations and release decisions."""

from __future__ import annotations

import json
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import TYPE_CHECKING, Literal

from pytest_cuke.message_ndjson import read_validated_ndjson
from pytest_cuke.message_schema_sync import resolve_upstream_release
from pytest_cuke.model.message_capability_inventory import (
    build_capability_inventory,
    capabilities_from_json,
    normalize_capability_id,
    normalize_capability_ids,
    normalize_field_name,
)
from pytest_cuke.model.message_extension import get_payload_kind
from pytest_cuke.model.message_status_governance import (
    GOVERNANCE_BLOCKING_STATUSES,
    NON_RUNTIME_CLASSIFICATION_STATUSES,
    CapabilityDecision,
    active_decisions_for_release,
    decision_to_dict,
    decisions_from_json,
)
from pytest_cuke.model.message_stream_validation import MessageStreamValidator
from pytest_cuke.model.message_types import Envelope, message_to_dict
from pytest_cuke.model.message_validation import MessageValidationError

if TYPE_CHECKING:
    from pytest_cuke.model.message_capability import MessageCapability

InputKind = Literal["runtime", "synthetic"]


def _snake_to_camel(value: str) -> str:
    head, *tail = value.split("_")
    return head + "".join(part[:1].upper() + part[1:] for part in tail)


def _observed_ids(envelopes: Iterable[Envelope]) -> tuple[str, ...]:
    observed: set[str] = set()

    def visit(value: object, payload_kind: str, path_parts: tuple[str, ...]) -> None:
        if isinstance(value, Mapping):
            for raw_name, child in value.items():
                if not isinstance(raw_name, str):
                    continue
                field_name = normalize_field_name(raw_name)
                child_path = (*path_parts, field_name)
                observed.add(normalize_capability_id(".".join((payload_kind, *child_path))))
                visit(child, payload_kind, child_path)
        elif isinstance(value, list):
            for child in value:
                visit(child, payload_kind, path_parts)

    for envelope in envelopes:
        payload_kind = get_payload_kind(envelope)
        if payload_kind is None:
            raise ValueError("Messages envelope has no recognized payload")
        wire = message_to_dict(envelope)
        payload = wire.get(_snake_to_camel(payload_kind))
        if not isinstance(payload, dict):
            raise ValueError(f"Messages {payload_kind} payload must serialize to an object")
        visit(payload, payload_kind, ())
    return tuple(sorted(observed))


def build_capability_report(
    envelopes: Iterable[Envelope],
    *,
    capabilities: Iterable[MessageCapability],
    decisions: Iterable[CapabilityDecision],
    baseline_release: str,
    input_kind: InputKind,
    mandatory_capability_ids: Iterable[str] = (),
    runtime_required_capability_ids: Iterable[str] = (),
    require_fully_governed: bool = False,
    require_runtime_required_covered: bool = False,
    require_non_runtime_classified: bool = False,
) -> dict[str, object]:
    """Build a deterministic coverage report; synthetic fields never count as runtime evidence."""
    if input_kind not in {"runtime", "synthetic"}:
        raise ValueError(f"input kind must be 'runtime' or 'synthetic', got {input_kind!r}")
    capability_records = tuple(capabilities)
    decision_records = decisions_from_json([_decision_to_raw(item) for item in decisions])
    inventory = {item.capability_id: item for item in capability_records}
    if len(inventory) != len(capability_records):
        raise ValueError("capability inventory contains duplicate normalized IDs")
    mandatory_ids = normalize_capability_ids(mandatory_capability_ids)
    runtime_ids = normalize_capability_ids(runtime_required_capability_ids)
    if not set(runtime_ids).issubset(mandatory_ids):
        outside = sorted(set(runtime_ids) - set(mandatory_ids))
        raise ValueError("runtime-required scope must be a subset of mandatory scope: " + ", ".join(outside))

    validator = MessageStreamValidator()
    accepted: list[Envelope] = []
    for position, envelope in enumerate(envelopes):
        try:
            accepted.append(validator.accept(envelope))
        except MessageValidationError as error:
            diagnostic = error.diagnostics[0]
            raise ValueError(f"invalid Messages envelope at record {position + 1}: {diagnostic.message}") from error
    diagnostics = validator.finish()
    if diagnostics:
        raise ValueError(f"invalid Messages stream: {diagnostics[0].message}")

    observed_ids = _observed_ids(accepted)
    observed_set = set(observed_ids)
    runtime_observed = observed_set if input_kind == "runtime" else set()
    sample_observed = observed_set if input_kind == "synthetic" else set()
    active_decisions = active_decisions_for_release(decision_records, baseline_release=baseline_release)
    capability_rows: list[dict[str, object]] = []
    for capability_id in sorted(inventory):
        capability = inventory[capability_id]
        decision = active_decisions.get(capability_id)
        if decision is not None:
            status = decision.status
            comment = decision.comment
        elif capability_id in runtime_observed:
            status = "Implemented"
            comment = None
        else:
            status = "Pending"
            comment = None
        capability_rows.append(
            {
                "capability_id": capability_id,
                "category": capability.category,
                "comment": comment,
                "description": capability.description,
                "mandatory": capability_id in mandatory_ids,
                "observed_runtime": capability_id in runtime_observed,
                "observed_sample": capability_id in sample_observed,
                "relevance": capability.relevance,
                "runtime_required": capability_id in runtime_ids,
                "source_reference": capability.source_reference,
                "status": status,
            }
        )

    relevant_ids = {item.capability_id for item in capability_records if item.relevance == "relevant"}
    missing_mandatory = sorted(set(mandatory_ids) - set(inventory))
    mandatory_violations = sorted(
        set(mandatory_ids)
        - {
            capability_id
            for capability_id in mandatory_ids
            if (decision := active_decisions.get(capability_id)) is not None and decision.status == "Implemented"
        }
    )
    missing_runtime = sorted(set(runtime_ids) - runtime_observed)
    non_runtime_relevant = relevant_ids - set(runtime_ids)
    non_runtime_uncovered = non_runtime_relevant - runtime_observed
    non_runtime_unclassified = sorted(
        capability_id
        for capability_id in non_runtime_uncovered
        if (decision := active_decisions.get(capability_id)) is None
        or decision.status not in NON_RUNTIME_CLASSIFICATION_STATUSES
    )
    classified_ids = {
        capability_id
        for capability_id, decision in active_decisions.items()
        if decision.status in NON_RUNTIME_CLASSIFICATION_STATUSES
    }
    failures: list[str] = []
    if require_fully_governed:
        if not mandatory_ids:
            failures.append("require-fully-governed: mandatory capability scope is empty")
        if mandatory_violations:
            failures.append(
                "require-fully-governed: missing Implemented decisions for: " + ", ".join(mandatory_violations)
            )
    if require_runtime_required_covered:
        if not runtime_ids:
            failures.append("require-runtime-required-covered: runtime-required capability scope is empty")
        if missing_runtime:
            failures.append(
                "require-runtime-required-covered: missing runtime observations for: " + ", ".join(missing_runtime)
            )
    if require_non_runtime_classified and non_runtime_unclassified:
        failures.append(
            "require-non-runtime-classified: missing explicit classifications for: "
            + ", ".join(non_runtime_unclassified)
        )

    summary = {
        "blocked_capabilities": sum(
            item["status"] in GOVERNANCE_BLOCKING_STATUSES
            or bool(item["mandatory"] and item["status"] != "Implemented")
            for item in capability_rows
        ),
        "implemented_capabilities": sum(item["status"] == "Implemented" for item in capability_rows),
        "mandatory_scope_violations": len(mandatory_violations),
        "non_runtime_classified": len(non_runtime_relevant & classified_ids),
        "non_runtime_covered": len(non_runtime_relevant & runtime_observed),
        "non_runtime_required_total": len(non_runtime_relevant),
        "observed_capabilities": len(observed_set),
        "runtime_required_covered": len(set(runtime_ids) & runtime_observed),
        "runtime_required_missing": len(missing_runtime),
        "runtime_required_total": len(runtime_ids),
        "total_capabilities": len(capability_rows),
        "total_relevant_capabilities": len(relevant_ids),
    }
    return {
        "baseline_release": baseline_release,
        "capabilities": capability_rows,
        "decisions": [decision_to_dict(active_decisions[key]) for key in sorted(active_decisions)],
        "gates": {"failures": failures, "passed": not failures},
        "observations": {
            "capability_ids": list(observed_ids),
            "record_count": len(accepted),
            "source_kind": input_kind,
        },
        "scope": {
            "mandatory_capability_ids": list(mandatory_ids),
            "missing_mandatory_capability_ids": missing_mandatory,
            "runtime_required_capability_ids": list(runtime_ids),
        },
        "summary": summary,
        "unmapped_observed_capability_ids": sorted(observed_set - set(inventory)),
    }


def _decision_to_raw(decision: CapabilityDecision) -> dict[str, object]:
    return {
        "capability_id": decision.capability_id,
        "status": decision.status,
        "release_target": decision.release_target,
        "comment": decision.comment,
    }


def load_capabilities_file(path: Path) -> tuple[MessageCapability, ...]:
    """Load and normalize a synchronized inventory JSON artifact."""
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError(f"cannot read capability inventory {path}: {error}") from error
    return capabilities_from_json(payload)


def load_decisions_file(path: Path) -> tuple[CapabilityDecision, ...]:
    """Load and validate a capability decision file."""
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError(f"cannot read capability decisions {path}: {error}") from error
    return decisions_from_json(payload)


def load_capability_ids_file(path: Path) -> tuple[str, ...]:
    """Load a newline-delimited scope file, ignoring blank and comment lines."""
    try:
        values = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeDecodeError) as error:
        raise ValueError(f"cannot read capability scope {path}: {error}") from error
    return normalize_capability_ids(
        line.strip() for line in values if line.strip() and not line.lstrip().startswith("#")
    )


def installed_capability_inventory() -> tuple[str, tuple[MessageCapability, ...]]:
    """Build an inventory from the installed package's pinned official schema baseline."""
    baseline_release, _ = resolve_upstream_release()
    schema_dir = Path(__file__).parent / "model" / "message_schemas"
    return baseline_release, build_capability_inventory(schema_dir, baseline_release=baseline_release)


__all__ = [
    "InputKind",
    "build_capability_report",
    "installed_capability_inventory",
    "load_capabilities_file",
    "load_capability_ids_file",
    "load_decisions_file",
    "read_validated_ndjson",
]
