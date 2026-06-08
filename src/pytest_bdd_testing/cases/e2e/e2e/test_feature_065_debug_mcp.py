"""E2E tests for Debug MCP: 01 Agentic debugging."""

import pytest

from pytest_bdd import scenarios

from ._bdd_filter import exclude_default_bdd_features

pytestmark = [pytest.mark.e2e]
pytest_plugins = ["pytest_bdd_testing.cases.e2e.steps_debug_mcp"]

test = scenarios("17 Debug MCP/01 Agentic debugging.feature.md", filter_=exclude_default_bdd_features)
