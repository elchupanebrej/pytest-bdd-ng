"""E2E tests for 09 Tag Expressions: 01 Tag expression evaluation."""

import pytest

from pytest_bdd import scenarios

from ._bdd_filter import exclude_default_bdd_features

pytestmark = [pytest.mark.e2e]

test = scenarios("09 Tag Expressions/01 Tag expression evaluation.feature.md", filter_=exclude_default_bdd_features)
