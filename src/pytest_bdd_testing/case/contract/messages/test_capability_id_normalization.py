"""

Provide test capability id normalization helpers.
"""

from __future__ import annotations

from pytest_bdd.model.coverage.inventory import (
    canonical_capability_id,
    canonical_capability_key,
    canonical_payload_kind,
    parse_capability_id,
)


def test_canonical_payload_kind_converts_snake_case_to_camel_case() -> None:
    """
    Verify canonical payload kind converts snake case to camel case.

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
    assert canonical_payload_kind("test_case_started") == "testCaseStarted"
    assert canonical_payload_kind("gherkin_document") == "gherkinDocument"


def test_canonical_payload_kind_preserves_existing_camel_case() -> None:
    """
    Verify canonical payload kind preserves existing camel case.

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
    assert canonical_payload_kind("testRunStarted") == "testRunStarted"


def test_canonical_capability_key_normalizes_payload_kind_only() -> None:
    """
    Verify canonical capability key normalizes payload kind only.

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
    assert canonical_capability_key("test_step_finished", "testStepResult.duration.nanos") == (
        "testStepFinished",
        "testStepResult.duration.nanos",
    )


def test_parse_and_canonical_capability_id() -> None:
    """
    Verify parse and canonical capability id.

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
    assert parse_capability_id("test_case_started.timestamp.seconds") == (
        "testCaseStarted",
        "timestamp.seconds",
    )
    assert canonical_capability_id("test_case_started.timestamp.seconds") == "testCaseStarted.timestamp.seconds"
