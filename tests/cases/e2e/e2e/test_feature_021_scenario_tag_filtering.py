"""E2E tests for 03 Scenario: 04 Tag filtering."""

import pytest

from pytest_bdd import scenarios

from ._bdd_filter import exclude_default_bdd_features

pytestmark = [pytest.mark.e2e]

test = scenarios("03 Scenario/04 Tag filtering.feature.md", filter_=exclude_default_bdd_features)
