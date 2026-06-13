"""

E2E tests for 16 Batch Collection: 02 Edge cases with large files.
"""

import pytest

from pytest_bdd import scenarios

pytestmark = [pytest.mark.e2e]

test = scenarios("16 Batch Collection/02 Edge cases with large files.feature.md")
