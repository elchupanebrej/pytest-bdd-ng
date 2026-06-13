"""

E2E tests for 06 StructBDD: 01 Steps.
"""

import pytest

from pytest_bdd import scenarios

pytestmark = [pytest.mark.e2e]

test = scenarios("06 StructBDD/01 Steps.feature.md")
