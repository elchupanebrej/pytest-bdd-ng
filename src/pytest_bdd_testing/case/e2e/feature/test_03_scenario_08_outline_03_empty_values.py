"""

E2E tests for 03 Scenario: 08 Outline/03 Empty values.
"""

import pytest

from pytest_bdd import scenarios

pytestmark = [pytest.mark.e2e]

test = scenarios("03 Scenario/08 Outline/03 Empty values.feature.md")
