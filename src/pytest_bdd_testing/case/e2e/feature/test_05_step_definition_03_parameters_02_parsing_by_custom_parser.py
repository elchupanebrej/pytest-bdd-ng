"""

E2E tests for 05 Step definition: 03 Parameters/02 Parsing by custom parser.
"""

import pytest

from pytest_bdd import scenarios

pytestmark = [pytest.mark.e2e]

test = scenarios("05 Step definition/03 Parameters/02 Parsing by custom parser.feature.md")
