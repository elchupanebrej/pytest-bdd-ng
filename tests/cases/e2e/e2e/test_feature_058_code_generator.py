"""E2E tests for 13 Code Generator: 01 Code generation."""

import pytest

from pytest_bdd import scenarios

from ._bdd_filter import exclude_default_bdd_features

pytestmark = [pytest.mark.e2e]

test = scenarios("13 Code Generator/01 Code generation.feature.md", filter_=exclude_default_bdd_features)
