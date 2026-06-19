"""

E2E tests for 10 Heading Validation: 01 Heading validation.
"""

import pytest

from pytest_bdd import scenarios
from pytest_bdd_testing.step.heading_validation import *  # noqa: F403

pytestmark = [pytest.mark.e2e]

test = scenarios("10 Heading Validation/01 Heading validation.feature.md")
