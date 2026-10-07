"""Load shared public E2E steps for autoloaded product feature files."""

from importlib.util import find_spec

pytest_plugins = [
    "pytester",
    "tests.e2e.steps",
    "tests.e2e.runtime_steps",
    "tests.e2e.formatter_steps",
    "tests.e2e.offline_formatter_steps",
    "tests.e2e.live_pretty_formatter_steps",
    "tests.e2e.live_progress_formatter_steps",
    "tests.e2e.live_progress_integration_steps",
    "tests.e2e.environment_inventory_steps",
    "tests.e2e.environment_proof_aggregation_steps",
    "tests.e2e.browser_report_steps",
]
if find_spec("pytest_httpserver") is not None:
    pytest_plugins.append("pytest_httpserver.pytest_plugin")
