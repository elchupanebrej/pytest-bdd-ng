import pytest

from pytest_bdd import scenarios
from pytest_bdd.compatibility.allure import ALLURE_INSTALLED
from pytest_bdd.compatibility.pytest import PYTEST81

pytestmark = [
    pytest.mark.skipif(not ALLURE_INSTALLED, reason="Allure is not installed"),
    pytest.mark.skipif(PYTEST81, reason="Allure uses deprecated APIs"),
]

test = scenarios("../testdata/allure_/outline.feature", "Scenario outline")
