"""

E2E tests for 03 Scenario: 07 Background.
"""

import pytest

from pytest_bdd import scenarios

pytestmark = [pytest.mark.e2e]

test = scenarios("03 Scenario/07 Background.feature.md")
