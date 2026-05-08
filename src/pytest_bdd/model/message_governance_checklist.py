"""Provide message governance checklist helpers."""

from __future__ import annotations

from typing import TYPE_CHECKING, Final, Literal

from attrs import frozen

from .message_capability import MessageCapability, capability_is_relevant
from .message_status_governance import (
    NON_IMPLEMENTED_STATUSES,
    CapabilityDecision,
    CapabilityStatus,
    evaluate_release_blockers,
    is_release_blocker_status,
    normalize_capability_status,
)

if TYPE_CHECKING:
    from .message_baseline_diff import BaselineDiffRecord

DEFAULT_CHECKLIST_NAME: Final[str] = "message-status-governance"
ChecklistDelta = Literal["unchanged", "added", "changed", "removed"]
ChecklistDisposition = Literal["approved", "blocked", "deferred"]


@frozen
class GovernanceChecklistEntry:
    """Represent governance checklist entry state."""

    capability_id: str
    status: CapabilityStatus
    comment_required: bool
    comment: str | None
    release_blocker: bool
    delta: ChecklistDelta
    disposition: ChecklistDisposition


@frozen
class GovernanceChecklist:
    """Represent governance checklist state."""

    checklist_name: str
    entries: tuple[GovernanceChecklistEntry, ...]
    unresolved_blockers: int


def _decision_index(decisions: list[CapabilityDecision]) -> dict[str, CapabilityDecision]:
    return {decision.capability_id: decision for decision in decisions}


def build_governance_checklist(
    capabilities: list[MessageCapability],
    decisions: list[CapabilityDecision],
    *,
    checklist_name: str = DEFAULT_CHECKLIST_NAME,
    baseline_diff: BaselineDiffRecord | None = None,
) -> GovernanceChecklist:
    """Build governance checklist."""
    index = _decision_index(decisions)
    added = set(baseline_diff.added_capability_ids) if baseline_diff is not None else set()
    changed = set(baseline_diff.changed_capability_ids) if baseline_diff is not None else set()
    removed = set(baseline_diff.removed_capability_ids) if baseline_diff is not None else set()

    relevant_ids = [capability.capability_id for capability in capabilities if capability_is_relevant(capability)]
    blocker_evaluation = evaluate_release_blockers(decisions, relevant_capability_ids=tuple(relevant_ids))
    blocker_ids = set(blocker_evaluation.unresolved_blocker_capability_ids)
    deferred_ids = set(blocker_evaluation.deferred_capability_ids)

    entries: list[GovernanceChecklistEntry] = []

    for capability_id in sorted(set(relevant_ids).union(removed)):
        decision = index.get(capability_id)
        if decision is None:
            status: CapabilityStatus = "Pending"
            comment: str | None = (
                "Decision is missing" if capability_id not in removed else "Capability removed from baseline"
            )
        else:
            status = normalize_capability_status(decision.status) or "Pending"
            comment = decision.rationale

        if capability_id in removed:
            delta: ChecklistDelta = "removed"
        elif capability_id in added:
            delta = "added"
        elif capability_id in changed:
            delta = "changed"
        else:
            delta = "unchanged"

        comment_required = status in NON_IMPLEMENTED_STATUSES
        release_blocker = capability_id in blocker_ids or (
            capability_id not in removed and is_release_blocker_status(status)
        )
        if capability_id in deferred_ids:
            disposition: ChecklistDisposition = "deferred"
        elif release_blocker:
            disposition = "blocked"
        else:
            disposition = "approved"

        entries.append(
            GovernanceChecklistEntry(
                capability_id=capability_id,
                status=status,
                comment_required=comment_required,
                comment=comment,
                release_blocker=release_blocker,
                delta=delta,
                disposition=disposition,
            )
        )

    unresolved_blockers = blocker_evaluation.blocker_count
    return GovernanceChecklist(
        checklist_name=checklist_name,
        entries=tuple(entries),
        unresolved_blockers=unresolved_blockers,
    )


def render_checklist_markdown(checklist: GovernanceChecklist) -> str:
    """Render checklist markdown."""
    lines = [
        f"# {checklist.checklist_name}",
        "",
        "| Capability ID | Status | Delta | Disposition | Comment Required | Release Blocker |",
        "|---------------|--------|-------|-------------|------------------|-----------------|",
    ]
    lines.extend(
        "| "
        f"{entry.capability_id} | {entry.status} | {entry.delta} | {entry.disposition} | "
        f"{str(entry.comment_required).lower()} | {str(entry.release_blocker).lower()} |"
        for entry in checklist.entries
    )
    lines.extend(("", f"Unresolved blockers: {checklist.unresolved_blockers}"))
    return "\n".join(lines)
