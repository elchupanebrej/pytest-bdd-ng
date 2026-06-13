"""

E2E tests for 11 Mimetype: 02 Edge cases.
"""

import pytest

from pytest_bdd import scenarios

pytestmark = [pytest.mark.e2e]

test = scenarios("11 Mimetype/02 Edge cases.feature.md")
