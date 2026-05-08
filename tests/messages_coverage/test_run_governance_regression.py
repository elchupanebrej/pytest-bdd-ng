"""Provide test run governance regression helpers."""

from __future__ import annotations

import json
from datetime import datetime, timezone

from pytest_bdd.model.coverage.inventory import CapabilityInventory, FieldMetadata
from pytest_bdd.model.message_status_governance import CapabilityDecision, validate_capability_decision
from pytest_bdd.script import message_capability_governance
from pytest_bdd.script.message_capability_governance import main


def _single_field_inventory() -> CapabilityInventory:
    return CapabilityInventory(
        payload_kinds=["testRunStarted"],
        fields={("testRunStarted", "id"): FieldMetadata(path="id", type="string", is_required=True)},
    )


def test_non_implementable_requires_hard_limitation_evidence() -> None:
    """Verify non implementable requires hard limitation evidence."""
    decision = CapabilityDecision(
        capability_id="testRunFinished.exception.stackTrace",
        status="Non-Implementable",
        release_target="v32.current",
        rationale="Field requires Java exception model unavailable in Python runtime signals.",
        hard_limitation="Python runtime does not expose Java stack-trace model objects for this envelope path.",
        decision_owner="pytest-bdd-ng-maintainers",
        evidence_refs=("tests/messages_coverage/probes/test_failing_step_runtime.py",),
        reviewed_at=datetime.now(timezone.utc),
        recheck_trigger="when Python runtime exposes Java exception model",
    )

    validation = validate_capability_decision(decision)
    assert validation.accepted


def test_non_implementable_rejects_future_work_wording() -> None:
    """Verify non implementable rejects future work wording."""
    decision = CapabilityDecision(
        capability_id="testRunFinished.exception.stackTrace",
        status="Non-Implementable",
        release_target="v32.current",
        rationale="Not implemented yet in reporter pipeline.",
        hard_limitation="Future work item only.",
        decision_owner="pytest-bdd-ng-maintainers",
        evidence_refs=("tests/messages_coverage/probes/test_failing_step_runtime.py",),
        reviewed_at=datetime.now(timezone.utc),
        recheck_trigger="later",
    )

    validation = validate_capability_decision(decision)
    assert not validation.accepted
    assert validation.violations


def test_partly_applicable_requires_language_runtime_mismatch_rationale() -> None:
    """Verify partly applicable requires language runtime mismatch rationale."""
    decision = CapabilityDecision(
        capability_id="hook.sourceReference.javaMethod.className",
        status="Partly-Applicable",
        release_target="v32.current",
        rationale="Python language runtime uses synthetic Java model projection for cross-language compatibility.",
        decision_owner="pytest-bdd-ng-maintainers",
        evidence_refs=("tests/messages/test_messages.py",),
        reviewed_at=datetime.now(timezone.utc),
    )

    validation = validate_capability_decision(decision)
    assert validation.accepted


def test_runtime_required_capability_without_runtime_evidence_fails_gate(tmp_path, monkeypatch) -> None:
    """Verify runtime required capability without runtime evidence fails gate."""
    monkeypatch.setattr(
        message_capability_governance,
        "generate_inventory",
        lambda _schema_dir: _single_field_inventory(),
    )
    messages_file = tmp_path / "messages.ndjson"
    messages_file.write_text("", encoding="utf-8")

    decisions_file = tmp_path / "decisions.json"
    decisions_file.write_text(
        json.dumps(
            [
                {
                    "capability_id": "testRunStarted.id",
                    "status": "Implemented",
                    "release_target": "v32.current",
                }
            ]
        ),
        encoding="utf-8",
    )

    runtime_required_file = tmp_path / "runtime-required.txt"
    runtime_required_file.write_text("testRunStarted.id\n", encoding="utf-8")

    output_file = tmp_path / "report.json"
    exit_code = main(
        [
            "report",
            "--messages-file",
            str(messages_file),
            "--baseline-release",
            "v32.current",
            "--decisions",
            str(decisions_file),
            "--runtime-required-capabilities-file",
            str(runtime_required_file),
            "--require-runtime-required-covered",
            "--output",
            str(output_file),
        ]
    )

    payload = json.loads(output_file.read_text(encoding="utf-8"))
    assert exit_code == 1
    assert payload["summary"]["runtime_required_missing"] == 1
    assert payload["capabilities"][0]["status"] == "Implemented"
    assert payload["capabilities"][0]["disposition"] == "blocked"


def test_non_runtime_capability_can_be_classified_partly_applicable(tmp_path, monkeypatch) -> None:
    """Verify non runtime capability can be classified partly applicable."""
    monkeypatch.setattr(
        message_capability_governance,
        "generate_inventory",
        lambda _schema_dir: _single_field_inventory(),
    )
    messages_file = tmp_path / "messages.ndjson"
    messages_file.write_text("", encoding="utf-8")

    decisions_file = tmp_path / "decisions.json"
    decisions_file.write_text(
        json.dumps(
            [
                {
                    "capability_id": "testRunStarted.id",
                    "status": "Partly-Applicable",
                    "release_target": "v32.current",
                    "rationale": "Python runtime uses Java model projection due to language/runtime mismatch.",
                    "decision_owner": "pytest-bdd-ng-maintainers",
                    "evidence_refs": ["tests/messages_coverage/test_run_governance_regression.py"],
                    "reviewed_at": "2026-03-03T00:00:00+00:00",
                }
            ]
        ),
        encoding="utf-8",
    )

    output_file = tmp_path / "report.json"
    exit_code = main(
        [
            "report",
            "--messages-file",
            str(messages_file),
            "--baseline-release",
            "v32.current",
            "--decisions",
            str(decisions_file),
            "--require-non-runtime-classified",
            "--require-fully-governed",
            "--output",
            str(output_file),
        ]
    )

    payload = json.loads(output_file.read_text(encoding="utf-8"))
    assert exit_code == 0
    assert payload["summary"]["blocked_capabilities"] == 0
    assert payload["summary"]["deferred_capabilities"] == 1
    assert payload["capabilities"][0]["status"] == "Partly-Applicable"
    assert payload["capabilities"][0]["disposition"] == "deferred"
