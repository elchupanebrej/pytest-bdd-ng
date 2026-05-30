"""E2E tests for 07 Report: 09 Cucumber formatter reports."""

import pytest

from pytest_bdd import scenarios

from ._bdd_filter import exclude_default_bdd_features

pytestmark = [pytest.mark.e2e]

test = scenarios("07 Report/09 Cucumber formatter reports.feature.md", filter_=exclude_default_bdd_features)
