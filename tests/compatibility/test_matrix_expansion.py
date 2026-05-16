"""Provide test matrix expansion helpers."""

from pytest_bdd.util.matrix import build_matrix, expand_tox_env_names


def test_expand_tox_env_names_returns_compatible_entries_only():
    """Verify expand tox env names returns compatible entries only."""
    entries = build_matrix(["313", "314"], ["83", "90"])
    envs = expand_tox_env_names(entries)

    assert "py313-pytest83-coverage-lin" in envs
    assert "py314-pytest90-coverage-lin" in envs
    assert "py314-pytest83-coverage-lin" not in envs
