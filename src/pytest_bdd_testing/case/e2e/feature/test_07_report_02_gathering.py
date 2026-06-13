"""

E2E tests for 07 Report: 02 Gathering.
"""

import pytest

from pytest_bdd import scenarios

pytestmark = [pytest.mark.e2e]

test = scenarios("07 Report/02 Gathering.feature.md")
