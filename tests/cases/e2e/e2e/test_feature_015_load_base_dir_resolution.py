"""E2E tests for 02 Feature: 09 Load/06 Feature base directory resolution."""

import pytest

from pytest_bdd import scenarios

from ._bdd_filter import exclude_default_bdd_features

pytestmark = [pytest.mark.e2e]

test = scenarios(
    "02 Feature/09 Load/06 Feature base directory resolution.feature.md",
    filter_=exclude_default_bdd_features,
)
