"""

E2E tests for 07 Report: 07 xdist HTML reporting.
"""

import pytest

from pytest_bdd import scenarios

pytestmark = [pytest.mark.e2e]

test = scenarios("07 Report/07 xdist HTML reporting.feature.md")
