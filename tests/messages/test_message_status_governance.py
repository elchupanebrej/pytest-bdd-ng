from __future__ import annotations

from pytest_bdd.model.message_status_governance import (
    CapabilityDecision,
    ensure_single_status_per_capability,
    evaluate_release_blockers,
    validate_capability_decision,
)

from .message_capability_fixtures import make_decision, utc_now


def test_validate_capability_decision_requires_mandatory_evidence_fields() -> None:
    decision = make_decision(
        "cap-1",
        status="Non-Implementable",
        rationale=None,
        decision_owner=None,
        evidence_refs=(),
        reviewed_at=None,
    )

    result = validate_capability_decision(decision)

    assert result.accepted is False
    assert set(result.missing_required_evidence_fields) == {
        "rationale",
        "decision_owner",
        "evidence_refs",
        "reviewed_at",
    }


def test_validate_capability_decision_accepts_complete_evidence_fields() -> None:
    decision = make_decision(
        "cap-1",
        status="Non-Implementable",
        rationale="Runtime does not expose required signal",
        decision_owner="reporting-owner",
        evidence_refs=("design-note-1",),
        reviewed_at=utc_now(),
    )

    result = validate_capability_decision(decision)

    assert result.accepted is True
    assert result.missing_required_evidence_fields == ()
    assert result.violations == ()


def test_status_uniqueness_detects_duplicate_capability_decisions() -> None:
    decisions = [
        CapabilityDecision(capability_id="cap-1", status="Implemented", release_target="r1"),
        CapabilityDecision(capability_id="cap-1", status="Pending", release_target="r1"),
    ]

    result = ensure_single_status_per_capability(decisions)

    assert result.is_unique is False
    assert result.duplicates == ("cap-1@r1",)


def test_status_uniqueness_allows_same_capability_across_distinct_release_targets() -> None:
    decisions = [
        CapabilityDecision(capability_id="cap-1", status="Implemented", release_target="r1"),
        CapabilityDecision(capability_id="cap-1", status="Pending", release_target="r2"),
    ]

    result = ensure_single_status_per_capability(decisions)

    assert result.is_unique is True
    assert result.duplicates == ()


def test_evaluate_release_blockers_flags_pending_and_missing_decisions() -> None:
    decisions = [
        CapabilityDecision(capability_id="cap-implemented", status="Implemented", release_target="r1"),
        CapabilityDecision(capability_id="cap-pending", status="Pending", release_target="r1"),
        CapabilityDecision(capability_id="cap-na", status="Not-Applicable", release_target="r1"),
    ]

    result = evaluate_release_blockers(
        decisions,
        relevant_capability_ids=("cap-implemented", "cap-pending", "cap-na", "cap-missing"),
    )

    assert result.unresolved_blocker_capability_ids == ("cap-missing", "cap-pending")
    assert result.deferred_capability_ids == ("cap-na",)
    assert result.missing_decision_capability_ids == ("cap-missing",)
