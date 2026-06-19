"""E2E tests for CCK Allure compatibility."""

import pytest

from pytest_bdd import scenarios
from pytest_bdd_testing.step.steps_cck_allure import *  # noqa: F403

pytestmark = [pytest.mark.e2e]

test = scenarios("12 Formatters/08 CCK Allure compatibility.feature.md")
