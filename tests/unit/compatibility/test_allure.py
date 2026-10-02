from __future__ import annotations

from pytest_cuke.compatibility.allure import ALLURE_INSTALLED


def test_allure_installed_flag() -> None:
    assert isinstance(ALLURE_INSTALLED, bool)
