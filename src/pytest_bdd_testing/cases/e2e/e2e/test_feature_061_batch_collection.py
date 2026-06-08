"""E2E tests for 16 Batch Collection: 01 Batch collection edge cases."""

import pytest

from pytest_bdd import scenarios

from ._bdd_filter import exclude_default_bdd_features

pytestmark = [pytest.mark.e2e]

test = scenarios("16 Batch Collection/01 Batch collection edge cases.feature.md", filter_=exclude_default_bdd_features)
