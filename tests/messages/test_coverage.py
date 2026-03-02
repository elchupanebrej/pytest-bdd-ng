from __future__ import annotations

from cucumber_messages import Envelope as Message  # type:ignore[attr-defined]
from cucumber_messages import TestCaseStarted as CucumberTestCaseStarted  # type:ignore[attr-defined]
from cucumber_messages import Timestamp  # type:ignore[attr-defined]

from pytest_bdd.model.coverage.inventory import generate_inventory
from pytest_bdd.model.coverage.tracker import ObservedCoverage
from pytest_bdd.model.message_capability_inventory import resolve_messages_schema_dir
from pytest_bdd.model.message_validation import validate_message_stream


def test_generate_inventory_from_schema() -> None:
    inventory = generate_inventory(resolve_messages_schema_dir())
    assert "testCaseStarted" in inventory.payload_kinds
    assert ("testCaseStarted", "id") in inventory.fields
    assert inventory.fields["testCaseStarted", "id"].type == "string"


def test_observed_coverage_records_state_dependent_fields() -> None:
    envelopes = [
        Message(
            test_case_started=CucumberTestCaseStarted(
                id="started-1",
                test_case_id="case-1",
                timestamp=Timestamp(seconds=1, nanos=0),
                attempt=0,
            )
        )
    ]

    result = validate_message_stream(envelopes, track_coverage=True)

    assert result.observed_coverage is not None
    observed = result.observed_coverage.observed_fields
    assert ("test_case_started", "") in observed
    assert ("test_case_started", "id") in observed
    assert ("test_case_started", "testCaseId") in observed


def test_observed_coverage_records_first_evidence_only() -> None:
    coverage = ObservedCoverage()
    coverage.record_field("test_case_finished", "implementation_status", evidence_scenario_id="scenario-A")
    coverage.record_field("test_case_finished", "implementation_status", evidence_scenario_id="scenario-B")

    assert ("test_case_finished", "implementation_status") in coverage.observed_fields
    assert coverage.evidence_scenarios["test_case_finished", "implementation_status"] == "scenario-A"
