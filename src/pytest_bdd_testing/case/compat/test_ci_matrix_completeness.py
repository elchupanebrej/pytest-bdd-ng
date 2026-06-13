"""

Provide test ci matrix completeness helpers.
"""

from pathlib import Path

from pytest_bdd.util.matrix import build_matrix, extract_factors_from_tox_ini


def test_each_compatible_pair_has_tox_env_name():
    """
    Verify each compatible pair has tox env name.

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
    py_factors, pytest_factors = extract_factors_from_tox_ini(Path("tox.ini"))
    entries = build_matrix(py_factors, pytest_factors)

    compatible_entries = [entry for entry in entries if entry.is_compatible]
    assert compatible_entries
    assert all(entry.tox_env_name for entry in compatible_entries)
