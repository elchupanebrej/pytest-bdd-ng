"""E2E tests for Allure Formatter."""

import pytest

from pytest_bdd import scenarios

pytestmark = [pytest.mark.e2e]

test = scenarios("12 Formatters/06 Allure formatter.feature.md")
