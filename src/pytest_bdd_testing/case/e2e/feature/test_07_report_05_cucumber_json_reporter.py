"""

E2E tests for 07 Report: 05 Cucumber JSON reporter.
"""

import pytest

from pytest_bdd import scenarios

pytestmark = [pytest.mark.e2e]

test = scenarios("07 Report/05 Cucumber JSON reporter.feature.md")
