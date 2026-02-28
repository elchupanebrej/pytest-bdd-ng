from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Final, Literal, cast

if TYPE_CHECKING:
    from datetime import datetime

CapabilityStatus = Literal["Implemented", "Non-Implementable", "Not-Acceptable", "Not-Applicable", "Pending"]
LegacyCapabilityStatus = Literal["done", "non-implementable", "not-acceptable", "not-applicable", "pending"]
CapabilityStatusLike = CapabilityStatus | LegacyCapabilityStatus | str

CAPABILITY_STATUSES: Final[tuple[CapabilityStatus, ...]] = (
    "Implemented",
    "Non-Implementable",
    "Not-Acceptable",
    "Not-Applicable",
    "Pending",
)

NON_IMPLEMENTED_STATUSES: Final[set[CapabilityStatus]] = {
    "Non-Implementable",
    "Not-Acceptable",
    "Not-Applicable",
    "Pending",
}

MANDATORY_EVIDENCE_FIELDS: Final[tuple[str, ...]] = (
    "rationale",
    "decision_owner",
    "evidence_refs",
    "reviewed_at",
)

RELEASE_BLOCKER_STATUSES: Final[set[CapabilityStatus]] = {
    "Pending",
    "Not-Acceptable",
}

LEGACY_STATUS_ALIASES: Final[dict[str, CapabilityStatus]] = {
    "done": "Implemented",
    "non-implementable": "Non-Implementable",
    "not-acceptable": "Not-Acceptable",
    "not-applicable": "Not-Applicable",
    "pending": "Pending",
}


@dataclass(frozen=True, slots=True)
class CapabilityDecision:
    capability_id: str
    status: CapabilityStatus
    release_target: str
    rationale: str | None = None
    decision_owner: str | None = None
    evidence_refs: tuple[str, ...] = ()
    reviewed_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class DecisionValidationResult:
    accepted: bool
    missing_required_evidence_fields: tuple[str, ...]
    violations: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class StatusUniquenessResult:
    is_unique: bool
    duplicates: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class BlockerEvaluationResult:
    unresolved_blocker_capability_ids: tuple[str, ...]
    deferred_capability_ids: tuple[str, ...]
    missing_decision_capability_ids: tuple[str, ...]

    @property
    def blocker_count(self) -> int:
        return len(self.unresolved_blocker_capability_ids)


def _is_non_empty_text(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def normalize_capability_status(status: CapabilityStatusLike) -> CapabilityStatus | None:
    if status in CAPABILITY_STATUSES:
        return cast(CapabilityStatus, status)
    return LEGACY_STATUS_ALIASES.get(str(status).strip().lower())


def missing_required_evidence_fields(decision: CapabilityDecision) -> tuple[str, ...]:
    status = normalize_capability_status(decision.status)
    if status is None or status not in NON_IMPLEMENTED_STATUSES:
        return ()

    missing: list[str] = []
    if not _is_non_empty_text(decision.rationale):
        missing.append("rationale")
    if not _is_non_empty_text(decision.decision_owner):
        missing.append("decision_owner")
    if not decision.evidence_refs:
        missing.append("evidence_refs")
    if decision.reviewed_at is None:
        missing.append("reviewed_at")
    return tuple(missing)


def validate_capability_decision(decision: CapabilityDecision) -> DecisionValidationResult:
    violations: list[str] = []
    status = normalize_capability_status(decision.status)
    if status is None:
        violations.append(f"Unknown status: {decision.status}")
    missing = missing_required_evidence_fields(decision)
    accepted = not violations and not missing
    return DecisionValidationResult(
        accepted=accepted,
        missing_required_evidence_fields=missing,
        violations=tuple(violations),
    )


def ensure_single_status_per_capability(decisions: list[CapabilityDecision]) -> StatusUniquenessResult:
    seen: set[str] = set()
    duplicates: list[str] = []
    for decision in decisions:
        if decision.capability_id in seen:
            duplicates.append(decision.capability_id)
        else:
            seen.add(decision.capability_id)
    return StatusUniquenessResult(is_unique=not duplicates, duplicates=tuple(sorted(set(duplicates))))


def is_release_blocker_status(status: CapabilityStatus) -> bool:
    return status in RELEASE_BLOCKER_STATUSES


def evaluate_release_blockers(
    decisions: list[CapabilityDecision],
    *,
    relevant_capability_ids: tuple[str, ...] = (),
) -> BlockerEvaluationResult:
    index = {decision.capability_id: decision for decision in decisions}
    blocker_ids: set[str] = set()
    deferred_ids: set[str] = set()
    missing_ids: set[str] = set()

    for decision in decisions:
        status = normalize_capability_status(decision.status)
        if status is None:
            blocker_ids.add(decision.capability_id)
            continue
        if is_release_blocker_status(status):
            blocker_ids.add(decision.capability_id)
        elif status in {"Non-Implementable", "Not-Applicable"}:
            deferred_ids.add(decision.capability_id)

    for capability_id in relevant_capability_ids:
        if capability_id not in index:
            missing_ids.add(capability_id)
            blocker_ids.add(capability_id)

    return BlockerEvaluationResult(
        unresolved_blocker_capability_ids=tuple(sorted(blocker_ids)),
        deferred_capability_ids=tuple(sorted(deferred_ids)),
        missing_decision_capability_ids=tuple(sorted(missing_ids)),
    )
