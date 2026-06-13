"""

E2E tests for 12 Formatters: 05 Usage statistics.
"""

import pytest

from pytest_bdd import scenarios

pytestmark = [pytest.mark.e2e]

test = scenarios("12 Formatters/05 Usage statistics.feature.md")
