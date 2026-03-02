from __future__ import annotations

import json

import pytest

from pytest_bdd.model.coverage.inventory import CapabilityInventory, FieldMetadata
from pytest_bdd.script import message_capability_governance
from pytest_bdd.script.message_capability_governance import main


def test_governance_report_generation_conforms_to_contract_shape(tmp_path) -> None:
    messages_file = tmp_path / "messages.ndjson"
    messages_file.write_text(
        '{"testCaseStarted":{"id":"123","testCaseId":"456","timestamp":{"seconds":0,"nanos":0},"attempt":0}}\n',
        encoding="utf-8",
    )

    output_file = tmp_path / "governance.json"
    exit_code = main(
        [
            "report",
            "--messages-file",
            str(messages_file),
            "--baseline-release",
            "v32.0.1",
            "--output",
            str(output_file),
        ]
    )

    assert exit_code == 0
    payload = json.loads(output_file.read_text(encoding="utf-8"))
    assert payload["version"] == "1.0"
    assert payload["baseline_release"] == "v32.0.1"
    assert "summary" in payload
    assert payload["summary"]["total_capabilities"] >= payload["summary"]["implemented_capabilities"]
    assert isinstance(payload["capabilities"], list)


def test_governance_diff_supports_governance_report_input_flags(tmp_path) -> None:
    previous = tmp_path / "previous-governance.json"
    current = tmp_path / "current-governance.json"
    output = tmp_path / "baseline-diff.json"

    previous.write_text(
        json.dumps(
            {
                "version": "1.0",
                "generated_at": "2026-03-01T00:00:00+00:00",
                "baseline_release": "v32.0.0",
                "summary": {
                    "total_capabilities": 1,
                    "implemented_capabilities": 1,
                    "blocked_capabilities": 0,
                    "deferred_capabilities": 0,
                    "coverage_percentage": 100.0,
                },
                "capabilities": [{"capability_id": "cap-1", "status": "Implemented", "disposition": "approved"}],
            }
        ),
        encoding="utf-8",
    )
    current.write_text(
        json.dumps(
            {
                "version": "1.0",
                "generated_at": "2026-03-08T00:00:00+00:00",
                "baseline_release": "v32.0.1",
                "summary": {
                    "total_capabilities": 2,
                    "implemented_capabilities": 1,
                    "blocked_capabilities": 1,
                    "deferred_capabilities": 0,
                    "coverage_percentage": 50.0,
                },
                "capabilities": [
                    {"capability_id": "cap-1", "status": "Implemented", "disposition": "approved"},
                    {"capability_id": "cap-2", "status": "Pending", "disposition": "blocked"},
                ],
            }
        ),
        encoding="utf-8",
    )

    exit_code = main(
        [
            "diff",
            "--previous-baseline",
            "v32.0.0",
            "--current-baseline",
            "v32.0.1",
            "--previous-governance",
            str(previous),
            "--current-governance",
            str(current),
            "--output",
            str(output),
        ]
    )

    payload = json.loads(output.read_text(encoding="utf-8"))
    assert exit_code == 0
    assert payload["added_capability_ids"] == ["cap-2"]


def test_governance_report_strict_mode_fails_on_pending_without_decision(tmp_path, monkeypatch) -> None:
    inventory = CapabilityInventory(
        payload_kinds=["testRunStarted"],
        fields={("testRunStarted", "id"): FieldMetadata(path="id", type="string", is_required=True)},
    )
    monkeypatch.setattr(message_capability_governance, "generate_inventory", lambda _schema_dir: inventory)

    messages_file = tmp_path / "messages.ndjson"
    messages_file.write_text("", encoding="utf-8")
    output_file = tmp_path / "governance.json"

    exit_code = main(
        [
            "report",
            "--messages-file",
            str(messages_file),
            "--baseline-release",
            "v32.0.1",
            "--require-fully-governed",
            "--output",
            str(output_file),
        ]
    )

    assert exit_code == 1
    payload = json.loads(output_file.read_text(encoding="utf-8"))
    assert payload["summary"]["blocked_capabilities"] == 1
    assert payload["capabilities"][0]["status"] == "Pending"


def test_governance_report_applies_decision_file_in_strict_mode(tmp_path, monkeypatch) -> None:
    inventory = CapabilityInventory(
        payload_kinds=["testRunStarted"],
        fields={("testRunStarted", "id"): FieldMetadata(path="id", type="string", is_required=True)},
    )
    monkeypatch.setattr(message_capability_governance, "generate_inventory", lambda _schema_dir: inventory)

    messages_file = tmp_path / "messages.ndjson"
    messages_file.write_text("", encoding="utf-8")
    decisions_file = tmp_path / "decisions.json"
    decisions_file.write_text(
        json.dumps(
            [
                {
                    "capability_id": "testRunStarted.id",
                    "status": "Not-Applicable",
                    "rationale": "No deterministic runtime path in this suite",
                    "decision_owner": "Coverage Governance",
                    "evidence_refs": ["tests/messages/test_governance.py"],
                    "reviewed_at": "2026-03-02T00:00:00+00:00",
                    "release_target": "messages-audit",
                }
            ]
        ),
        encoding="utf-8",
    )
    output_file = tmp_path / "governance.json"

    exit_code = main(
        [
            "report",
            "--messages-file",
            str(messages_file),
            "--baseline-release",
            "v32.0.1",
            "--decisions",
            str(decisions_file),
            "--require-fully-governed",
            "--output",
            str(output_file),
        ]
    )

    assert exit_code == 0
    payload = json.loads(output_file.read_text(encoding="utf-8"))
    assert payload["summary"]["blocked_capabilities"] == 0
    assert payload["summary"]["deferred_capabilities"] == 1
    assert payload["capabilities"][0]["status"] == "Not-Applicable"
    assert payload["capabilities"][0]["disposition"] == "deferred"


def test_governance_report_rejects_unknown_decision_capability_ids(tmp_path, monkeypatch) -> None:
    inventory = CapabilityInventory(
        payload_kinds=["testRunStarted"],
        fields={("testRunStarted", "id"): FieldMetadata(path="id", type="string", is_required=True)},
    )
    monkeypatch.setattr(message_capability_governance, "generate_inventory", lambda _schema_dir: inventory)

    messages_file = tmp_path / "messages.ndjson"
    messages_file.write_text("", encoding="utf-8")
    decisions_file = tmp_path / "decisions.json"
    decisions_file.write_text(
        json.dumps(
            [
                {
                    "capability_id": "unknown.capability",
                    "status": "Not-Applicable",
                    "rationale": "Not emitted",
                    "decision_owner": "Coverage Governance",
                    "evidence_refs": ["tests/messages/test_governance.py"],
                    "reviewed_at": "2026-03-02T00:00:00+00:00",
                    "release_target": "messages-audit",
                }
            ]
        ),
        encoding="utf-8",
    )
    output_file = tmp_path / "governance.json"

    with pytest.raises(ValueError, match="unknown capability IDs"):
        main(
            [
                "report",
                "--messages-file",
                str(messages_file),
                "--baseline-release",
                "v32.0.1",
                "--decisions",
                str(decisions_file),
                "--output",
                str(output_file),
            ]
        )
