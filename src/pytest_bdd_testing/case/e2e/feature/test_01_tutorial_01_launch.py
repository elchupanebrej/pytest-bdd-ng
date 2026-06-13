"""

E2E tests for 01 Tutorial: 01 Launch.
"""

import pytest

from pytest_bdd import scenarios

pytestmark = [pytest.mark.e2e]

test = scenarios("01 Tutorial/01 Launch.feature.md")
