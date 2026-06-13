"""

E2E tests for 03 Scenario: 06 Scenarios loader.
"""

import pytest

from pytest_bdd import scenarios

pytestmark = [pytest.mark.e2e]

test = scenarios("03 Scenario/06 Scenarios loader.feature.md")
