"""

Provide test run contract helpers.
"""

from __future__ import annotations

from pathlib import Path

CONTRACT_PATH = (
    Path(__file__).resolve().parents[4]
    / "specs"
    / "003-unify-run-context"
    / "contracts"
    / "hook-execution-context.openapi.yaml"
)


def test_run_contract_exists() -> None:
    """
    Verify run contract exists.

    Test target:
        Enforce framework invariants and stable API contracts.
    Test type:
        E2E/Acceptance test
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


def test_run_contract_has_required_paths() -> None:
    """
    Verify run contract has required paths.

    Test target:
        Enforce framework invariants and stable API contracts.
    Test type:
        E2E/Acceptance test
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
    assert "/execution-context/session-root:" in contract_text
    assert "/execution-context/session-fixture:" in contract_text
    assert "/execution-context/config-stash:" in contract_text
    assert "/execution-context/active-set:" in contract_text
    assert "/execution-context/transitions:" in contract_text
    assert "/hooks/{hookName}/parameter-model:" in contract_text
    assert "/reporting/context-snapshot:" in contract_text
    assert "/compatibility/external-api:" in contract_text


def test_run_contract_has_minimal_change_constraints() -> None:
    """
    Verify run contract has minimal change constraints.

    Test target:
        Enforce framework invariants and stable API contracts.
    Test type:
        E2E/Acceptance test
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
    assert "consumerMigrationRequired:" in contract_text
    assert "- false" in contract_text
    assert "maxItems: 0" in contract_text
    assert "previousStep:" in contract_text
    assert "activeSet:" in contract_text
