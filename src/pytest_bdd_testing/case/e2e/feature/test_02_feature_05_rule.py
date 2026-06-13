"""

E2E tests for 02 Feature: 05 Rule.
"""

import pytest

from pytest_bdd import scenarios

pytestmark = [pytest.mark.e2e]

test = scenarios("02 Feature/05 Rule.feature.md")
