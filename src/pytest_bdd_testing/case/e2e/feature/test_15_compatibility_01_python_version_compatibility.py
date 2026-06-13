"""

E2E tests for 15 Compatibility: 01 Python version compatibility.
"""

import pytest

from pytest_bdd import scenarios

pytestmark = [pytest.mark.e2e]

test = scenarios("15 Compatibility/01 Python version compatibility.feature.md")
