"""Decision loading and validation for message capability governance."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

from pytest_bdd.model.coverage.inventory import canonical_capability_id
from pytest_bdd.model.message_status_governance import (
    CapabilityDecision,
    ensure_single_status_per_capability,
    normalize_capability_status,
    validate_capability_decision,
    validate_mandatory_scope_decision,
)

if TYPE_CHECKING:
    from pytest_bdd.model.message_baseline_diff import BaselineDiffRecord


def _load_decisions(path: Path) -> list[CapabilityDecision]:
    from pytest_bdd.script.message_capability_governance.schema import _load_json

    payload = _load_json(path)
    if isinstance(payload, dict):
        payload = [payload]
    if not isinstance(payload, list):
        msg = f"Expected decision list in {path}"
        raise TypeError(msg)

    result: list[CapabilityDecision] = []
    for item in payload:
        if not isinstance(item, dict):
            continue
        reviewed_at_raw = item.get("reviewed_at")
        reviewed_at = None
        if isinstance(reviewed_at_raw, str) and reviewed_at_raw:
            reviewed_at = datetime.fromisoformat(reviewed_at_raw)
        normalized_status = normalize_capability_status(str(item["status"]))
        if normalized_status is None:
            msg = f"Unknown capability status '{item['status']}' in {path}"
            raise ValueError(msg)
        result.append(
            CapabilityDecision(
                capability_id=str(item["capability_id"]),
                status=normalized_status,
                rationale=item.get("rationale"),
                hard_limitation=item.get("hard_limitation"),
                decision_owner=item.get("decision_owner"),
                evidence_refs=tuple(item.get("evidence_refs") or []),
                reviewed_at=reviewed_at,
                release_target=str(item.get("release_target", "next-release")),
                recheck_trigger=item.get("recheck_trigger"),
            ),
        )
    return result


def _validate_decisions(
    decisions: list[CapabilityDecision],
    *,
    mandatory_capability_ids: set[str] | None = None,
) -> list[CapabilityDecision]:
    canonical_decisions = [
        CapabilityDecision(
            capability_id=canonical_capability_id(decision.capability_id),
            status=decision.status,
            release_target=decision.release_target,
            rationale=decision.rationale,
            hard_limitation=decision.hard_limitation,
            decision_owner=decision.decision_owner,
            evidence_refs=decision.evidence_refs,
            reviewed_at=decision.reviewed_at,
            recheck_trigger=decision.recheck_trigger,
        )
        for decision in decisions
    ]

    uniqueness = ensure_single_status_per_capability(canonical_decisions)
    if not uniqueness.is_unique:
        msg = f"Duplicate capability decisions found for: {', '.join(uniqueness.duplicates)}"
        raise ValueError(msg)

    mandatory_ids = mandatory_capability_ids or set()
    validated: list[CapabilityDecision] = []
    for decision in canonical_decisions:
        validation = validate_capability_decision(decision)
        if not validation.accepted:
            parts: list[str] = []
            if validation.violations:
                parts.append("; ".join(validation.violations))
            if validation.missing_required_evidence_fields:
                parts.append(
                    "missing required evidence fields: " + ", ".join(validation.missing_required_evidence_fields),
                )
            details = "; ".join(parts) if parts else "invalid decision"
            msg = f"Invalid decision for '{decision.capability_id}': {details}"
            raise ValueError(msg)
        mandatory_violations = validate_mandatory_scope_decision(
            decision,
            mandatory_capability_ids=mandatory_ids,
        )
        if mandatory_violations:
            msg = "; ".join(mandatory_violations)
            raise ValueError(msg)
        validated.append(decision)

    return validated


def _select_active_decisions(
    decisions: list[CapabilityDecision],
    *,
    release_target: str,
) -> dict[str, CapabilityDecision]:
    grouped: dict[str, list[CapabilityDecision]] = {}
    for decision in decisions:
        grouped.setdefault(decision.capability_id, []).append(decision)

    active: dict[str, CapabilityDecision] = {}
    for capability_id, candidates in grouped.items():
        exact = [decision for decision in candidates if decision.release_target == release_target]
        if exact:
            active[capability_id] = exact[0]
            continue

        next_release = [decision for decision in candidates if decision.release_target == "next-release"]
        if next_release:
            active[capability_id] = next_release[0]
            continue

        active[capability_id] = max(
            candidates,
            key=lambda decision: (
                decision.reviewed_at.isoformat() if decision.reviewed_at is not None else "",
                decision.release_target,
            ),
        )
    return active


def _load_baseline_diff(path: Path) -> BaselineDiffRecord:
    from datetime import timezone

    from pytest_bdd.model.message_baseline_diff import BaselineDiffRecord
    from pytest_bdd.script.message_capability_governance.schema import _load_json

    payload = _load_json(path)
    if not isinstance(payload, dict):
        msg = f"Expected baseline diff object in {path}"
        raise TypeError(msg)
    generated_at_raw = payload.get("generated_at")
    generated_at = (
        datetime.fromisoformat(generated_at_raw) if isinstance(generated_at_raw, str) else datetime.now(timezone.utc)
    )
    return BaselineDiffRecord(
        diff_run_id=str(payload["diff_run_id"]),
        previous_baseline=str(payload["previous_baseline"]),
        current_baseline=str(payload["current_baseline"]),
        added_capability_ids=tuple(payload.get("added_capability_ids") or []),
        changed_capability_ids=tuple(payload.get("changed_capability_ids") or []),
        removed_capability_ids=tuple(payload.get("removed_capability_ids") or []),
        generated_at=generated_at,
    )
