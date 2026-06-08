"""E2E tests for 11 Mimetype: 02 Edge cases."""

import pytest

from pytest_bdd import scenarios

from ._bdd_filter import exclude_default_bdd_features

pytestmark = [pytest.mark.e2e]

test = scenarios("11 Mimetype/02 Edge cases.feature.md", filter_=exclude_default_bdd_features)
