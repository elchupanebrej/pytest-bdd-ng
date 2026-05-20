"""E2E tests for 12 Formatters: 02 Progress formatters."""

import pytest

from pytest_bdd import scenarios

from ._bdd_filter import exclude_default_bdd_features

pytestmark = [pytest.mark.e2e]

test = scenarios("12 Formatters/02 Progress formatters.feature.md", filter_=exclude_default_bdd_features)
