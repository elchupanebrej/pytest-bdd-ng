from pytest import mark

from pytest_cuke import scenario
from pytest_cuke.compatibility.allure import ALLURE_INSTALLED
from pytest_cuke.compatibility.pytest import PYTEST81

pytestmark = mark.integration


@scenario("testdata/allure_/outline.feature", "Scenario outline")
@mark.skipif(not ALLURE_INSTALLED, reason="Allure is not installed")
@mark.skipif(PYTEST81, reason="Allure uses deprecated APIs")
def test_scenario_outline():
    pass
