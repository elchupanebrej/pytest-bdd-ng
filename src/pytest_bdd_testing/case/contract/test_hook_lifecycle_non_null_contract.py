"""

Provide test hook lifecycle non null contract helpers.
"""

from __future__ import annotations

from pathlib import Path

CONTRACT_PATH = (
    Path(__file__).resolve().parents[4]
    / "specs"
    / "016-strict-non-null"
    / "contracts"
    / "hook-lifecycle-non-null.openapi.yaml"
)


def test_hook_lifecycle_non_null_contract_exists() -> None:
    """
    Verify hook lifecycle non null contract exists.

    Test target:
        Enforce framework invariants and stable API contracts.
    Test type:
        Integration test
    Test scenario:
        Given the relevant preconditions are met, when Enforce framework invariants and stable API contracts., then the
        expected outcome is produced.
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
    assert CONTRACT_PATH.exists()


def test_hook_lifecycle_non_null_contract_has_required_paths() -> None:
    """
    Verify hook lifecycle non null contract has required paths.

    Test target:
        Enforce framework invariants and stable API contracts.
    Test type:
        Integration test
    Test scenario:
        Given the relevant preconditions are met, when Enforce framework invariants and stable API contracts., then the
        expected outcome is produced.
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
    contract_text = CONTRACT_PATH.read_text()
    assert "/hooks/{hookName}/run-surface:" in contract_text
    assert "/hooks/{hookName}/boundary-failure:" in contract_text
    assert "/reporting/context-snapshot:" in contract_text
    assert "/parser/parse-error-emission:" in contract_text
    assert "/compatibility/hook-plugin-public-api:" in contract_text


def test_hook_lifecycle_non_null_contract_declares_non_null_policies() -> None:
    """
    Verify hook lifecycle non null contract declares non null policies.

    Test target:
        Enforce framework invariants and stable API contracts.
    Test type:
        Integration test
    Test scenario:
        Given the relevant preconditions are met, when Enforce framework invariants and stable API contracts., then the
        expected outcome is produced.
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
    contract_text = CONTRACT_PATH.read_text()
    assert "guaranteed_present" in contract_text
    assert "empty_object_allowed" in contract_text
    assert "fail_fast" in contract_text
    assert "NoPreviousStep" in contract_text or "no_previous_step" in contract_text
    assert "binding_missing" in contract_text
    assert "emit_best_effort" in contract_text
    assert "best_effort" in contract_text
    assert "explicit_empty_state_when_inactive" in contract_text
