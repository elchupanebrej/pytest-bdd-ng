"""

E2E tests for Debug MCP: 01 Agentic debugging.
"""

import pytest

from pytest_bdd import scenarios

pytestmark = [pytest.mark.e2e]
pytest_plugins = ["pytest_bdd_testing.step.debug_mcp"]

test = scenarios("17 Debug MCP/01 Agentic debugging.feature.md")
