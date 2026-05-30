"""E2E tests for 01 Tutorial: 01 Launch."""

import pytest

from pytest_bdd import scenarios

from ._bdd_filter import exclude_default_bdd_features

pytestmark = [pytest.mark.e2e]

test = scenarios("01 Tutorial/01 Launch.feature.md", filter_=exclude_default_bdd_features)
