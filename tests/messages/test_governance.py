from __future__ import annotations

import json

import pytest

from pytest_bdd.model.coverage.inventory import CapabilityInventory, FieldMetadata
from pytest_bdd.script import message_capability_governance
from pytest_bdd.script.message_capability_governance import main


def _single_field_inventory() -> CapabilityInventory:
    return CapabilityInventory(
        payload_kinds=["testRunStarted"],
        fields={("testRunStarted", "id"): FieldMetadata(path="id", type="string", is_required=True)},
    )


def test_governance_report_generation_conforms_to_contract_shape(tmp_path) -> None:
    messages_file = tmp_path / "messages.ndjson"
    messages_file.write_text(
        '{"testRunStarted":{"id":"123","timestamp":{"seconds":0,"nanos":0}}}\n',
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
    assert payload["version"] == "1.1"
    assert payload["baseline_release"] == "v32.0.1"
    assert payload["summary"]["total_capabilities"] >= payload["summary"]["implemented_capabilities"]
    assert payload["summary"]["runtime_required_total"] >= 0
    assert payload["summary"]["non_runtime_required_total"] >= 0
    assert isinstance(payload["capabilities"], list)


def test_governance_diff_supports_governance_report_input_flags(tmp_path) -> None:
    previous = tmp_path / "previous-governance.json"
    current = tmp_path / "current-governance.json"
    output = tmp_path / "baseline-diff.json"

    previous.write_text(
        json.dumps(
            {
                "version": "1.1",
                "generated_at": "2026-03-01T00:00:00+00:00",
                "baseline_release": "v32.0.0",
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
                "capabilities": [{"capability_id": "cap-1", "status": "Implemented", "disposition": "approved"}],
            }
        ),
        encoding="utf-8",
    )
    current.write_text(
        json.dumps(
            {
                "version": "1.1",
                "generated_at": "2026-03-08T00:00:00+00:00",
                "baseline_release": "v32.0.1",
                "summary": {
                    "total_capabilities": 2,
                    "implemented_capabilities": 1,
                    "blocked_capabilities": 1,
                    "deferred_capabilities": 0,
                    "coverage_percentage": 50.0,
                    "runtime_required_total": 0,
                    "runtime_required_covered": 0,
                    "runtime_required_missing": 0,
                    "non_runtime_required_total": 2,
                    "non_runtime_covered": 1,
                    "non_runtime_classified": 0,
                    "mandatory_scope_violations": 0,
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
    monkeypatch.setattr(
        message_capability_governance, "generate_inventory", lambda _schema_dir: _single_field_inventory()
    )

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
    monkeypatch.setattr(
        message_capability_governance, "generate_inventory", lambda _schema_dir: _single_field_inventory()
    )

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
                    "release_target": "v32.0.1",
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
    assert payload["summary"]["non_runtime_classified"] == 1
    assert payload["capabilities"][0]["status"] == "Not-Applicable"
    assert payload["capabilities"][0]["disposition"] == "deferred"


def test_governance_report_accepts_partly_applicable_decision_with_required_comment(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(
        message_capability_governance, "generate_inventory", lambda _schema_dir: _single_field_inventory()
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
                    "rationale": "Java language model is mapped in Python runtime with no native equivalent model.",
                    "decision_owner": "Coverage Governance",
                    "evidence_refs": ["tests/messages/test_governance.py"],
                    "reviewed_at": "2026-03-02T00:00:00+00:00",
                    "release_target": "v32.0.1",
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
    assert payload["capabilities"][0]["status"] == "Partly-Applicable"
    assert payload["capabilities"][0]["disposition"] == "deferred"


def test_governance_report_rejects_unknown_decision_capability_ids(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(
        message_capability_governance, "generate_inventory", lambda _schema_dir: _single_field_inventory()
    )

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
                    "release_target": "v32.0.1",
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


def test_governance_report_loads_runtime_required_scope_with_unique_ids(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(
        message_capability_governance, "generate_inventory", lambda _schema_dir: _single_field_inventory()
    )

    messages_file = tmp_path / "messages.ndjson"
    messages_file.write_text("", encoding="utf-8")
    mandatory_file = tmp_path / "mandatory.txt"
    mandatory_file.write_text("# comment\ntestRunStarted.id\ntest_run_started.id\n", encoding="utf-8")
    runtime_required_file = tmp_path / "runtime-required.txt"
    runtime_required_file.write_text("test_run_started.id\n", encoding="utf-8")
    output_file = tmp_path / "governance.json"

    exit_code = main(
        [
            "report",
            "--messages-file",
            str(messages_file),
            "--baseline-release",
            "v32.0.1",
            "--mandatory-capabilities-file",
            str(mandatory_file),
            "--runtime-required-capabilities-file",
            str(runtime_required_file),
            "--output",
            str(output_file),
        ]
    )

    payload = json.loads(output_file.read_text(encoding="utf-8"))
    assert exit_code == 0
    assert payload["summary"]["runtime_required_total"] == 1
    assert payload["summary"]["runtime_required_covered"] == 0
    assert payload["summary"]["runtime_required_missing"] == 1
    assert payload["summary"]["mandatory_scope_violations"] == 1
    assert payload["capabilities"][0]["runtime_required"] is True


def test_governance_report_rejects_unknown_runtime_required_capability_ids(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(
        message_capability_governance, "generate_inventory", lambda _schema_dir: _single_field_inventory()
    )

    messages_file = tmp_path / "messages.ndjson"
    messages_file.write_text("", encoding="utf-8")
    runtime_required_file = tmp_path / "runtime-required.txt"
    runtime_required_file.write_text("unknown.capability\n", encoding="utf-8")
    output_file = tmp_path / "governance.json"

    with pytest.raises(ValueError, match="Runtime-required capability file contains unknown capability IDs"):
        main(
            [
                "report",
                "--messages-file",
                str(messages_file),
                "--baseline-release",
                "v32.0.1",
                "--runtime-required-capabilities-file",
                str(runtime_required_file),
                "--output",
                str(output_file),
            ]
        )


def test_governance_report_rejects_runtime_required_ids_outside_mandatory_scope(tmp_path, monkeypatch) -> None:
    inventory = CapabilityInventory(
        payload_kinds=["testRunStarted"],
        fields={
            ("testRunStarted", "id"): FieldMetadata(path="id", type="string", is_required=True),
            ("testRunStarted", "timestamp.seconds"): FieldMetadata(
                path="timestamp.seconds", type="integer", is_required=True
            ),
        },
    )
    monkeypatch.setattr(message_capability_governance, "generate_inventory", lambda _schema_dir: inventory)

    messages_file = tmp_path / "messages.ndjson"
    messages_file.write_text("", encoding="utf-8")
    mandatory_file = tmp_path / "mandatory.txt"
    mandatory_file.write_text("testRunStarted.timestamp.seconds\n", encoding="utf-8")
    runtime_required_file = tmp_path / "runtime-required.txt"
    runtime_required_file.write_text("testRunStarted.id\n", encoding="utf-8")
    output_file = tmp_path / "governance.json"

    with pytest.raises(ValueError, match="runtime-required capability file contains IDs outside mandatory scope"):
        main(
            [
                "report",
                "--messages-file",
                str(messages_file),
                "--baseline-release",
                "v32.0.1",
                "--mandatory-capabilities-file",
                str(mandatory_file),
                "--runtime-required-capabilities-file",
                str(runtime_required_file),
                "--output",
                str(output_file),
            ]
        )


def test_governance_report_runtime_required_gate_requires_scope_file(tmp_path) -> None:
    messages_file = tmp_path / "messages.ndjson"
    messages_file.write_text("", encoding="utf-8")

    with pytest.raises(
        ValueError, match="--require-runtime-required-covered requires --runtime-required-capabilities-file"
    ):
        main(
            [
                "report",
                "--messages-file",
                str(messages_file),
                "--baseline-release",
                "v32.0.1",
                "--require-runtime-required-covered",
            ]
        )


def test_governance_report_runtime_required_gate_fails_without_runtime_evidence(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(
        message_capability_governance, "generate_inventory", lambda _schema_dir: _single_field_inventory()
    )

    messages_file = tmp_path / "messages.ndjson"
    messages_file.write_text("", encoding="utf-8")
    runtime_required_file = tmp_path / "runtime-required.txt"
    runtime_required_file.write_text("testRunStarted.id\n", encoding="utf-8")
    output_file = tmp_path / "governance.json"

    exit_code = main(
        [
            "report",
            "--messages-file",
            str(messages_file),
            "--baseline-release",
            "v32.0.1",
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


def test_governance_report_rejects_partly_applicable_decision_for_runtime_required_capability(
    tmp_path, monkeypatch
) -> None:
    monkeypatch.setattr(
        message_capability_governance, "generate_inventory", lambda _schema_dir: _single_field_inventory()
    )

    messages_file = tmp_path / "messages.ndjson"
    messages_file.write_text(
        '{"testRunStarted":{"id":"123","timestamp":{"seconds":0,"nanos":0}}}\n',
        encoding="utf-8",
    )
    decisions_file = tmp_path / "decisions.json"
    decisions_file.write_text(
        json.dumps(
            [
                {
                    "capability_id": "testRunStarted.id",
                    "status": "Partly-Applicable",
                    "rationale": "Java language model is mapped in Python runtime with no native equivalent model.",
                    "decision_owner": "Coverage Governance",
                    "evidence_refs": ["tests/messages/test_governance.py"],
                    "reviewed_at": "2026-03-02T00:00:00+00:00",
                    "release_target": "v32.0.1",
                }
            ]
        ),
        encoding="utf-8",
    )
    runtime_required_file = tmp_path / "runtime-required.txt"
    runtime_required_file.write_text("testRunStarted.id\n", encoding="utf-8")
    output_file = tmp_path / "governance.json"

    with pytest.raises(ValueError, match="mandatory scope capabilities cannot use deferred statuses"):
        main(
            [
                "report",
                "--messages-file",
                str(messages_file),
                "--baseline-release",
                "v32.0.1",
                "--decisions",
                str(decisions_file),
                "--runtime-required-capabilities-file",
                str(runtime_required_file),
                "--require-runtime-required-covered",
                "--output",
                str(output_file),
            ]
        )


def test_governance_report_non_runtime_classification_gate_fails_without_decisions(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(
        message_capability_governance, "generate_inventory", lambda _schema_dir: _single_field_inventory()
    )

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
            "--require-non-runtime-classified",
            "--output",
            str(output_file),
        ]
    )

    assert exit_code == 1


def test_governance_report_rejects_non_implementable_without_required_hard_issue_fields(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(
        message_capability_governance, "generate_inventory", lambda _schema_dir: _single_field_inventory()
    )

    messages_file = tmp_path / "messages.ndjson"
    messages_file.write_text("", encoding="utf-8")
    decisions_file = tmp_path / "decisions.json"
    decisions_file.write_text(
        json.dumps(
            [
                {
                    "capability_id": "testRunStarted.id",
                    "status": "Non-Implementable",
                    "rationale": "Python runtime cannot emit this shape",
                    "decision_owner": "Coverage Governance",
                    "evidence_refs": ["tests/messages/test_governance.py"],
                    "reviewed_at": "2026-03-02T00:00:00+00:00",
                    "release_target": "v32.0.1",
                }
            ]
        ),
        encoding="utf-8",
    )
    output_file = tmp_path / "governance.json"

    with pytest.raises(ValueError, match="missing required evidence fields: recheck_trigger, hard_limitation"):
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


def test_governance_report_rejects_non_implementable_when_runtime_evidence_exists(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(
        message_capability_governance, "generate_inventory", lambda _schema_dir: _single_field_inventory()
    )

    messages_file = tmp_path / "messages.ndjson"
    messages_file.write_text(
        '{"testRunStarted":{"id":"123","timestamp":{"seconds":0,"nanos":0}}}\n',
        encoding="utf-8",
    )
    decisions_file = tmp_path / "decisions.json"
    decisions_file.write_text(
        json.dumps(
            [
                {
                    "capability_id": "testRunStarted.id",
                    "status": "Non-Implementable",
                    "rationale": "Hard technical limitation documented",
                    "hard_limitation": "Hard technical limitation: runtime cannot expose this field.",
                    "decision_owner": "Coverage Governance",
                    "evidence_refs": ["tests/messages/test_governance.py"],
                    "reviewed_at": "2026-03-03T00:00:00+00:00",
                    "release_target": "v32.0.1",
                    "recheck_trigger": "runtime-hook-surface-change",
                }
            ]
        ),
        encoding="utf-8",
    )
    output_file = tmp_path / "governance.json"

    with pytest.raises(ValueError, match="runtime evidence but is marked Non-Implementable"):
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
