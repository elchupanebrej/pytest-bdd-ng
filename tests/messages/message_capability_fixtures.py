from __future__ import annotations

from datetime import UTC, datetime

from pytest_bdd.model.message_capability import MessageCapability
from pytest_bdd.model.message_outcome_mapping import OutcomeMappingRule
from pytest_bdd.model.message_status_governance import CapabilityDecision


def utc_now() -> datetime:
    return datetime.now(UTC)


def make_capability(
    capability_id: str,
    *,
    name: str = "Capability",
    description: str = "Capability description",
    category: str = "core",
    affects: tuple[str, ...] = ("emitted_envelope_payload",),
    baseline_release: str = "v32.0.1",
    source_reference: str = "upstream/messages",
) -> MessageCapability:
    return MessageCapability(
        capability_id=capability_id,
        baseline_release=baseline_release,
        name=name,
        description=description,
        category=category,
        affects=frozenset(affects),
        source_reference=source_reference,
    )


def make_decision(
    capability_id: str,
    *,
    status: str = "Implemented",
    rationale: str | None = None,
    decision_owner: str | None = None,
    evidence_refs: tuple[str, ...] = (),
    reviewed_at: datetime | None = None,
    release_target: str = "next-release",
) -> CapabilityDecision:
    return CapabilityDecision(
        capability_id=capability_id,
        status=status,
        rationale=rationale,
        decision_owner=decision_owner,
        evidence_refs=tuple(evidence_refs),
        reviewed_at=reviewed_at,
        release_target=release_target,
    )


def make_mapping_rule(
    mapping_id: str,
    *,
    outcome_scope: str,
    outcome_status: str,
    capability_ids: tuple[str, ...],
    priority: int = 0,
    mapping_rationale: str = "matrix-mapping",
) -> OutcomeMappingRule:
    return OutcomeMappingRule(
        mapping_id=mapping_id,
        outcome_scope=outcome_scope,
        outcome_status=outcome_status,
        capability_ids=tuple(capability_ids),
        priority=priority,
        mapping_rationale=mapping_rationale,
    )
