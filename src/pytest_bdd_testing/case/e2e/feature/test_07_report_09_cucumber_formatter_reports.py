"""

E2E tests for 07 Report: 09 Cucumber formatter reports.
"""

import pytest

from pytest_bdd import scenarios

pytestmark = [pytest.mark.e2e]

test = scenarios("07 Report/09 Cucumber formatter reports.feature.md")
