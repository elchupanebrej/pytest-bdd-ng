"""Provide entrypoint helpers."""

from pytest_bdd.compatibility.pytest import Config

from .plugin import ScenarioReporterPlugin


def pytest_configure(config: Config) -> None:
    """Handle configure."""
    config.pluginmanager.register(ScenarioReporterPlugin())
