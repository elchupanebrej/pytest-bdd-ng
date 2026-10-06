"""Decision records and validation rules for Cucumber Messages capabilities."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Final, Literal

from pytest_cuke.model.message_capability_inventory import normalize_capability_id

if TYPE_CHECKING:
    from collections.abc import Iterable
CapabilityStatus = Literal[
    "Implemented",
    "Partly-Applicable",
    "Non-Implementable",
    "Not-Acceptable",
    "Not-Applicable",
    "Pending",
]

CAPABILITY_STATUSES: Final[tuple[CapabilityStatus, ...]] = (
    "Implemented",
    "Partly-Applicable",
    "Non-Implementable",
    "Not-Acceptable",
    "Not-Applicable",
    "Pending",
)
NON_RUNTIME_CLASSIFICATION_STATUSES: Final[frozenset[CapabilityStatus]] = frozenset(
    {"Partly-Applicable", "Non-Implementable", "Not-Acceptable", "Not-Applicable"}
)
GOVERNANCE_BLOCKING_STATUSES: Final[frozenset[CapabilityStatus]] = frozenset({"Pending", "Not-Acceptable"})


@dataclass(frozen=True, slots=True)
class CapabilityDecision:
    """A release-scoped implementation or non-runtime classification decision."""

    capability_id: str
    status: CapabilityStatus
    release_target: str
    comment: str | None = None


def normalize_capability_status(value: object) -> CapabilityStatus | None:
    """Return the canonical status spelling, accepting lowercase separators."""
    if not isinstance(value, str):
        return None
    normalized = value.strip().replace("_", "-").replace(" ", "-").lower()
    aliases: dict[str, CapabilityStatus] = {
        "implemented": "Implemented",
        "done": "Implemented",
        "partly-applicable": "Partly-Applicable",
        "partially-applicable": "Partly-Applicable",
        "non-implementable": "Non-Implementable",
        "not-acceptable": "Not-Acceptable",
        "not-applicable": "Not-Applicable",
        "pending": "Pending",
    }
    return aliases.get(normalized)


def validate_decisions(decisions: Iterable[CapabilityDecision]) -> tuple[CapabilityDecision, ...]:
    """Validate decision comments and reject duplicate or contradictory terminals."""
    normalized: list[CapabilityDecision] = []
    seen: dict[tuple[str, str], CapabilityStatus] = {}
    for decision in decisions:
        capability_id = normalize_capability_id(decision.capability_id)
        status = normalize_capability_status(decision.status)
        if not capability_id or "." not in capability_id:
            raise ValueError(f"invalid capability id: {decision.capability_id!r}")
        if status is None:
            raise ValueError(f"unknown status for {capability_id}: {decision.status!r}")
        release_target = decision.release_target.strip()
        if not release_target:
            raise ValueError(f"missing release_target for {capability_id}")
        comment = decision.comment.strip() if isinstance(decision.comment, str) else None
        if status != "Implemented" and not comment:
            raise ValueError(f"{capability_id}: status {status} requires a non-empty comment")

        key = (capability_id, release_target)
        previous = seen.get(key)
        if previous is not None:
            detail = "conflicting terminal statuses" if previous != status else "duplicate decision"
            raise ValueError(f"{detail} for {capability_id}@{release_target}: {previous} and {status}")
        seen[key] = status
        normalized.append(CapabilityDecision(capability_id, status, release_target, comment))

    return tuple(sorted(normalized, key=lambda item: (item.capability_id, item.release_target)))


def active_decisions_for_release(
    decisions: Iterable[CapabilityDecision],
    *,
    baseline_release: str,
) -> dict[str, CapabilityDecision]:
    """Select exact-release decisions, falling back only to explicit next-release defaults."""
    if not baseline_release.strip():
        raise ValueError("baseline release must be a non-empty name")
    grouped: dict[str, list[CapabilityDecision]] = {}
    for decision in validate_decisions(decisions):
        if decision.release_target in {baseline_release, "next-release"}:
            grouped.setdefault(decision.capability_id, []).append(decision)

    selected: dict[str, CapabilityDecision] = {}
    for capability_id, candidates in grouped.items():
        exact = next((item for item in candidates if item.release_target == baseline_release), None)
        default = next((item for item in candidates if item.release_target == "next-release"), None)
        selected_decision = exact if exact is not None else default
        if selected_decision is not None:
            selected[capability_id] = selected_decision
    return selected


def decisions_from_json(payload: object) -> tuple[CapabilityDecision, ...]:
    """Parse and validate a JSON decision array or an object with `decisions`."""
    if isinstance(payload, dict):
        payload = payload.get("decisions")
    if not isinstance(payload, list):
        raise ValueError("decision file must contain an array or an object with a 'decisions' array")

    decisions: list[CapabilityDecision] = []
    for index, item in enumerate(payload):
        if not isinstance(item, dict):
            raise ValueError(f"decision {index + 1} must be a JSON object")
        capability_id = item.get("capability_id", item.get("capabilityId"))
        status_value = item.get("status")
        release_target = item.get("release_target", item.get("releaseTarget", "next-release"))
        comment = item.get("comment", item.get("rationale"))
        status = normalize_capability_status(status_value)
        if not isinstance(capability_id, str):
            raise ValueError(f"decision {index + 1} is missing string capability_id")
        if status is None:
            raise ValueError(f"decision {index + 1} has unknown status {status_value!r}")
        if not isinstance(release_target, str):
            raise ValueError(f"decision {index + 1} has non-string release_target")
        if comment is not None and not isinstance(comment, str):
            raise ValueError(f"decision {index + 1} has non-string comment")
        decisions.append(CapabilityDecision(capability_id, status, release_target, comment))
    return validate_decisions(decisions)


def decision_to_dict(decision: CapabilityDecision) -> dict[str, object]:
    """Return stable JSON-compatible decision data."""
    result: dict[str, object] = {
        "capability_id": decision.capability_id,
        "release_target": decision.release_target,
        "status": decision.status,
    }
    if decision.comment is not None:
        result["comment"] = decision.comment
    return result


__all__ = [
    "CAPABILITY_STATUSES",
    "GOVERNANCE_BLOCKING_STATUSES",
    "NON_RUNTIME_CLASSIFICATION_STATUSES",
    "CapabilityDecision",
    "CapabilityStatus",
    "active_decisions_for_release",
    "decision_to_dict",
    "decisions_from_json",
    "normalize_capability_status",
    "validate_decisions",
]
