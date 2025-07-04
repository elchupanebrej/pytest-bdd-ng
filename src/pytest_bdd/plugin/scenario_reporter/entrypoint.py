from pytest_bdd.compatibility.pytest import Config

from .plugin import ScenarioReporter


def pytest_configure(config: Config) -> None:
    config.pluginmanager.register(ScenarioReporter())
