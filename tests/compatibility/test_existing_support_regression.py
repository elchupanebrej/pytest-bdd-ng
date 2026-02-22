from pathlib import Path

from pytest_bdd.compatibility.matrix import extract_factors_from_tox_ini


def test_eol_py39_and_pre625_pytest_factors_are_removed():
    py_factors, pytest_factors = extract_factors_from_tox_ini(Path("tox.ini"))

    assert "39" not in py_factors
    assert "60" not in pytest_factors
    assert "61" not in pytest_factors
    assert "62" not in pytest_factors
    assert "310" in py_factors
    assert "625" in pytest_factors
