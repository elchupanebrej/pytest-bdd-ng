"""

Provide test execution message adapter roundtrip helpers.
"""

from __future__ import annotations

from cucumber_messages import (
    Envelope as Message,  # type:ignore[attr-defined, import-untyped] — upstream library missing type stubs
)
from cucumber_messages import TestCase as CucumberTestCase
from cucumber_messages import TestStep as CucumberTestStep

from pytest_bdd.model.execution_message_adapter import ExecutionMessageAdapter
from pytest_bdd.model.message_converter import envelope_to_dict
from pytest_bdd.model.message_registry import EnvelopeRegistry


def test_execution_message_adapter_roundtrip_preserves_test_case_links() -> None:
    """
    Verify execution message adapter roundtrip preserves test case links.

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
    envelope = Message(
        test_case=CucumberTestCase(
            id="test-case-1",
            pickle_id="pickle-1",
            test_steps=[
                CucumberTestStep(id="test-step-1", pickle_step_id="pickle-step-1"),
                CucumberTestStep(id="test-step-2", pickle_step_id="pickle-step-2"),
            ],
        ),
    )
    registry = EnvelopeRegistry()
    registry.add_envelope(envelope)

    serialized = ExecutionMessageAdapter.serialize(envelope)
    projection = ExecutionMessageAdapter.deserialize_dict(envelope_to_dict(serialized), registry=registry)

    assert projection.payload_kind == "test_case"
    assert projection.payload.id == "test-case-1"
    assert projection.resolve("test-case-1") is registry.envelopes[0].test_case
    assert projection.resolve("test-step-1") is registry.envelopes[0].test_case.test_steps[0]
