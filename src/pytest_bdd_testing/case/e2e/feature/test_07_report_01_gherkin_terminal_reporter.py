"""

E2E tests for 07 Report: 01 Gherkin terminal reporter.
"""

import pytest

from pytest_bdd import scenarios

pytestmark = [pytest.mark.e2e]

test = scenarios("07 Report/01 Gherkin terminal reporter.feature.md")
