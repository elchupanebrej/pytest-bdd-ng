from __future__ import annotations

import json
from pathlib import Path

import pytest

from pytest_cuke.model.message_capability_inventory import (
    build_capability_inventory,
    capability_inventory_to_dict,
    capabilities_from_json,
    normalize_capability_id,
    normalize_capability_ids,
    sync_capability_inventory,
)
from pytest_cuke.model.message_converter import make_test_run_finished, make_test_run_started
from pytest_cuke.model.message_capability import MessageCapability
from pytest_cuke.model.message_baseline_diff import build_baseline_diff
from pytest_cuke.model.message_governance_checklist import build_governance_checklist
from pytest_cuke.model.message_types import message_to_dict
from pytest_cuke.message_capability_governance_cli import _format_report
from pytest_cuke.model.message_status_governance import (
    CapabilityDecision,
    validate_decisions,
)
from pytest_cuke.message_capability_governance import build_capability_report

SCHEMA_DIR = Path(__file__).parents[3] / "src/pytest_cuke/model/message_schemas"


def test_capability_ids_normalize_payload_and_field_casing() -> None:
    assert normalize_capability_id("testRunStarted.testCaseId") == "test_run_started.test_case_id"
    assert normalize_capability_id("test_run_started.test_case_id") == "test_run_started.test_case_id"
    assert normalize_capability_ids(["testRunStarted.testCaseId", "test_run_started.test_case_id"]) == (
        "test_run_started.test_case_id",
    )
    duplicate_spellings = (
        MessageCapability(
            "testRunStarted.testCaseId",
            "27.0.0",
            "Test case id",
            "The canonical test case id.",
            "lifecycle",
            frozenset({"emitted_envelope_payload"}),
            "z/TestRunStarted.json#/properties/testCaseId",
        ),
        MessageCapability(
            "test_run_started.test_case_id",
            "27.0.0",
            "Test case id",
            "Identifier of a test case.",
            "lifecycle",
            frozenset({"emitted_envelope_payload"}),
            "a/TestRunStarted.json#/properties/test_case_id",
        ),
    )
    normalized = sync_capability_inventory("28.0.0", duplicate_spellings)
    reversed_normalized = sync_capability_inventory("28.0.0", reversed(duplicate_spellings))
    assert [item.capability_id for item in normalized] == ["test_run_started.test_case_id"]
    assert normalized[0].baseline_release == "28.0.0"
    assert normalized == reversed_normalized


@pytest.mark.parametrize("capability_id", ["attachment.-", "attachment.foo.-"])
def test_capability_id_rejects_segments_that_normalize_to_empty(capability_id: str) -> None:
    with pytest.raises(ValueError, match="normalizes to empty"):
        normalize_capability_id(capability_id)


def test_inventory_rejects_unknown_relevance_impacts() -> None:
    with pytest.raises(ValueError, match="unknown affects values"):
        capabilities_from_json(
            {
                "baseline_release": "28.0.0",
                "capabilities": [
                    {
                        "capability_id": "attachment.body",
                        "affects": ["emitted_envelope_payload_typo"],
                    }
                ],
            }
        )


def test_inventory_walks_schema_references_and_is_deterministic() -> None:
    first = build_capability_inventory(SCHEMA_DIR, baseline_release="28.0.0")
    second = build_capability_inventory(SCHEMA_DIR, baseline_release="28.0.0")

    ids = [capability.capability_id for capability in first]
    assert ids == sorted(set(ids))
    assert ids == [capability.capability_id for capability in second]
    assert "test_run_started.timestamp.seconds" in ids
    timestamp = next(item for item in first if item.capability_id == "test_run_started.timestamp.seconds")
    assert timestamp.source_reference == "Timestamp.json#/properties/seconds"
    assert "test_run_hook_started.test_run_started_id" in ids
    assert all(capability.baseline_release == "28.0.0" for capability in first)


def test_decision_validation_requires_comment_for_non_implemented_status() -> None:
    decision = CapabilityDecision(
        capability_id="attachment.body",
        status="Non-Implementable",
        release_target="28.0.0",
    )

    with pytest.raises(ValueError, match=r"attachment\.body.*comment"):
        validate_decisions([decision])


def test_decision_validation_rejects_conflicting_terminal_statuses() -> None:
    decisions = [
        CapabilityDecision(
            capability_id="attachment.body",
            status="Implemented",
            release_target="28.0.0",
        ),
        CapabilityDecision(
            capability_id="attachment.body",
            status="Not-Applicable",
            release_target="28.0.0",
            comment="This field is not used by this release.",
        ),
    ]

    with pytest.raises(ValueError, match=r"attachment\.body@28\.0\.0"):
        validate_decisions(decisions)


def test_checklist_prefers_exact_release_decision_to_next_release_default() -> None:
    capability = MessageCapability(
        capability_id="test_run_started.timestamp.seconds",
        baseline_release="28.0.0",
        name="Start timestamp seconds",
        description="A start timestamp field.",
        category="lifecycle",
        affects=frozenset({"emitted_envelope_payload"}),
    )
    decisions = (
        CapabilityDecision(capability.capability_id, "Implemented", "next-release"),
        CapabilityDecision(
            capability.capability_id,
            "Partly-Applicable",
            "28.0.0",
            "This release only guarantees second precision.",
        ),
        CapabilityDecision(capability.capability_id, "Implemented", "29.0.0"),
    )

    checklist = build_governance_checklist(
        (capability,),
        decisions,
        baseline_release="28.0.0",
        mandatory_capability_ids=(capability.capability_id,),
    )

    assert checklist.entries[0].status == "Partly-Applicable"
    assert checklist.entries[0].comment == "This release only guarantees second precision."
    assert checklist.entries[0].release_blocker is True


def test_checklist_keeps_mandatory_fields_missing_from_a_baseline_visible() -> None:
    missing_id = "test_run_started.future_field"

    checklist = build_governance_checklist(
        (),
        (),
        baseline_release="28.0.0",
        mandatory_capability_ids=(missing_id,),
    )

    assert len(checklist.entries) == 1
    assert checklist.entries[0].capability_id == missing_id
    assert checklist.entries[0].status == "Pending"
    assert checklist.entries[0].release_blocker is True


def test_baseline_diff_reports_field_and_decision_changes_without_mutating_inputs() -> None:
    previous = (
        MessageCapability(
            "test_run_started.timestamp.seconds",
            "27.0.0",
            "Timestamp seconds",
            "Previous description.",
            "lifecycle",
            frozenset({"emitted_envelope_payload"}),
        ),
        MessageCapability(
            "test_run_finished.success",
            "27.0.0",
            "Success",
            "A success flag.",
            "lifecycle",
            frozenset({"emitted_envelope_payload"}),
        ),
    )
    current = (
        MessageCapability(
            "test_run_started.timestamp.seconds",
            "28.0.0",
            "Timestamp seconds",
            "Updated description.",
            "lifecycle",
            frozenset({"emitted_envelope_payload"}),
        ),
        MessageCapability(
            "test_run_started.id",
            "28.0.0",
            "Start id",
            "A run id.",
            "lifecycle",
            frozenset({"emitted_envelope_payload"}),
        ),
    )
    previous_decisions = (
        CapabilityDecision("test_run_started.timestamp.seconds", "Implemented", "next-release"),
        CapabilityDecision(
            "test_run_finished.success",
            "Not-Applicable",
            "next-release",
            "This event does not use a success field.",
        ),
    )
    current_decisions = (
        CapabilityDecision(
            "test_run_started.timestamp.seconds",
            "Partly-Applicable",
            "next-release",
            "Only second precision is guaranteed.",
        ),
        CapabilityDecision("test_run_started.id", "Implemented", "next-release"),
    )

    diff = build_baseline_diff(
        previous_baseline="27.0.0",
        current_baseline="28.0.0",
        previous_capabilities=previous,
        current_capabilities=current,
        previous_decisions=previous_decisions,
        current_decisions=current_decisions,
    )

    assert diff.added_capability_ids == ("test_run_started.id",)
    assert diff.changed_capability_ids == ("test_run_started.timestamp.seconds",)
    assert diff.removed_capability_ids == ("test_run_finished.success",)
    assert diff.added_decision_ids == ("test_run_started.id@next-release",)
    assert diff.changed_decision_ids == ("test_run_started.timestamp.seconds@next-release",)
    assert diff.removed_decision_ids == ("test_run_finished.success@next-release",)


def test_report_separates_runtime_observations_from_synthetic_samples() -> None:
    capabilities = build_capability_inventory(SCHEMA_DIR, baseline_release="28.0.0")
    envelopes = [make_test_run_started(1), make_test_run_finished(2)]
    required_id = "test_run_started.timestamp.seconds"

    runtime = build_capability_report(
        envelopes,
        capabilities=capabilities,
        decisions=(),
        baseline_release="28.0.0",
        input_kind="runtime",
        mandatory_capability_ids=(required_id,),
        runtime_required_capability_ids=(required_id,),
    )
    synthetic = build_capability_report(
        envelopes,
        capabilities=capabilities,
        decisions=(),
        baseline_release="28.0.0",
        input_kind="synthetic",
        mandatory_capability_ids=(required_id,),
        runtime_required_capability_ids=(required_id,),
    )

    assert runtime["observations"]["source_kind"] == "runtime"
    assert synthetic["observations"]["source_kind"] == "synthetic"
    runtime_capability = next(item for item in runtime["capabilities"] if item["capability_id"] == required_id)
    synthetic_capability = next(item for item in synthetic["capabilities"] if item["capability_id"] == required_id)
    assert runtime_capability["observed_runtime"] is True
    assert synthetic_capability["observed_runtime"] is False
    assert synthetic_capability["observed_sample"] is True


def test_markdown_report_lists_scope_observed_fields_and_explicit_decisions() -> None:
    capability_id = "test_run_started.timestamp.seconds"
    comment = "Second precision is the implemented runtime contract."
    report = build_capability_report(
        [make_test_run_started(1), make_test_run_finished(2)],
        capabilities=build_capability_inventory(SCHEMA_DIR, baseline_release="28.0.0"),
        decisions=(CapabilityDecision(capability_id, "Partly-Applicable", "28.0.0", comment),),
        baseline_release="28.0.0",
        input_kind="runtime",
        mandatory_capability_ids=(capability_id,),
        runtime_required_capability_ids=(capability_id,),
    )

    markdown = _format_report(report, "markdown")

    assert "## Scope" in markdown
    assert "## Observed fields" in markdown
    assert "## Decisions" in markdown
    assert f"`{capability_id}`" in markdown
    assert comment in markdown
    assert report["decisions"] == [
        {
            "capability_id": capability_id,
            "status": "Partly-Applicable",
            "release_target": "28.0.0",
            "comment": comment,
        }
    ]


@pytest.mark.parametrize(
    ("gate", "expected_id"),
    [
        ("require_runtime_required_covered", "test_step_started.test_step_id"),
        ("require_non_runtime_classified", "test_step_started.test_step_id"),
        ("require_fully_governed", "test_step_started.test_step_id"),
    ],
)
def test_report_gates_fail_independently_with_offending_capability_ids(
    gate: str,
    expected_id: str,
) -> None:
    capabilities = build_capability_inventory(SCHEMA_DIR, baseline_release="28.0.0")
    report = build_capability_report(
        [make_test_run_started(1), make_test_run_finished(2)],
        capabilities=capabilities,
        decisions=(),
        baseline_release="28.0.0",
        input_kind="runtime",
        mandatory_capability_ids=(expected_id,)
        if gate in {"require_fully_governed", "require_runtime_required_covered"}
        else (),
        runtime_required_capability_ids=(expected_id,) if gate == "require_runtime_required_covered" else (),
        **{gate: True},
    )

    assert report["gates"]["passed"] is False
    assert any(expected_id in result for result in report["gates"]["failures"])


def test_runtime_required_scope_must_always_be_subset_of_mandatory_scope() -> None:
    with pytest.raises(ValueError, match="runtime-required scope must be a subset of mandatory scope"):
        build_capability_report(
            [make_test_run_started(1), make_test_run_finished(2)],
            capabilities=build_capability_inventory(SCHEMA_DIR, baseline_release="28.0.0"),
            decisions=(),
            baseline_release="28.0.0",
            input_kind="runtime",
            mandatory_capability_ids=(),
            runtime_required_capability_ids=("test_run_started.timestamp.seconds",),
        )


def test_invalid_stream_does_not_replace_existing_report(tmp_path: Path) -> None:
    messages_file = tmp_path / "messages.ndjson"
    report_file = tmp_path / "report.json"
    messages_file.write_text('{"testRunStarted":{"timestamp":{"seconds":1,"nanos":0}}}\n', encoding="utf-8")
    report_file.write_text('{"previous":"valid"}\n', encoding="utf-8")

    from pytest_cuke.message_capability_governance_cli import main

    exit_code = main(
        [
            "report",
            "--messages-file",
            str(messages_file),
            "--input-kind",
            "runtime",
            "--output",
            str(report_file),
        ]
    )

    assert exit_code == 2
    assert json.loads(report_file.read_text(encoding="utf-8")) == {"previous": "valid"}


@pytest.mark.parametrize("unknown_field", ["unexpected", "test_run_started"])
def test_unknown_raw_wire_fields_are_rejected_before_conversion(
    unknown_field: str,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    messages_file = tmp_path / "messages.ndjson"
    start = {
        "testRunStarted": {"timestamp": {"seconds": 1, "nanos": 0}},
        unknown_field: {"timestamp": {"seconds": 9, "nanos": 0}},
    }
    finish = {"testRunFinished": {"timestamp": {"seconds": 2, "nanos": 0}, "success": True}}
    messages_file.write_text("\n".join(json.dumps(item) for item in (start, finish)) + "\n", encoding="utf-8")
    report_file = tmp_path / "report.json"
    report_file.write_text('{"previous":"valid"}\n', encoding="utf-8")

    from pytest_cuke.message_capability_governance_cli import main

    exit_code = main(
        [
            "report",
            "--messages-file",
            str(messages_file),
            "--input-kind",
            "runtime",
            "--output",
            str(report_file),
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 2
    assert unknown_field in captured.err
    assert "additional properties" in captured.err.lower()
    assert json.loads(report_file.read_text(encoding="utf-8")) == {"previous": "valid"}


@pytest.mark.parametrize(
    ("gate", "capability_id", "scope_flag"),
    [
        ("--require-fully-governed", "test_step_started.test_step_id", "--mandatory-capabilities-file"),
        (
            "--require-runtime-required-covered",
            "test_run_started.id",
            "--runtime-required-capabilities-file",
        ),
        ("--require-non-runtime-classified", "test_step_started.test_step_id", None),
    ],
)
def test_public_cli_gates_fail_independently_with_capability_ids(
    gate: str,
    capability_id: str,
    scope_flag: str | None,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    capability = MessageCapability(
        capability_id=capability_id,
        baseline_release="28.0.0",
        name="Required field",
        description="A governance test field.",
        category="lifecycle",
        affects=frozenset({"emitted_envelope_payload"}),
    )
    inventory_file = tmp_path / "capabilities.json"
    inventory_file.write_text(
        json.dumps(capability_inventory_to_dict((capability,), baseline_release="28.0.0")),
        encoding="utf-8",
    )
    messages_file = tmp_path / "messages.ndjson"
    messages = (make_test_run_started(1), make_test_run_finished(2))
    messages_file.write_text(
        "".join(json.dumps(message_to_dict(message)) + "\n" for message in messages),
        encoding="utf-8",
    )
    report_file = tmp_path / "report.json"
    scope_file = tmp_path / "scope.txt"
    scope_file.write_text(capability_id + "\n", encoding="utf-8")
    arguments = [
        "report",
        "--messages-file",
        str(messages_file),
        "--input-kind",
        "synthetic",
        "--capabilities",
        str(inventory_file),
    ]
    if scope_flag is not None:
        arguments.extend((scope_flag, str(scope_file)))
        if scope_flag == "--runtime-required-capabilities-file":
            arguments.extend(("--mandatory-capabilities-file", str(scope_file)))
    arguments.extend((gate, "--output", str(report_file)))

    from pytest_cuke.message_capability_governance_cli import main

    exit_code = main(arguments)

    report = json.loads(report_file.read_text(encoding="utf-8"))
    captured = capsys.readouterr()
    assert exit_code == 1
    assert report["gates"]["passed"] is False
    assert capability_id in " ".join(report["gates"]["failures"])
    assert capability_id in captured.err


@pytest.mark.parametrize("invalid_kind", ["schema", "decision"])
def test_invalid_schema_or_decision_does_not_replace_existing_output(
    invalid_kind: str,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    output_file = tmp_path / "valid-output.json"
    output_file.write_text('{"previous":"valid"}\n', encoding="utf-8")

    from pytest_cuke.message_capability_governance_cli import main

    if invalid_kind == "schema":
        schema_dir = tmp_path / "schemas"
        schema_dir.mkdir()
        (schema_dir / "Envelope.schema.json").write_text('{"type":"object"}\n', encoding="utf-8")
        exit_code = main(
            [
                "sync",
                "--baseline-release",
                "28.0.0",
                "--schema-dir",
                str(schema_dir),
                "--output",
                str(output_file),
            ]
        )
    else:
        decisions_file = tmp_path / "decisions.json"
        decisions_file.write_text(
            json.dumps(
                [
                    {
                        "capability_id": "attachment.body",
                        "status": "Non-Implementable",
                        "release_target": "28.0.0",
                    }
                ]
            ),
            encoding="utf-8",
        )
        exit_code = main(["validate-decision", "--input", str(decisions_file), "--output", str(output_file)])

    captured = capsys.readouterr()
    assert exit_code == 2
    assert "error:" in captured.err
    assert json.loads(output_file.read_text(encoding="utf-8")) == {"previous": "valid"}


def test_installed_schema_sync_rejects_a_mislabeled_baseline(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    output_file = tmp_path / "valid-inventory.json"
    output_file.write_text('{"previous":"valid"}\n', encoding="utf-8")

    from pytest_cuke.message_capability_governance_cli import main

    exit_code = main(
        [
            "sync",
            "--baseline-release",
            "27.0.0",
            "--output",
            str(output_file),
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 2
    assert "does not match installed schema baseline" in captured.err
    assert json.loads(output_file.read_text(encoding="utf-8")) == {"previous": "valid"}
