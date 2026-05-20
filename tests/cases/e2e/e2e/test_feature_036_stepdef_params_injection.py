"""E2E tests for 05 Step definition: 03 Parameters/03 Injection as fixtures."""

import pytest

from pytest_bdd import scenarios

from ._bdd_filter import exclude_default_bdd_features

pytestmark = [pytest.mark.e2e]

test = scenarios(
    "05 Step definition/03 Parameters/03 Injection as fixtures.feature.md", filter_=exclude_default_bdd_features
)
