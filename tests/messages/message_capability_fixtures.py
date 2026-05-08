"""Provide message capability fixtures helpers."""

from __future__ import annotations

from datetime import UTC, datetime

from pytest_bdd.model.message_capability import MessageCapability
from pytest_bdd.model.message_outcome_mapping import OutcomeMappingRule
from pytest_bdd.model.message_status_governance import CapabilityDecision


def utc_now() -> datetime:
    """Handle utc now."""
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
    """Create capability."""
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
    hard_limitation: str | None = None,
    decision_owner: str | None = None,
    evidence_refs: tuple[str, ...] = (),
    reviewed_at: datetime | None = None,
    release_target: str = "next-release",
    recheck_trigger: str | None = None,
) -> CapabilityDecision:
    """Create decision."""
    return CapabilityDecision(
        capability_id=capability_id,
        status=status,
        rationale=rationale,
        hard_limitation=hard_limitation,
        decision_owner=decision_owner,
        evidence_refs=tuple(evidence_refs),
        reviewed_at=reviewed_at,
        release_target=release_target,
        recheck_trigger=recheck_trigger,
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
    """Create mapping rule."""
    return OutcomeMappingRule(
        mapping_id=mapping_id,
        outcome_scope=outcome_scope,
        outcome_status=outcome_status,
        capability_ids=tuple(capability_ids),
        priority=priority,
        mapping_rationale=mapping_rationale,
    )


def make_capability_sync_payload() -> dict[str, object]:
    """Create capability sync payload."""
    return {
        "baseline_release": "v32.0.1",
        "source_entries": [
            {
                "capability_id": "cap-1",
                "baseline_release": "legacy",
                "name": "Capability 1",
                "description": "desc",
                "relevance": "relevant",
                "source_reference": "messages/jsonschema/src/Envelope.json",
            },
            {
                "capability_id": "cap-1",
                "baseline_release": "legacy",
                "name": "Capability 1 duplicate",
                "description": "desc",
                "relevance": "relevant",
                "source_reference": "messages/jsonschema/src/Envelope.json",
            },
        ],
    }


def make_governance_report_payload() -> dict[str, object]:
    """Create governance report payload."""
    now = utc_now().isoformat()
    return {
        "version": "1.1",
        "generated_at": now,
        "baseline_release": "v32.0.1",
        "summary": {
            "total_capabilities": 1,
            "implemented_capabilities": 1,
            "blocked_capabilities": 0,
            "deferred_capabilities": 0,
            "coverage_percentage": 100.0,
            "runtime_required_total": 0,
            "runtime_required_covered": 0,
            "runtime_required_missing": 0,
            "non_runtime_required_total": 1,
            "non_runtime_covered": 1,
            "non_runtime_classified": 0,
            "mandatory_scope_violations": 0,
        },
        "capabilities": [
            {
                "capability_id": "testCaseStarted.id",
                "status": "Implemented",
                "disposition": "approved",
                "mandatory_scope": False,
                "runtime_required": False,
                "observed_runtime": True,
                "decision_owner": "Automation",
                "reviewed_at": now,
                "evidence_refs": ["tests/messages/test_governance.py"],
            }
        ],
    }
