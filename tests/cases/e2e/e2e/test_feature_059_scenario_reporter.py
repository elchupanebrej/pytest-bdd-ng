"""E2E tests for 14 Scenario Reporter: 01 Scenario reporting."""

import pytest

from pytest_bdd import scenarios

from ._bdd_filter import exclude_default_bdd_features

pytestmark = [pytest.mark.e2e]

test = scenarios("14 Scenario Reporter/01 Scenario reporting.feature.md", filter_=exclude_default_bdd_features)
