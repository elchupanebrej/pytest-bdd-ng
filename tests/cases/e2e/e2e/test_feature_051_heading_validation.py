"""E2E tests for 10 Heading Validation: 01 Heading validation."""

import pytest

from pytest_bdd import scenarios

from ._bdd_filter import exclude_default_bdd_features

pytestmark = [pytest.mark.e2e]

test = scenarios("10 Heading Validation/01 Heading validation.feature.md", filter_=exclude_default_bdd_features)
