"""

E2E tests for 03 Scenario: 01 Scenario binding.
"""

import pytest

from pytest_bdd import scenarios

pytestmark = [pytest.mark.e2e]

test = scenarios("03 Scenario/01 Scenario binding.feature.md")
