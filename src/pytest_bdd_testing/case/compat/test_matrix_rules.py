"""

Provide test matrix rules helpers.
"""

from pytest_bdd.compatibility.runtime_compat import (
    REASON_COMPATIBLE,
    REASON_EOL_PYTEST,
    REASON_EOL_PYTHON,
    REASON_PYTEST_UNAVAILABLE,
    REASON_PYTHON_NOT_SUPPORTED_BY_PYTEST,
    is_pair_compatible,
)


def test_py314_pytest90_is_compatible():
    """
    Verify py314 pytest90 is compatible.

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
    compatible, reason = is_pair_compatible("314", "90")
    assert compatible is True
    assert reason == REASON_COMPATIBLE


def test_py314_pytest83_is_not_compatible():
    """
    Verify py314 pytest83 is not compatible.

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
    compatible, reason = is_pair_compatible("314", "83")
    assert compatible is False
    assert reason == REASON_PYTHON_NOT_SUPPORTED_BY_PYTEST


def test_unknown_pytest_factor_is_unavailable():
    """
    Verify unknown pytest factor is unavailable.

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
    compatible, reason = is_pair_compatible("313", "999")
    assert compatible is False
    assert reason == REASON_PYTEST_UNAVAILABLE


def test_eol_pytest60_factor_is_unavailable():
    """
    Verify eol pytest60 factor is unavailable.

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
    compatible, reason = is_pair_compatible("310", "60")
    assert compatible is False
    assert reason == REASON_EOL_PYTEST


def test_eol_python39_factor_is_unsupported():
    """
    Verify eol python39 factor is unsupported.

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
    compatible, reason = is_pair_compatible("39", "90")
    assert compatible is False
    assert reason == REASON_EOL_PYTHON
