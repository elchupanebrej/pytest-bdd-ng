"""

E2E tests for 03 Scenario: 02 Tag.
"""

import pytest

from pytest_bdd import scenarios

pytestmark = [pytest.mark.e2e]

test = scenarios("03 Scenario/02 Tag.feature.md")
