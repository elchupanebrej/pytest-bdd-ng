"""Provide test pair validation helpers."""

import json

from pytest_bdd.script.compatibility_matrix import main


def test_pair_validation_returns_nonzero_for_incompatible_pair(capsys):
    """Verify pair validation returns nonzero for incompatible pair."""
    code = main(["--python", "314", "--pytest", "83", "--json"])
    out = capsys.readouterr().out
    payload = json.loads(out)

    assert code == 1
    assert payload["isCompatible"] is False
    assert payload["isSupported"] is False
    assert payload["reasonCode"] == "python_not_supported_by_pytest"


def test_pair_validation_returns_zero_for_compatible_pair(capsys):
    """Verify pair validation returns zero for compatible pair."""
    code = main(["--python", "314", "--pytest", "90", "--json"])
    out = capsys.readouterr().out
    payload = json.loads(out)

    assert code == 0
    assert payload["isCompatible"] is True
    assert payload["isSupported"] is True
    assert payload["reasonCode"] == "compatible"


def test_pair_validation_returns_nonzero_for_eol_pair(capsys):
    """Verify pair validation returns nonzero for eol pair."""
    code = main(["--python", "39", "--pytest", "90", "--json"])
    out = capsys.readouterr().out
    payload = json.loads(out)

    assert code == 1
    assert payload["isCompatible"] is False
    assert payload["isSupported"] is False
    assert payload["reasonCode"] == "eol_python"
