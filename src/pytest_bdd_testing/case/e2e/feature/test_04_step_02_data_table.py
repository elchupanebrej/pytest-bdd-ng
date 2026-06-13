"""

E2E tests for 04 Step: 02 Data table.
"""

import pytest

from pytest_bdd import scenarios

pytestmark = [pytest.mark.e2e]

test = scenarios("04 Step/02 Data table.feature.md")
