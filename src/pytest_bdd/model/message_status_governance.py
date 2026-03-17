from __future__ import annotations

from typing import TYPE_CHECKING, Final, Literal, cast

from attrs import frozen

if TYPE_CHECKING:
    from datetime import datetime

CapabilityStatus = Literal[
    "Implemented",
    "Partly-Applicable",
    "Non-Implementable",
    "Not-Acceptable",
    "Not-Applicable",
    "Pending",
]
LegacyCapabilityStatus = Literal[
    "done",
    "partly-applicable",
    "partially-applicable",
    "non-implementable",
    "not-acceptable",
    "not-applicable",
    "pending",
]
CapabilityStatusLike = CapabilityStatus | LegacyCapabilityStatus | str

CAPABILITY_STATUSES: Final[tuple[CapabilityStatus, ...]] = (
    "Implemented",
    "Partly-Applicable",
    "Non-Implementable",
    "Not-Acceptable",
    "Not-Applicable",
    "Pending",
)

NON_IMPLEMENTED_STATUSES: Final[set[CapabilityStatus]] = {
    "Partly-Applicable",
    "Non-Implementable",
    "Not-Acceptable",
    "Not-Applicable",
    "Pending",
}

MANDATORY_SCOPE_FORBIDDEN_STATUSES: Final[set[CapabilityStatus]] = {
    "Partly-Applicable",
    "Non-Implementable",
    "Not-Acceptable",
    "Not-Applicable",
}

MANDATORY_EVIDENCE_FIELDS: Final[tuple[str, ...]] = (
    "rationale",
    "decision_owner",
    "evidence_refs",
    "reviewed_at",
)

NON_IMPLEMENTABLE_REQUIRED_FIELDS: Final[tuple[str, ...]] = (
    "recheck_trigger",
    "hard_limitation",
)

FORBIDDEN_NON_IMPLEMENTABLE_PATTERNS: Final[tuple[str, ...]] = (
    "not implemented yet",
    "future work",
    "not observed in this test only",
)

RELEASE_BLOCKER_STATUSES: Final[set[CapabilityStatus]] = {
    "Pending",
    "Not-Acceptable",
}

LEGACY_STATUS_ALIASES: Final[dict[str, CapabilityStatus]] = {
    "done": "Implemented",
    "partly-applicable": "Partly-Applicable",
    "partially-applicable": "Partly-Applicable",
    "non-implementable": "Non-Implementable",
    "not-acceptable": "Not-Acceptable",
    "not-applicable": "Not-Applicable",
    "pending": "Pending",
}


@frozen
class CapabilityDecision:
    capability_id: str
    status: CapabilityStatus
    release_target: str
    rationale: str | None = None
    hard_limitation: str | None = None
    decision_owner: str | None = None
    evidence_refs: tuple[str, ...] = ()
    reviewed_at: datetime | None = None
    recheck_trigger: str | None = None


@frozen
class DecisionValidationResult:
    accepted: bool
    missing_required_evidence_fields: tuple[str, ...]
    violations: tuple[str, ...]


@frozen
class StatusUniquenessResult:
    is_unique: bool
    duplicates: tuple[str, ...]


@frozen
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
    if status == "Non-Implementable":
        if not _is_non_empty_text(decision.recheck_trigger):
            missing.append("recheck_trigger")
        if not _is_non_empty_text(decision.hard_limitation):
            missing.append("hard_limitation")
    return tuple(missing)


def validate_non_implementable_policy(decision: CapabilityDecision) -> tuple[str, ...]:
    status = normalize_capability_status(decision.status)
    if status != "Non-Implementable":
        return ()

    rationale = decision.rationale or ""
    hard_limitation = decision.hard_limitation or ""
    combined_text = f"{rationale}\n{hard_limitation}".lower()

    return tuple(
        f"non-implementable rationale uses forbidden phrase: '{pattern}'"
        for pattern in FORBIDDEN_NON_IMPLEMENTABLE_PATTERNS
        if pattern in combined_text
    )


def validate_partly_applicable_policy(decision: CapabilityDecision) -> tuple[str, ...]:
    status = normalize_capability_status(decision.status)
    if status != "Partly-Applicable":
        return ()

    rationale = (decision.rationale or "").lower()
    if "language" in rationale and ("model" in rationale or "runtime" in rationale):
        return ()
    return (
        (
            "partly-applicable rationale must explain language/runtime model mismatch "
            "(for example: no native language-equivalent model in current runtime)"
        ),
    )


def validate_capability_decision(decision: CapabilityDecision) -> DecisionValidationResult:
    violations: list[str] = []
    status = normalize_capability_status(decision.status)
    if status is None:
        violations.append(f"Unknown status: {decision.status}")
    violations.extend(validate_non_implementable_policy(decision))
    violations.extend(validate_partly_applicable_policy(decision))
    missing = missing_required_evidence_fields(decision)
    accepted = not violations and not missing
    return DecisionValidationResult(
        accepted=accepted,
        missing_required_evidence_fields=missing,
        violations=tuple(violations),
    )


def validate_mandatory_scope_decision(
    decision: CapabilityDecision,
    *,
    mandatory_capability_ids: set[str],
) -> tuple[str, ...]:
    if decision.capability_id not in mandatory_capability_ids:
        return ()
    status = normalize_capability_status(decision.status)
    if status in MANDATORY_SCOPE_FORBIDDEN_STATUSES:
        message = (
            "mandatory scope capabilities cannot use deferred statuses "
            f"({', '.join(sorted(MANDATORY_SCOPE_FORBIDDEN_STATUSES))}): {decision.capability_id} -> {status}"
        )
        return (message,)
    return ()


def ensure_single_status_per_capability(decisions: list[CapabilityDecision]) -> StatusUniquenessResult:
    seen: set[tuple[str, str]] = set()
    duplicates: list[str] = []
    for decision in decisions:
        uniqueness_key = (decision.capability_id, decision.release_target)
        if uniqueness_key in seen:
            duplicates.append(f"{decision.capability_id}@{decision.release_target}")
        else:
            seen.add(uniqueness_key)
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
        elif status in {"Partly-Applicable", "Non-Implementable", "Not-Applicable"}:
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
