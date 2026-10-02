"""Load shared public E2E steps for autoloaded product feature files."""

from importlib.util import find_spec

pytest_plugins = ["pytester", "tests.e2e.steps"]
if find_spec("pytest_httpserver") is not None:
    pytest_plugins.append("pytest_httpserver.pytest_plugin")
