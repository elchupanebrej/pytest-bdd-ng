"""Stable JSON and Markdown rendering for release capability decisions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal

from pytest_cuke.model.message_capability_inventory import normalize_capability_ids
from pytest_cuke.model.message_status_governance import (
    GOVERNANCE_BLOCKING_STATUSES,
    CapabilityDecision,
    CapabilityStatus,
    active_decisions_for_release,
)

if TYPE_CHECKING:
    from collections.abc import Iterable

    from pytest_cuke.model.message_baseline_diff import BaselineDiffRecord
    from pytest_cuke.model.message_capability import MessageCapability

ChecklistDelta = Literal["added", "changed", "removed", "unchanged"]


@dataclass(frozen=True, slots=True)
class GovernanceChecklistEntry:
    capability_id: str
    status: CapabilityStatus
    comment_required: bool
    comment: str | None
    release_blocker: bool
    delta: ChecklistDelta


@dataclass(frozen=True, slots=True)
class GovernanceChecklist:
    checklist_name: str
    baseline_release: str
    entries: tuple[GovernanceChecklistEntry, ...]
    unresolved_blockers: int


def build_governance_checklist(
    capabilities: Iterable[MessageCapability],
    decisions: Iterable[CapabilityDecision],
    *,
    baseline_release: str,
    mandatory_capability_ids: Iterable[str] = (),
    baseline_diff: BaselineDiffRecord | None = None,
) -> GovernanceChecklist:
    """Build a sorted checklist for relevant capabilities and removed baseline fields."""
    capability_map = {capability.capability_id: capability for capability in capabilities}
    decision_map = active_decisions_for_release(decisions, baseline_release=baseline_release)
    mandatory = set(normalize_capability_ids(mandatory_capability_ids))
    added = set(baseline_diff.added_capability_ids) if baseline_diff else set()
    changed = set(baseline_diff.changed_capability_ids) if baseline_diff else set()
    removed = set(baseline_diff.removed_capability_ids) if baseline_diff else set()
    ids = (
        {capability_id for capability_id, capability in capability_map.items() if capability.relevance == "relevant"}
        | removed
        | mandatory
    )

    entries: list[GovernanceChecklistEntry] = []
    for capability_id in sorted(ids):
        decision = decision_map.get(capability_id)
        status: CapabilityStatus = decision.status if decision else "Pending"
        if capability_id in removed:
            delta: ChecklistDelta = "removed"
        elif capability_id in added:
            delta = "added"
        elif capability_id in changed:
            delta = "changed"
        else:
            delta = "unchanged"
        release_blocker = status in GOVERNANCE_BLOCKING_STATUSES or (
            capability_id in mandatory and status != "Implemented"
        )
        entries.append(
            GovernanceChecklistEntry(
                capability_id=capability_id,
                status=status,
                comment_required=status != "Implemented",
                comment=decision.comment if decision else "Decision is missing",
                release_blocker=release_blocker,
                delta=delta,
            )
        )

    return GovernanceChecklist(
        checklist_name=f"Cucumber Messages {baseline_release} governance checklist",
        baseline_release=baseline_release,
        entries=tuple(entries),
        unresolved_blockers=sum(entry.release_blocker for entry in entries),
    )


def checklist_to_dict(checklist: GovernanceChecklist) -> dict[str, object]:
    """Serialize a checklist as deterministic JSON-compatible data."""
    return {
        "baseline_release": checklist.baseline_release,
        "checklist_name": checklist.checklist_name,
        "entries": [
            {
                "capability_id": entry.capability_id,
                "comment": entry.comment,
                "comment_required": entry.comment_required,
                "delta": entry.delta,
                "release_blocker": entry.release_blocker,
                "status": entry.status,
            }
            for entry in checklist.entries
        ],
        "summary": {
            "total_capabilities": len(checklist.entries),
            "unresolved_blockers": checklist.unresolved_blockers,
        },
    }


def render_checklist_markdown(checklist: GovernanceChecklist) -> str:
    """Render a stable release checklist suitable for review in source control."""
    rows = [
        f"# {checklist.checklist_name}",
        "",
        f"Baseline: `{checklist.baseline_release}`",
        f"Unresolved blockers: **{checklist.unresolved_blockers}**",
        "",
        "| Capability | Status | Change | Release blocker | Comment |",
        "| --- | --- | --- | --- | --- |",
    ]
    for entry in checklist.entries:
        comment = (entry.comment or "").replace("|", "\\|").replace("\n", " ")
        blocker = "yes" if entry.release_blocker else "no"
        rows.append(f"| `{entry.capability_id}` | {entry.status} | {entry.delta} | {blocker} | {comment} |")
    return "\n".join(rows) + "\n"


__all__ = [
    "GovernanceChecklist",
    "GovernanceChecklistEntry",
    "build_governance_checklist",
    "checklist_to_dict",
    "render_checklist_markdown",
]
