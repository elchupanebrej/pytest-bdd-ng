"""Deterministic comparisons between named Messages capability baselines."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterable

    from pytest_cuke.model.message_capability import MessageCapability
    from pytest_cuke.model.message_status_governance import CapabilityDecision


@dataclass(frozen=True, slots=True)
class BaselineDiffRecord:
    previous_baseline: str
    current_baseline: str
    added_capability_ids: tuple[str, ...]
    changed_capability_ids: tuple[str, ...]
    removed_capability_ids: tuple[str, ...]
    added_decision_ids: tuple[str, ...]
    changed_decision_ids: tuple[str, ...]
    removed_decision_ids: tuple[str, ...]


def _capability_signature(capability: MessageCapability) -> tuple[object, ...]:
    return (
        capability.name,
        capability.description,
        capability.category,
        tuple(sorted(capability.affects)),
        capability.source_reference,
        capability.relevance,
    )


def _decision_signature(decision: CapabilityDecision) -> tuple[object, ...]:
    return (decision.status, decision.comment)


def build_baseline_diff(
    *,
    previous_baseline: str,
    current_baseline: str,
    previous_capabilities: Iterable[MessageCapability],
    current_capabilities: Iterable[MessageCapability],
    previous_decisions: Iterable[CapabilityDecision] = (),
    current_decisions: Iterable[CapabilityDecision] = (),
) -> BaselineDiffRecord:
    """Compare schema inventory and decisions without mutating either input."""
    previous = {capability.capability_id: capability for capability in previous_capabilities}
    current = {capability.capability_id: capability for capability in current_capabilities}
    previous_ids = set(previous)
    current_ids = set(current)

    previous_governance = {
        (decision.capability_id, decision.release_target): decision for decision in previous_decisions
    }
    current_governance = {(decision.capability_id, decision.release_target): decision for decision in current_decisions}
    previous_governance_ids = set(previous_governance)
    current_governance_ids = set(current_governance)

    changed_decisions = {
        key
        for key in previous_governance_ids & current_governance_ids
        if _decision_signature(previous_governance[key]) != _decision_signature(current_governance[key])
    }

    return BaselineDiffRecord(
        previous_baseline=previous_baseline,
        current_baseline=current_baseline,
        added_capability_ids=tuple(sorted(current_ids - previous_ids)),
        changed_capability_ids=tuple(
            sorted(
                capability_id
                for capability_id in previous_ids & current_ids
                if _capability_signature(previous[capability_id]) != _capability_signature(current[capability_id])
            )
        ),
        removed_capability_ids=tuple(sorted(previous_ids - current_ids)),
        added_decision_ids=tuple(
            sorted(
                f"{capability_id}@{release_target}"
                for capability_id, release_target in current_governance_ids - previous_governance_ids
            )
        ),
        changed_decision_ids=tuple(
            sorted(f"{capability_id}@{release_target}" for capability_id, release_target in changed_decisions)
        ),
        removed_decision_ids=tuple(
            sorted(
                f"{capability_id}@{release_target}"
                for capability_id, release_target in previous_governance_ids - current_governance_ids
            )
        ),
    )


def baseline_diff_to_dict(diff: BaselineDiffRecord) -> dict[str, object]:
    """Serialize a diff record with stable JSON field ordering."""
    return {
        "added_capability_ids": list(diff.added_capability_ids),
        "added_decision_ids": list(diff.added_decision_ids),
        "changed_capability_ids": list(diff.changed_capability_ids),
        "changed_decision_ids": list(diff.changed_decision_ids),
        "current_baseline": diff.current_baseline,
        "previous_baseline": diff.previous_baseline,
        "removed_capability_ids": list(diff.removed_capability_ids),
        "removed_decision_ids": list(diff.removed_decision_ids),
    }


__all__ = ["BaselineDiffRecord", "baseline_diff_to_dict", "build_baseline_diff"]
