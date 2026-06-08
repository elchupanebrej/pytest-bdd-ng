"""E2E tests for 12 Formatters: 01 JUnit XML reporter."""

import pytest

from pytest_bdd import scenarios

from ._bdd_filter import exclude_default_bdd_features

pytestmark = [pytest.mark.e2e]

test = scenarios("12 Formatters/01 JUnit XML reporter.feature.md", filter_=exclude_default_bdd_features)
