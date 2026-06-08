"""Coverage-focused tests for Phase 14 validation gaps."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from typing import TYPE_CHECKING

import pytest

from pytest_bdd.mimetype import Mimetype, Suffix, mimetype_suffix_pairs, struct_bdd_suffixes
from pytest_bdd.model.coverage.tracker import ObservedCoverage
from pytest_bdd.model.message_baseline_diff import (
    BaselineComparisonSchedule,
    build_baseline_diff,
    execute_weekly_baseline_diff,
    is_weekly_run_due,
    next_weekly_run_at,
)
from pytest_bdd.model.message_capability import (
    MessageCapability,
    capability_is_relevant,
    classify_capability_relevance,
)
from pytest_bdd.model.message_converter import governance_value_to_dict
from pytest_bdd.model.message_governance_checklist import (
    build_governance_checklist,
    render_checklist_markdown,
)
from pytest_bdd.model.message_serialization import (
    MessageSerializationProfile,
    normalize_envelope_dict_for_profile,
)
from pytest_bdd.model.message_status_governance import (
    CapabilityDecision,
    ensure_single_status_per_capability,
    evaluate_release_blockers,
    missing_required_evidence_fields,
    normalize_capability_status,
    validate_capability_decision,
)
from pytest_bdd.model.message_validation_result import MessageValidationResult, MessageValidationViolation
from pytest_bdd.model.message_validation_xdist import (
    format_xdist_transport_compatibility_error,
    validate_execnet_serializable_payload,
    validate_xdist_reporting_compatibility,
)
from pytest_bdd.util.data_table import data_table_to_dicts
from pytest_bdd.util.matrix import (
    build_matrix,
    build_migration_coverage_summary,
    discover_feature_scenario_ids,
    discover_user_facing_test_scenario_ids,
    expand_tox_env_names,
    extract_factors_from_tox_ini,
)
from pytest_bdd.util.temp_root import prefer_posix_temp_root
from pytest_bdd.util.url import is_local_url, is_url_parsable
from pytest_bdd.util.webloc import read, write

if TYPE_CHECKING:
    from pathlib import Path

pytestmark = [pytest.mark.unit]


@dataclass
class _GovernancePayload:
    name: str
    created_at: datetime


def _capability(
    capability_id: str,
    *,
    affects: frozenset[str] = frozenset({"status_mapping"}),
    explicit_relevance: str | None = None,
) -> MessageCapability:
    return MessageCapability(
        capability_id=capability_id,
        baseline_release="v1",
        name=f"Capability {capability_id}",
        description="Tracks coverage for a capability",
        category="core",
        affects=affects,
        explicit_relevance=explicit_relevance,
    )


def test_mimetype_suffix_tables_include_struct_bdd_variants() -> None:
    assert Suffix.struct_bdd in struct_bdd_suffixes
    assert (Mimetype.gherkin_plain, Suffix.feature) in mimetype_suffix_pairs
    assert Mimetype.struct_bdd_hjson.value == "application/x.struct_bdd+hjson"
    assert Mimetype.python.value == "text/x-python"


def test_data_table_to_dicts_maps_first_column_to_remaining_cells() -> None:
    table = SimpleNamespace(
        rows=[
            SimpleNamespace(cells=[SimpleNamespace(value="status"), SimpleNamespace(value="pass")]),
            SimpleNamespace(
                cells=[
                    SimpleNamespace(value="tags"),
                    SimpleNamespace(value="unit"),
                    SimpleNamespace(value="fast"),
                ],
            ),
        ],
    )

    assert data_table_to_dicts(table) == {"status": ["pass"], "tags": ["unit", "fast"]}
    assert data_table_to_dicts(None) == {}


def test_url_and_webloc_helpers_round_trip(tmp_path: Path) -> None:
    webloc_path = tmp_path / "link.webloc"

    write(webloc_path, "https://example.test/docs")

    assert read(webloc_path) == "https://example.test/docs"
    assert is_local_url("features/example.feature.md")
    assert not is_local_url("https://example.test/docs")
    assert not is_local_url(object())
    assert is_url_parsable("https://example.test/docs")


def test_temp_root_helper_returns_false_for_non_wsl_temp() -> None:
    assert prefer_posix_temp_root() is False


def test_message_capability_relevance_uses_explicit_and_impact_rules() -> None:
    relevant = _capability("cap-1")
    explicit = _capability("cap-2", affects=frozenset(), explicit_relevance="relevant")
    out_of_scope = _capability("cap-3", affects=frozenset())

    assert classify_capability_relevance(relevant) == "relevant"
    assert capability_is_relevant(explicit)
    assert classify_capability_relevance(out_of_scope) == "out_of_scope"


def test_governance_value_to_dict_normalizes_dataclasses_and_sets() -> None:
    created_at = datetime(2026, 5, 20, tzinfo=timezone.utc)
    value = {"payload": _GovernancePayload("capability", created_at), "tags": {"b", "a"}}

    result = governance_value_to_dict(value)

    assert result["payload"]["name"] == "capability"
    assert result["payload"]["created_at"] == "2026-05-20T00:00:00+00:00"
    assert sorted(result["tags"]) == ["a", "b"]


def test_message_status_governance_flags_missing_and_duplicate_decisions() -> None:
    pending = CapabilityDecision(capability_id="cap-1", status="Pending", release_target="v1")
    duplicate = CapabilityDecision(capability_id="cap-1", status="Implemented", release_target="v1")
    non_implementable = CapabilityDecision(
        capability_id="cap-2",
        status="Non-Implementable",
        release_target="v1",
        rationale="not implemented yet",
    )

    assert normalize_capability_status("done") == "Implemented"
    assert "rationale" in missing_required_evidence_fields(pending)
    assert "hard_limitation" in missing_required_evidence_fields(non_implementable)
    assert validate_capability_decision(non_implementable).accepted is False
    assert ensure_single_status_per_capability([pending, duplicate]).duplicates == ("cap-1@v1",)


def test_release_blocker_and_checklist_rendering_include_missing_relevant_capabilities() -> None:
    capability = _capability("cap-1")
    deferred = CapabilityDecision(
        capability_id="cap-2",
        status="Partly-Applicable",
        release_target="v1",
        rationale="Language runtime model mismatch",
        decision_owner="qa",
        evidence_refs=("tests/example.py",),
        reviewed_at=datetime(2026, 5, 20, tzinfo=timezone.utc),
    )

    blockers = evaluate_release_blockers([deferred], relevant_capability_ids=("cap-1", "cap-2"))
    checklist = build_governance_checklist([capability], [deferred])
    rendered = render_checklist_markdown(checklist)

    assert blockers.unresolved_blocker_capability_ids == ("cap-1",)
    assert blockers.deferred_capability_ids == ("cap-2",)
    assert "cap-1" in rendered
    assert "Unresolved blockers" in rendered


def test_governance_checklist_marks_added_changed_removed_entries() -> None:
    now = datetime(2026, 5, 20, tzinfo=timezone.utc)
    cap_added = _capability("cap-added")
    cap_changed = _capability("cap-changed")
    decision_added = CapabilityDecision(
        capability_id="cap-added",
        status="Implemented",
        release_target="v1",
    )
    decision_changed = CapabilityDecision(
        capability_id="cap-changed",
        status="Not-Applicable",
        release_target="v1",
        rationale="Capability is covered by upstream runtime",
        decision_owner="qa",
        evidence_refs=("docs/features/example.rst",),
        reviewed_at=now,
    )
    diff = build_baseline_diff(
        previous_baseline="v1",
        current_baseline="v2",
        previous_capabilities=[
            _capability("cap-changed", affects=frozenset({"lifecycle_linkage"})),
            _capability("cap-removed"),
        ],
        current_capabilities=[cap_added, cap_changed],
        generated_at=now,
    )

    checklist = build_governance_checklist(
        [cap_added, cap_changed],
        [decision_added, decision_changed],
        baseline_diff=diff,
    )

    entries = {entry.capability_id: entry for entry in checklist.entries}
    assert entries["cap-added"].delta == "added"
    assert entries["cap-added"].disposition == "approved"
    assert entries["cap-changed"].delta == "changed"
    assert entries["cap-changed"].comment_required
    assert entries["cap-removed"].delta == "removed"
    assert entries["cap-removed"].comment == "Capability removed from baseline"


def test_baseline_diff_detects_added_changed_removed_and_due_schedule() -> None:
    now = datetime(2026, 5, 20, tzinfo=timezone.utc)
    previous = [_capability("cap-1"), _capability("cap-2")]
    current = [_capability("cap-1", affects=frozenset({"lifecycle_linkage"})), _capability("cap-3")]
    schedule = BaselineComparisonSchedule(
        schedule_id="weekly",
        cadence="weekly",
        last_run_at=now - timedelta(days=8),
        next_run_at=now - timedelta(days=1),
    )

    diff = build_baseline_diff(
        previous_baseline="v1",
        current_baseline="v2",
        previous_capabilities=previous,
        current_capabilities=current,
        generated_at=now,
    )
    result = execute_weekly_baseline_diff(
        schedule=schedule,
        previous_baseline="v1",
        current_baseline="v2",
        previous_capabilities=previous,
        current_capabilities=current,
        now=now,
    )

    assert next_weekly_run_at(now) == now + timedelta(days=7)
    assert is_weekly_run_due(schedule, now=now)
    assert diff.added_capability_ids == ("cap-3",)
    assert diff.changed_capability_ids == ("cap-1",)
    assert diff.removed_capability_ids == ("cap-2",)
    assert result.due is True
    assert result.schedule.next_run_at == now + timedelta(days=7)


def test_baseline_diff_skips_when_schedule_not_due() -> None:
    now = datetime(2026, 5, 20, tzinfo=timezone.utc)
    future = BaselineComparisonSchedule(
        schedule_id="weekly",
        cadence="weekly",
        last_run_at=now,
        next_run_at=now + timedelta(days=1),
    )
    wrong_cadence = BaselineComparisonSchedule(
        schedule_id="monthly",
        cadence="monthly",  # type: ignore[arg-type] — argument type compatibility
        last_run_at=now - timedelta(days=30),
        next_run_at=now - timedelta(days=1),
    )

    result = execute_weekly_baseline_diff(
        schedule=future,
        previous_baseline="v1",
        current_baseline="v2",
        previous_capabilities=[],
        current_capabilities=[],
        now=now,
    )

    assert not is_weekly_run_due(future, now=now)
    assert not is_weekly_run_due(wrong_cadence, now=now)
    assert result.due is False
    assert result.record is None


def test_message_validation_result_and_coverage_tracker_record_status() -> None:
    coverage = ObservedCoverage()
    violation = MessageValidationViolation(code="INVALID_PAYLOAD_SHAPE", message="bad payload")
    passing = MessageValidationResult(
        status="pass",
        orphan_reference_count=0,
        duplicate_lifecycle_id_count=0,
        blocked_for_release=False,
        violations=(),
        observed_coverage=coverage,
    )
    failing = MessageValidationResult(
        status="fail",
        orphan_reference_count=1,
        duplicate_lifecycle_id_count=0,
        blocked_for_release=True,
        violations=(violation,),
    )

    coverage.record_field("pickle", "astNodeIds", evidence_scenario_id="scenario-1")

    assert passing.is_valid
    assert not failing.is_valid
    assert ("pickle", "astNodeIds") in coverage.observed_fields
    assert coverage.evidence_scenarios["pickle", "astNodeIds"] == "scenario-1"


def test_message_serialization_profile_downgrades_pytest_bdd_pattern_types() -> None:
    envelope = {"stepDefinition": {"pattern": {"type": "PYTEST_BDD_PARSE_EXPRESSION"}}}
    normalized = normalize_envelope_dict_for_profile(envelope, profile=MessageSerializationProfile.schema_compatible)

    assert normalized["stepDefinition"]["pattern"]["type"] == "REGULAR_EXPRESSION"
    assert envelope["stepDefinition"]["pattern"]["type"] == "PYTEST_BDD_PARSE_EXPRESSION"
    assert normalize_envelope_dict_for_profile(envelope, profile=MessageSerializationProfile.extended) is envelope


def test_message_serialization_handles_snake_case_and_unknown_pattern_types() -> None:
    envelope = {"step_definition": {"pattern": {"type": "CUCUMBER_EXPRESSION"}}}
    normalized = normalize_envelope_dict_for_profile(envelope, profile=MessageSerializationProfile.schema_compatible)
    no_pattern = normalize_envelope_dict_for_profile(
        {"stepDefinition": {"pattern": "not-a-dict"}},
        profile=MessageSerializationProfile.schema_compatible,
    )

    assert normalized["step_definition"]["pattern"]["type"] == "CUCUMBER_EXPRESSION"
    assert no_pattern == {"stepDefinition": {"pattern": "not-a-dict"}}


def test_xdist_validation_reports_topology_and_serialization_failures() -> None:
    controller = validate_xdist_reporting_compatibility(
        xdist_active=True,
        is_worker=False,
        is_controller=True,
        remote_module_available=False,
        controller_event_patch_installed=True,
        worker_sender_available=True,
    )
    violations = validate_execnet_serializable_payload({"ok": [1, "two"], 3: "bad", "bad": object()})

    assert not controller.is_valid
    assert "pytest_xdist_getremotemodule" in controller.reason
    assert len(violations) == 2
    assert "Distributed reporting requires" in format_xdist_transport_compatibility_error("reason")


def test_xdist_validation_accepts_non_xdist_and_flags_worker_channel() -> None:
    inactive = validate_xdist_reporting_compatibility(
        xdist_active=False,
        is_worker=False,
        is_controller=False,
        remote_module_available=False,
        controller_event_patch_installed=False,
        worker_sender_available=False,
    )
    controller_patch = validate_xdist_reporting_compatibility(
        xdist_active=True,
        is_worker=False,
        is_controller=True,
        remote_module_available=True,
        controller_event_patch_installed=False,
        worker_sender_available=True,
    )
    worker = validate_xdist_reporting_compatibility(
        xdist_active=True,
        is_worker=True,
        is_controller=False,
        remote_module_available=True,
        controller_event_patch_installed=True,
        worker_sender_available=False,
    )
    serializable = validate_execnet_serializable_payload({"ok": ("tuple", 1, None, True)})

    assert inactive.is_valid
    assert not controller_patch.is_valid
    assert "controller support" in controller_patch.reason
    assert not worker.is_valid
    assert "worker channel sender" in worker.reason
    assert serializable == ()


def test_matrix_helpers_discover_factors_and_feature_ids(tmp_path: Path) -> None:
    tox_ini = tmp_path / "tox.ini"
    features = tmp_path / "features"
    tests = tmp_path / "tests"
    tox_ini.write_text("envlist = py{310,311}-pytest{70,latest}, py312-pytest80\n", encoding="utf-8")
    (features / "Area").mkdir(parents=True)
    (features / "Area" / "01 Example.feature.md").write_text("# Feature: Example", encoding="utf-8")
    (tests / "feature").mkdir(parents=True)
    (tests / "feature" / "test_no_scenario.py").write_text("def test_example(): pass", encoding="utf-8")

    python_factors, pytest_factors = extract_factors_from_tox_ini(tox_ini)
    entries = build_matrix(["310"], ["70", "latest"])
    summary = build_migration_coverage_summary(tests, features)

    assert python_factors == ["310", "311", "312"]
    assert pytest_factors == ["70", "80", "latest"]
    assert discover_feature_scenario_ids(features) == {"01-example"}
    assert discover_user_facing_test_scenario_ids(tests) == {"no-scenario"}
    assert expand_tox_env_names(entries) == ["py310-pytest70-coverage-lin", "py310-pytestlatest-coverage-lin"]
    assert summary.total_user_facing_scenarios == 2


def test_matrix_helpers_handle_missing_roots_and_non_matching_files(tmp_path: Path) -> None:
    features = tmp_path / "features"
    tests = tmp_path / "tests"
    (features / "Area").mkdir(parents=True)
    (features / "Area" / "not-a-feature.md").write_text("# Doc", encoding="utf-8")
    (features / "Area" / "Example.txt").write_text("Feature: ignored", encoding="utf-8")
    (tests / "feature").mkdir(parents=True)
    (tests / "feature" / "test_ignored.py").write_text("def test_ignored(): pass", encoding="utf-8")

    assert discover_feature_scenario_ids(features) == set()
    assert discover_feature_scenario_ids(tmp_path / "missing") == set()
    assert discover_user_facing_test_scenario_ids(tests) == set()
    assert discover_user_facing_test_scenario_ids(tmp_path / "missing") == set()
    assert build_migration_coverage_summary(tmp_path / "missing-tests", tmp_path / "missing-features").threshold_met
