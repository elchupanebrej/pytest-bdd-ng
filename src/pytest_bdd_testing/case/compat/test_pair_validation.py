"""

Provide test pair validation helpers.
"""

import json

from pytest_bdd.script.compatibility_matrix import main


def test_pair_validation_returns_nonzero_for_incompatible_pair(capsys):
    """
    Verify pair validation returns nonzero for incompatible pair.

    Test target:
        Protect API compatibility and version stability across the framework execution matrix.
    Test type:
        E2E/Acceptance test
    Test scenario:
        Given the relevant preconditions are met, when Protect API compatibility and version stability across the
        framework execution matrix., then the expected outcome is produced.
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
    code = main(["--python", "314", "--pytest", "83", "--json"])
    out = capsys.readouterr().out
    payload = json.loads(out)

    assert code == 1
    assert payload["isCompatible"] is False
    assert payload["isSupported"] is False
    assert payload["reasonCode"] == "python_not_supported_by_pytest"


def test_pair_validation_returns_zero_for_compatible_pair(capsys):
    """
    Verify pair validation returns zero for compatible pair.

    Test target:
        Protect API compatibility and version stability across the framework execution matrix.
    Test type:
        E2E/Acceptance test
    Test scenario:
        Given the relevant preconditions are met, when Protect API compatibility and version stability across the
        framework execution matrix., then the expected outcome is produced.
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
    code = main(["--python", "314", "--pytest", "90", "--json"])
    out = capsys.readouterr().out
    payload = json.loads(out)

    assert code == 0
    assert payload["isCompatible"] is True
    assert payload["isSupported"] is True
    assert payload["reasonCode"] == "compatible"


def test_pair_validation_returns_nonzero_for_eol_pair(capsys):
    """
    Verify pair validation returns nonzero for eol pair.

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
    code = main(["--python", "39", "--pytest", "90", "--json"])
    out = capsys.readouterr().out
    payload = json.loads(out)

    assert code == 1
    assert payload["isCompatible"] is False
    assert payload["isSupported"] is False
    assert payload["reasonCode"] == "eol_python"
