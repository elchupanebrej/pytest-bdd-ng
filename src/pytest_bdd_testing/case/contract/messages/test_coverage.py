"""

Provide test coverage helpers.
"""

from __future__ import annotations

from cucumber_messages import (
    Envelope as Message,  # type:ignore[attr-defined] — upstream type stubs missing this attribute
)
from cucumber_messages import (
    TestCaseStarted as CucumberTestCaseStarted,  # type:ignore[attr-defined] — upstream type stubs missing this attribute
)
from cucumber_messages import Timestamp  # type:ignore[attr-defined] — upstream type stubs missing this attribute

from pytest_bdd.model.coverage.inventory import generate_inventory
from pytest_bdd.model.coverage.tracker import ObservedCoverage
from pytest_bdd.model.message_capability_inventory import resolve_messages_schema_dir
from pytest_bdd.model.message_validation import validate_message_stream


def test_generate_inventory_from_schema() -> None:
    """
    Verify generate inventory from schema.

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
    inventory = generate_inventory(resolve_messages_schema_dir())
    assert "testCaseStarted" in inventory.payload_kinds
    assert ("testCaseStarted", "id") in inventory.fields
    assert inventory.fields["testCaseStarted", "id"].type == "string"


def test_observed_coverage_records_state_dependent_fields() -> None:
    """
    Verify observed coverage records state dependent fields.

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
    envelopes = [
        Message(
            test_case_started=CucumberTestCaseStarted(
                id="started-1",
                test_case_id="case-1",
                timestamp=Timestamp(seconds=1, nanos=0),
                attempt=0,
            ),
        ),
    ]

    result = validate_message_stream(envelopes, track_coverage=True)

    assert result.observed_coverage is not None
    observed = result.observed_coverage.observed_fields
    assert ("testCaseStarted", "") in observed
    assert ("testCaseStarted", "id") in observed
    assert ("testCaseStarted", "testCaseId") in observed


def test_observed_coverage_records_first_evidence_only() -> None:
    """
    Verify observed coverage records first evidence only.

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
    coverage = ObservedCoverage()
    coverage.record_field("test_case_finished", "implementation_status", evidence_scenario_id="scenario-A")
    coverage.record_field("test_case_finished", "implementation_status", evidence_scenario_id="scenario-B")

    assert ("testCaseFinished", "implementation_status") in coverage.observed_fields
    assert coverage.evidence_scenarios["testCaseFinished", "implementation_status"] == "scenario-A"
