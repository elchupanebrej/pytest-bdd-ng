import json

import pytest

from pytest_cuke.message_capability_governance_cli import main
from pytest_cuke.model.message_status_governance import CAPABILITY_STATUSES


def decision(status="Non-Implementable"):
    return {
        "capability_id": "hook.source_reference.java_method.class_name",
        "release_target": "34.2.1",
        "status": status,
        "comment": "The language model differs in this runtime; this is only a validation test decision.",
        "decision_owner": "test-only owner",
        "evidence_refs": ["proof://test-only/runtime-observation"],
        "reviewed_at": "2026-11-01T00:00:00+00:00",
        "hard_limitation": "The test models a Python-only hook without a JVM declaring class.",
        "recheck_trigger": "A real foreign-runtime event source is added.",
    }


@pytest.mark.parametrize("status", CAPABILITY_STATUSES)
def test_public_cli_preserves_complete_proof_metadata(tmp_path, status):
    original = decision(status)
    source = tmp_path / "decisions.json"
    destination = tmp_path / "validated.json"
    source.write_text(json.dumps({"decisions": [original]}))
    assert main(["validate-decision", "--input", str(source), "--output", str(destination)]) == 0
    assert json.loads(destination.read_text())["decisions"] == [original]


@pytest.mark.parametrize("status", [status for status in CAPABILITY_STATUSES if status != "Implemented"])
@pytest.mark.parametrize("field", ["decision_owner", "evidence_refs", "reviewed_at"])
def test_public_cli_rejects_unreviewable_nonimplemented_decisions(tmp_path, capsys, status, field):
    incomplete = decision(status)
    incomplete.pop(field)
    source = tmp_path / "incomplete.json"
    source.write_text(json.dumps([incomplete]))
    assert main(["validate-decision", "--input", str(source)]) != 0
    captured = capsys.readouterr()
    assert field in captured.out + captured.err


@pytest.mark.parametrize("field", ["hard_limitation", "recheck_trigger"])
def test_nonimplementable_requires_technical_proof_and_a_recheck_condition(tmp_path, capsys, field):
    incomplete = decision()
    incomplete.pop(field)
    source = tmp_path / "unproven.json"
    source.write_text(json.dumps([incomplete]))
    assert main(["validate-decision", "--input", str(source)]) != 0
    captured = capsys.readouterr()
    assert field in captured.out + captured.err


def test_report_retains_the_proof_without_counting_it_as_runtime_observation(tmp_path):
    original = decision()
    source = tmp_path / "decisions.json"
    messages = tmp_path / "empty.ndjson"
    destination = tmp_path / "report.json"
    source.write_text(json.dumps([original]))
    synthetic = [
        {
            "meta": {
                "protocolVersion": "34.2.1",
                "implementation": {"name": "synthetic-test", "version": "0"},
                "runtime": {"name": "python", "version": "3.14"},
                "os": {"name": "test", "version": "0"},
                "cpu": {"name": "test"},
            }
        },
        {"testRunStarted": {"id": "synthetic-run", "timestamp": {"seconds": 1, "nanos": 0}}},
        {
            "testRunFinished": {
                "success": True,
                "testRunStartedId": "synthetic-run",
                "timestamp": {"seconds": 2, "nanos": 0},
            }
        },
    ]
    messages.write_text("".join(json.dumps(row) + "\n" for row in synthetic))
    assert (
        main(
            [
                "report",
                "--messages-file",
                str(messages),
                "--input-kind",
                "synthetic",
                "--decisions",
                str(source),
                "--format",
                "json",
                "--output",
                str(destination),
            ]
        )
        == 0
    )
    report = json.loads(destination.read_text())
    assert report["decisions"] == [original]
    assert report["observations"]["source_kind"] == "synthetic"
    assert all(not row["observed_runtime"] for row in report["capabilities"])

    markdown = tmp_path / "report.md"
    assert (
        main(
            [
                "report",
                "--messages-file",
                str(messages),
                "--input-kind",
                "synthetic",
                "--decisions",
                str(source),
                "--format",
                "markdown",
                "--output",
                str(markdown),
            ]
        )
        == 0
    )
    rendered = markdown.read_text()
    for field in ["decision_owner", "reviewed_at", "hard_limitation", "recheck_trigger"]:
        assert original[field] in rendered
    assert original["evidence_refs"][0] in rendered


def test_decision_diff_detects_changed_proof_owner(tmp_path):
    inventory = tmp_path / "inventory.json"
    assert main(["sync", "--baseline-release", "34.2.1", "--output", str(inventory)]) == 0
    previous = decision()
    current = {**previous, "decision_owner": "new test-only owner"}
    before = tmp_path / "before.json"
    after = tmp_path / "after.json"
    output = tmp_path / "diff.json"
    before.write_text(json.dumps([previous]))
    after.write_text(json.dumps([current]))
    assert (
        main(
            [
                "diff",
                "--previous-baseline",
                "34.2.1",
                "--current-baseline",
                "34.2.1",
                "--previous",
                str(inventory),
                "--current",
                str(inventory),
                "--previous-decisions",
                str(before),
                "--current-decisions",
                str(after),
                "--output",
                str(output),
            ]
        )
        == 0
    )
    assert json.loads(output.read_text())["changed_decision_ids"] == [previous["capability_id"] + "@34.2.1"]
