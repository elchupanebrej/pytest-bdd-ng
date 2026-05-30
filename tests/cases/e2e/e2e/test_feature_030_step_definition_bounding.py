"""E2E tests for 04 Step: 03 Step definition bounding."""

import pytest

from pytest_bdd import scenarios

from ._bdd_filter import exclude_default_bdd_features

pytestmark = [pytest.mark.e2e]

test = scenarios("04 Step/03 Step definition bounding.feature.md", filter_=exclude_default_bdd_features)
