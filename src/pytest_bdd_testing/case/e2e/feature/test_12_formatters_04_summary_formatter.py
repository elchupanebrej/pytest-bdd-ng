"""

E2E tests for 12 Formatters: 04 Summary formatter.
"""

import pytest

from pytest_bdd import scenarios

pytestmark = [pytest.mark.e2e]

test = scenarios("12 Formatters/04 Summary formatter.feature.md")
