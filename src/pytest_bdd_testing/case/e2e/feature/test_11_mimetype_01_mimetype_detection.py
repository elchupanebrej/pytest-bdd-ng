"""

E2E tests for 11 Mimetype: 01 Mimetype detection.
"""

import pytest

from pytest_bdd import scenarios

pytestmark = [pytest.mark.e2e]

test = scenarios("11 Mimetype/01 Mimetype detection.feature.md")
