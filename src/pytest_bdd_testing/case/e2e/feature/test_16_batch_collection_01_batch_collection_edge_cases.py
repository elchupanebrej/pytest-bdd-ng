"""

E2E tests for 16 Batch Collection: 01 Batch collection edge cases.
"""

import pytest

from pytest_bdd import scenarios

pytestmark = [pytest.mark.e2e]

test = scenarios("16 Batch Collection/01 Batch collection edge cases.feature.md")
