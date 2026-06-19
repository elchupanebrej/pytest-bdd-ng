"""

E2E tests for 07 Report: 03 Allure scenario.
"""

import pytest

from pytest_bdd import scenarios
from pytest_bdd_testing.step.steps_allure_formatter import *  # noqa: F403

pytestmark = [pytest.mark.e2e]

test = scenarios("07 Report/03 Allure scenario.feature.md")
