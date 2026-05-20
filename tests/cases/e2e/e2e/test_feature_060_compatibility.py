"""E2E tests for 15 Compatibility: 01 Python version compatibility."""

import pytest

from pytest_bdd import scenarios

from ._bdd_filter import exclude_default_bdd_features

pytestmark = [pytest.mark.e2e]

test = scenarios("15 Compatibility/01 Python version compatibility.feature.md", filter_=exclude_default_bdd_features)
