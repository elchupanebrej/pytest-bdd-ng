"""E2E tests for 04 Step: 01 Doc string."""

import pytest

from pytest_bdd import scenarios

from ._bdd_filter import exclude_default_bdd_features

pytestmark = [pytest.mark.e2e]

test = scenarios("04 Step/01 Doc string.feature.md", filter_=exclude_default_bdd_features)
