"""

E2E tests for 02 Feature: 02 Tag conversion.
"""

import pytest

from pytest_bdd import scenarios

pytestmark = [pytest.mark.e2e]

test = scenarios("02 Feature/02 Tag conversion.feature.md")
