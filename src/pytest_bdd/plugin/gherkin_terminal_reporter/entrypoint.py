import pytest

from pytest_bdd.compatibility.pytest import Config, Parser, TerminalReporter

from .exception import IncompatiblePluginConfigurationError, IncompatiblePluginError
from .plugin import GherkinTerminalReporter


def pytest_addoption(parser: Parser) -> None:
    group = parser.getgroup("terminal reporting", "reporting", after="general")
    group._addoption(
        "--gherkin-terminal-reporter",
        action="store_true",
        dest="gherkin_terminal_reporter",
        default=False,
        help="enable gherkin output",
    )


@pytest.mark.trylast
def pytest_configure(config: Config) -> None:
    if config.option.gherkin_terminal_reporter:
        # Get the standard terminal reporter plugin and replace it with our
        current_reporter = config.pluginmanager.getplugin("terminalreporter")
        if current_reporter.__class__ != TerminalReporter:
            raise IncompatiblePluginError(current_reporter)
        gherkin_reporter = GherkinTerminalReporter(config)
        config.pluginmanager.unregister(current_reporter)
        config.pluginmanager.register(gherkin_reporter, "terminalreporter")
        if config.pluginmanager.getplugin("dsession"):
            msg = "xdist"
            raise IncompatiblePluginConfigurationError(msg)
