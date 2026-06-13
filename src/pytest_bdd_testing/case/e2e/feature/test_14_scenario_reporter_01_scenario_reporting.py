"""

E2E tests for 14 Scenario Reporter: 01 Scenario reporting.
"""

import pytest

from pytest_bdd import scenarios

pytestmark = [pytest.mark.e2e]

test = scenarios("14 Scenario Reporter/01 Scenario reporting.feature.md")
