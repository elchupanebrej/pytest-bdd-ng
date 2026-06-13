"""

E2E tests for 04 Step: 01 Doc string.
"""

import pytest

from pytest_bdd import scenarios

pytestmark = [pytest.mark.e2e]

test = scenarios("04 Step/01 Doc string.feature.md")
