"""

E2E tests for 02 Feature: 01 Non-strict gherkin.
"""

import pytest

from pytest_bdd import scenarios

pytestmark = [pytest.mark.e2e]

test = scenarios("02 Feature/01 Non-strict gherkin.feature.md")
