from pathlib import Path

from pytest_bdd.compatibility.matrix import extract_factors_from_tox_ini


def test_existing_py39_pytest60_factor_still_present():
    py_factors, pytest_factors = extract_factors_from_tox_ini(Path("tox.ini"))

    assert "39" in py_factors
    assert "60" in pytest_factors
