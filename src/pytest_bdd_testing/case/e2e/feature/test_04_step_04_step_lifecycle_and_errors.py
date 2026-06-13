"""

E2E tests for 04 Step: 04 Step lifecycle and errors.
"""

import pytest

from pytest_bdd import scenarios

pytestmark = [pytest.mark.e2e]

test = scenarios("04 Step/04 Step lifecycle and errors.feature.md")
