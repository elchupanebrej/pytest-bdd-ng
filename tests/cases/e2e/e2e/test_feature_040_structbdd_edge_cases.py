"""E2E tests for 06 StructBDD: 02 StructBDD edge cases."""

import pytest

from pytest_bdd import scenarios

from ._bdd_filter import exclude_default_bdd_features

pytestmark = [pytest.mark.e2e]

test = scenarios("06 StructBDD/02 StructBDD edge cases.feature.md", filter_=exclude_default_bdd_features)
