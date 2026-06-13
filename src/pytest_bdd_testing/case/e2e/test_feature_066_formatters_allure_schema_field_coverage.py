"""E2E tests for Allure schema field coverage."""

import pytest

from pytest_bdd import scenarios

pytestmark = [pytest.mark.e2e]

test = scenarios("12 Formatters/07 Allure schema field coverage.feature.md")
