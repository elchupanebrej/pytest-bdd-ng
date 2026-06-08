"""E2E tests for 08 Go Parser: 01 Go parser backend."""

import pytest

from pytest_bdd import scenarios

from ._bdd_filter import exclude_default_bdd_features

pytestmark = [pytest.mark.e2e]

test = scenarios("08 Go Parser/01 Go parser backend.feature.md", filter_=exclude_default_bdd_features)
