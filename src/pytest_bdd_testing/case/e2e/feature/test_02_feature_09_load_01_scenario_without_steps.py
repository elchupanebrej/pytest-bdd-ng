"""

E2E tests for 02 Feature: 09 Load/01 Scenario without steps.
"""

import pytest

from pytest_bdd import scenarios

pytestmark = [pytest.mark.e2e]

test = scenarios("02 Feature/09 Load/01 Scenario without steps.feature.md")
