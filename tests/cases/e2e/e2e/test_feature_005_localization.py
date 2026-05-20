"""E2E tests for 02 Feature: 04 Localization."""

import pytest

from pytest_bdd import scenarios

from ._bdd_filter import exclude_default_bdd_features

pytestmark = [pytest.mark.e2e]

test = scenarios("02 Feature/04 Localization.feature.md", filter_=exclude_default_bdd_features)
