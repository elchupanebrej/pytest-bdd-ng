import pytest

from pytest_bdd import scenarios
from pytest_bdd.compatibility.allure import ALLURE_INSTALLED

pytestmark = [
    pytest.mark.skipif(not ALLURE_INSTALLED, reason="Allure is not installed"),
]

test = scenarios("../testdata/allure_/outline.feature", "Scenario outline")
