"""E2E tests for 07 Report: 01 Gherkin terminal reporter."""

import pytest

from pytest_bdd import scenarios

from ._bdd_filter import exclude_default_bdd_features

pytestmark = [pytest.mark.e2e]

test = scenarios("07 Report/01 Gherkin terminal reporter.feature.md", filter_=exclude_default_bdd_features)
