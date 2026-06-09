"""E2E tests for Allure-Cucumber Converter."""

import pytest

from pytest_bdd import scenarios

pytestmark = [pytest.mark.e2e]

test = scenarios("17 Allure Converter/1 Allure converter.feature.md")
