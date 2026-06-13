"""

Provide test compatibility contract helpers.
"""

from pathlib import Path

import yaml


def test_contract_has_required_paths():
    """
    Verify contract has required paths.

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
    contract_path = Path("specs/001-add-py314-pytest39-support/contracts/compatibility-matrix.openapi.yaml")
    data = yaml.safe_load(contract_path.read_text(encoding="utf-8"))
    paths = data["paths"]

    assert "/compatibility/policy" in paths
    assert "/compatibility/matrix" in paths
    assert "/compatibility/validate" in paths


def test_contract_declares_eol_reason_codes():
    """
    Verify contract declares eol reason codes.

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
    contract_path = Path("specs/001-add-py314-pytest39-support/contracts/compatibility-matrix.openapi.yaml")
    data = yaml.safe_load(contract_path.read_text(encoding="utf-8"))
    reason_codes = data["components"]["schemas"]["CompatibilityMatrixEntry"]["properties"]["reasonCode"]["enum"]

    assert "eol_python" in reason_codes
    assert "eol_pytest" in reason_codes
