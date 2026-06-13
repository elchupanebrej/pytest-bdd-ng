"""

E2E tests for 07 Report: 04 Allure outline.
"""

import pytest

from pytest_bdd import scenarios

pytestmark = [pytest.mark.e2e]

test = scenarios("07 Report/04 Allure outline.feature.md")
