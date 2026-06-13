"""

E2E tests for 05 Step definition: 01 Pytest fixtures substitution.
"""

import pytest

from pytest_bdd import scenarios

pytestmark = [pytest.mark.e2e]

test = scenarios("05 Step definition/01 Pytest fixtures substitution.feature.md")
