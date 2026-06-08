"""E2E tests for 07 Report: 05 Cucumber JSON reporter."""

import pytest

from pytest_bdd import scenarios

from ._bdd_filter import exclude_default_bdd_features

pytestmark = [pytest.mark.e2e]

test = scenarios("07 Report/05 Cucumber JSON reporter.feature.md", filter_=exclude_default_bdd_features)
