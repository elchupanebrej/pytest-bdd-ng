"""

Provide test message status governance helpers.
"""

from __future__ import annotations

from pytest_bdd.model.message_status_governance import (
    CapabilityDecision,
    ensure_single_status_per_capability,
    evaluate_release_blockers,
    validate_capability_decision,
)
from pytest_bdd_testing.tool.message.capability_fixtures import make_decision, utc_now


def test_validate_capability_decision_requires_mandatory_evidence_fields() -> None:
    """
    Verify validate capability decision requires mandatory evidence fields.

    Test target:
        Verify Cucumber Messages protocol compliance to support external reporting tools and IDE bindings.
    Test type:
        E2E/Acceptance test
    Test scenario:
        Given the relevant preconditions are met, when Verify Cucumber Messages protocol compliance to support external
        reporting tools and IDE bindings., then the expected outcome is produced.
    BDD reference:
        None
    Fixtures:
        - None
    Mocks:
        - None
    Side effects:
        None
    Reduction:
        Requires real component interaction that cannot be reproduced by mocking alone.
    Escalation:
        Testing at a higher level would not add coverage and would slow down the suite.
    Atomicity:
        All assertions share the same setup and verify a single coherent behavior.
    Autonomy:
        Covers a distinct code path not exercised by any sibling test.
    Test quality score:
        #test-eval:isolation=5
        #test-eval:determinism=5
        #test-eval:setup_complexity=1
        #test-eval:assertions_clarity=5
    """
    decision = make_decision(
        "cap-1",
        status="Non-Implementable",
        rationale=None,
        hard_limitation=None,
        decision_owner=None,
        evidence_refs=(),
        reviewed_at=None,
    )

    result = validate_capability_decision(decision)

    assert result.accepted is False
    assert set(result.missing_required_evidence_fields) == {
        "rationale",
        "hard_limitation",
        "decision_owner",
        "evidence_refs",
        "reviewed_at",
        "recheck_trigger",
    }


def test_validate_capability_decision_accepts_complete_evidence_fields() -> None:
    """
    Verify validate capability decision accepts complete evidence fields.

    Test target:
        Verify Cucumber Messages protocol compliance to support external reporting tools and IDE bindings.
    Test type:
        E2E/Acceptance test
    Test scenario:
        Given the relevant preconditions are met, when Verify Cucumber Messages protocol compliance to support external
        reporting tools and IDE bindings., then the expected outcome is produced.
    BDD reference:
        None
    Fixtures:
        - None
    Mocks:
        - None
    Side effects:
        None
    Reduction:
        Requires real component interaction that cannot be reproduced by mocking alone.
    Escalation:
        Testing at a higher level would not add coverage and would slow down the suite.
    Atomicity:
        All assertions share the same setup and verify a single coherent behavior.
    Autonomy:
        Covers a distinct code path not exercised by any sibling test.
    Test quality score:
        #test-eval:isolation=5
        #test-eval:determinism=5
        #test-eval:setup_complexity=1
        #test-eval:assertions_clarity=5
    """
    decision = make_decision(
        "cap-1",
        status="Non-Implementable",
        rationale="Runtime does not expose required signal",
        hard_limitation="Hard technical limitation: runtime hook surface has no event carrying this field.",
        decision_owner="reporting-owner",
        evidence_refs=("design-note-1",),
        reviewed_at=utc_now(),
        recheck_trigger="new-runtime-event-available",
    )

    result = validate_capability_decision(decision)

    assert result.accepted is True
    assert result.missing_required_evidence_fields == ()
    assert result.violations == ()


def test_validate_capability_decision_rejects_soft_non_implementable_rationale() -> None:
    """
    Verify validate capability decision rejects soft non implementable rationale.

    Test target:
        Verify Cucumber Messages protocol compliance to support external reporting tools and IDE bindings.
    Test type:
        E2E/Acceptance test
    Test scenario:
        Given the relevant preconditions are met, when Verify Cucumber Messages protocol compliance to support external
        reporting tools and IDE bindings., then the expected outcome is produced.
    BDD reference:
        None
    Fixtures:
        - None
    Mocks:
        - None
    Side effects:
        None
    Reduction:
        Requires real component interaction that cannot be reproduced by mocking alone.
    Escalation:
        Testing at a higher level would not add coverage and would slow down the suite.
    Atomicity:
        All assertions share the same setup and verify a single coherent behavior.
    Autonomy:
        Covers a distinct code path not exercised by any sibling test.
    Test quality score:
        #test-eval:isolation=5
        #test-eval:determinism=5
        #test-eval:setup_complexity=1
        #test-eval:assertions_clarity=5
    """
    decision = make_decision(
        "cap-1",
        status="Non-Implementable",
        rationale="Future work after milestone",
        hard_limitation="not implemented yet",
        decision_owner="reporting-owner",
        evidence_refs=("design-note-1",),
        reviewed_at=utc_now(),
        recheck_trigger="new-runtime-event-available",
    )

    result = validate_capability_decision(decision)

    assert result.accepted is False
    assert any("forbidden phrase" in violation for violation in result.violations)


def test_validate_capability_decision_requires_language_runtime_mismatch_for_partly_applicable() -> None:
    """
    Verify validate capability decision requires language runtime mismatch for partly applicable.

    Test target:
        Verify Cucumber Messages protocol compliance to support external reporting tools and IDE bindings.
    Test type:
        E2E/Acceptance test
    Test scenario:
        Given the relevant preconditions are met, when Verify Cucumber Messages protocol compliance to support external
        reporting tools and IDE bindings., then the expected outcome is produced.
    BDD reference:
        None
    Fixtures:
        - None
    Mocks:
        - None
    Side effects:
        None
    Reduction:
        Requires real component interaction that cannot be reproduced by mocking alone.
    Escalation:
        Testing at a higher level would not add coverage and would slow down the suite.
    Atomicity:
        All assertions share the same setup and verify a single coherent behavior.
    Autonomy:
        Covers a distinct code path not exercised by any sibling test.
    Test quality score:
        #test-eval:isolation=5
        #test-eval:determinism=5
        #test-eval:setup_complexity=1
        #test-eval:assertions_clarity=5
    """
    decision = make_decision(
        "cap-1",
        status="Partly-Applicable",
        rationale="Partly supported for now",
        decision_owner="reporting-owner",
        evidence_refs=("design-note-1",),
        reviewed_at=utc_now(),
    )

    result = validate_capability_decision(decision)

    assert result.accepted is False
    assert any("language/runtime model mismatch" in violation for violation in result.violations)


def test_validate_capability_decision_accepts_partly_applicable_with_language_runtime_rationale() -> None:
    """
    Verify validate capability decision accepts partly applicable with language runtime rationale.

    Test target:
        Verify Cucumber Messages protocol compliance to support external reporting tools and IDE bindings.
    Test type:
        E2E/Acceptance test
    Test scenario:
        Given the relevant preconditions are met, when Verify Cucumber Messages protocol compliance to support external
        reporting tools and IDE bindings., then the expected outcome is produced.
    BDD reference:
        None
    Fixtures:
        - None
    Mocks:
        - None
    Side effects:
        None
    Reduction:
        Requires real component interaction that cannot be reproduced by mocking alone.
    Escalation:
        Testing at a higher level would not add coverage and would slow down the suite.
    Atomicity:
        All assertions share the same setup and verify a single coherent behavior.
    Autonomy:
        Covers a distinct code path not exercised by any sibling test.
    Test quality score:
        #test-eval:isolation=5
        #test-eval:determinism=5
        #test-eval:setup_complexity=1
        #test-eval:assertions_clarity=5
    """
    decision = make_decision(
        "cap-1",
        status="Partly-Applicable",
        rationale="Java language model is mapped in Python runtime with no native equivalent model.",
        decision_owner="reporting-owner",
        evidence_refs=("design-note-1",),
        reviewed_at=utc_now(),
    )

    result = validate_capability_decision(decision)

    assert result.accepted is True
    assert result.missing_required_evidence_fields == ()
    assert result.violations == ()


def test_status_uniqueness_detects_duplicate_capability_decisions() -> None:
    """
    Verify status uniqueness detects duplicate capability decisions.

    Test target:
        Verify Cucumber Messages protocol compliance to support external reporting tools and IDE bindings.
    Test type:
        E2E/Acceptance test
    Test scenario:
        Given the relevant preconditions are met, when Verify Cucumber Messages protocol compliance to support external
        reporting tools and IDE bindings., then the expected outcome is produced.
    BDD reference:
        None
    Fixtures:
        - None
    Mocks:
        - None
    Side effects:
        None
    Reduction:
        Requires real component interaction that cannot be reproduced by mocking alone.
    Escalation:
        Testing at a higher level would not add coverage and would slow down the suite.
    Atomicity:
        All assertions share the same setup and verify a single coherent behavior.
    Autonomy:
        Covers a distinct code path not exercised by any sibling test.
    Test quality score:
        #test-eval:isolation=5
        #test-eval:determinism=5
        #test-eval:setup_complexity=1
        #test-eval:assertions_clarity=5
    """
    decisions = [
        CapabilityDecision(capability_id="cap-1", status="Implemented", release_target="r1"),
        CapabilityDecision(capability_id="cap-1", status="Pending", release_target="r1"),
    ]

    result = ensure_single_status_per_capability(decisions)

    assert result.is_unique is False
    assert result.duplicates == ("cap-1@r1",)


def test_status_uniqueness_allows_same_capability_across_distinct_release_targets() -> None:
    """
    Verify status uniqueness allows same capability across distinct release targets.

    Test target:
        Verify Cucumber Messages protocol compliance to support external reporting tools and IDE bindings.
    Test type:
        E2E/Acceptance test
    Test scenario:
        Given the relevant preconditions are met, when Verify Cucumber Messages protocol compliance to support external
        reporting tools and IDE bindings., then the expected outcome is produced.
    BDD reference:
        None
    Fixtures:
        - None
    Mocks:
        - None
    Side effects:
        None
    Reduction:
        Requires real component interaction that cannot be reproduced by mocking alone.
    Escalation:
        Testing at a higher level would not add coverage and would slow down the suite.
    Atomicity:
        All assertions share the same setup and verify a single coherent behavior.
    Autonomy:
        Covers a distinct code path not exercised by any sibling test.
    Test quality score:
        #test-eval:isolation=5
        #test-eval:determinism=5
        #test-eval:setup_complexity=1
        #test-eval:assertions_clarity=5
    """
    decisions = [
        CapabilityDecision(capability_id="cap-1", status="Implemented", release_target="r1"),
        CapabilityDecision(capability_id="cap-1", status="Pending", release_target="r2"),
    ]

    result = ensure_single_status_per_capability(decisions)

    assert result.is_unique is True
    assert result.duplicates == ()


def test_evaluate_release_blockers_flags_pending_and_missing_decisions() -> None:
    """
    Verify evaluate release blockers flags pending and missing decisions.

    Test target:
        Verify Cucumber Messages protocol compliance to support external reporting tools and IDE bindings.
    Test type:
        E2E/Acceptance test
    Test scenario:
        Given the relevant preconditions are met, when Verify Cucumber Messages protocol compliance to support external
        reporting tools and IDE bindings., then the expected outcome is produced.
    BDD reference:
        None
    Fixtures:
        - None
    Mocks:
        - None
    Side effects:
        None
    Reduction:
        Requires real component interaction that cannot be reproduced by mocking alone.
    Escalation:
        Testing at a higher level would not add coverage and would slow down the suite.
    Atomicity:
        All assertions share the same setup and verify a single coherent behavior.
    Autonomy:
        Covers a distinct code path not exercised by any sibling test.
    Test quality score:
        #test-eval:isolation=5
        #test-eval:determinism=5
        #test-eval:setup_complexity=1
        #test-eval:assertions_clarity=5
    """
    decisions = [
        CapabilityDecision(capability_id="cap-implemented", status="Implemented", release_target="r1"),
        CapabilityDecision(capability_id="cap-pending", status="Pending", release_target="r1"),
        CapabilityDecision(capability_id="cap-na", status="Not-Applicable", release_target="r1"),
        CapabilityDecision(capability_id="cap-partly", status="Partly-Applicable", release_target="r1"),
    ]

    result = evaluate_release_blockers(
        decisions,
        relevant_capability_ids=("cap-implemented", "cap-pending", "cap-na", "cap-partly", "cap-missing"),
    )

    assert result.unresolved_blocker_capability_ids == ("cap-missing", "cap-pending")
    assert result.deferred_capability_ids == ("cap-na", "cap-partly")
    assert result.missing_decision_capability_ids == ("cap-missing",)
