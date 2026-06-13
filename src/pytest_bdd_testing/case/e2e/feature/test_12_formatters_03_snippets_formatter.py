"""

E2E tests for 12 Formatters: 03 Snippets formatter.
"""

import pytest

from pytest_bdd import scenarios

pytestmark = [pytest.mark.e2e]

test = scenarios("12 Formatters/03 Snippets formatter.feature.md")
