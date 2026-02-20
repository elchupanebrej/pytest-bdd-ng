from pytest_bdd.compatibility.matrix import (
    REASON_COMPATIBLE,
    REASON_PYTEST_UNAVAILABLE,
    REASON_PYTHON_NOT_SUPPORTED_BY_PYTEST,
    is_pair_compatible,
)


def test_py314_pytest90_is_compatible():
    compatible, reason = is_pair_compatible("314", "90")
    assert compatible is True
    assert reason == REASON_COMPATIBLE


def test_py314_pytest83_is_not_compatible():
    compatible, reason = is_pair_compatible("314", "83")
    assert compatible is False
    assert reason == REASON_PYTHON_NOT_SUPPORTED_BY_PYTEST


def test_unknown_pytest_factor_is_unavailable():
    compatible, reason = is_pair_compatible("313", "999")
    assert compatible is False
    assert reason == REASON_PYTEST_UNAVAILABLE
