"""E2E tests for 03 Scenario: 02 Tag."""

import pytest

from pytest_bdd import scenarios

from ._bdd_filter import exclude_default_bdd_features

pytestmark = [pytest.mark.e2e]

test = scenarios("03 Scenario/02 Tag.feature.md", filter_=exclude_default_bdd_features)
