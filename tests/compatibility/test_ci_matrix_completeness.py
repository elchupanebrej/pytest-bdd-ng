"""Provide test ci matrix completeness helpers."""

from pathlib import Path

from pytest_bdd.compatibility.matrix import build_matrix, extract_factors_from_tox_ini


def test_each_compatible_pair_has_tox_env_name():
    """Verify each compatible pair has tox env name."""
    py_factors, pytest_factors = extract_factors_from_tox_ini(Path("tox.ini"))
    entries = build_matrix(py_factors, pytest_factors)

    compatible_entries = [entry for entry in entries if entry.is_compatible]
    assert compatible_entries
    assert all(entry.tox_env_name for entry in compatible_entries)
