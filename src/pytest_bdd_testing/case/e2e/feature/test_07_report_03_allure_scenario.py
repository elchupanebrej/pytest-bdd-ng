"""

E2E tests for 07 Report: 03 Allure scenario.
"""

import pytest

from pytest_bdd import scenarios

pytestmark = [pytest.mark.e2e]

test = scenarios("07 Report/03 Allure scenario.feature.md")
