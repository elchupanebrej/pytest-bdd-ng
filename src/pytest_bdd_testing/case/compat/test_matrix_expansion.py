"""

Provide test matrix expansion helpers.
"""

from pytest_bdd.util.matrix import build_matrix, expand_tox_env_names


def test_expand_tox_env_names_returns_compatible_entries_only():
    """
    Verify expand tox env names returns compatible entries only.

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
    entries = build_matrix(["313", "314"], ["83", "90"])
    envs = expand_tox_env_names(entries)

    assert "py313-pytest83-coverage-lin" in envs
    assert "py314-pytest90-coverage-lin" in envs
    assert "py314-pytest83-coverage-lin" not in envs
