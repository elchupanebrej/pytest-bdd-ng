"""E2E tests for Allure Formatter."""

import pytest

from pytest_bdd import scenarios
from pytest_bdd_testing.step.steps_allure_formatter import *  # noqa: F403

pytestmark = [pytest.mark.e2e]

test = scenarios("12 Formatters/06 Allure formatter.feature.md")
