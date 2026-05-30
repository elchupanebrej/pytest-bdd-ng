"""E2E tests for 16 Batch Collection: 02 Edge cases with large files."""

import pytest

from pytest_bdd import scenarios

from ._bdd_filter import exclude_default_bdd_features

pytestmark = [pytest.mark.e2e]

test = scenarios("16 Batch Collection/02 Edge cases with large files.feature.md", filter_=exclude_default_bdd_features)
