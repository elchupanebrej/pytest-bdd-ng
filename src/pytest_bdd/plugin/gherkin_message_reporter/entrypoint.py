import pytest

from pytest_bdd.compatibility.pytest import Config, Parser, PytestPluginManager

from .plugin import GherkinMessageReporter


def pytest_addhooks(pluginmanager: PytestPluginManager) -> None:
    """Register plugin hooks."""
    from .hook import GherkinMessageReporterHookSpec

    pluginmanager.add_hookspecs(GherkinMessageReporterHookSpec)


def pytest_addoption(parser: Parser) -> None:
    """Add pytest-bdd options."""
    group = parser.getgroup("bdd", "Cucumber NDJSON")
    group.addoption(
        "--messagesndjson",
        "--messages-ndjson",
        "--messagesjsonl",
        "--messages-jsonl",
        action="store",
        dest="messages_ndjson_path",
        metavar="path",
        default=None,
        help="messages ndjson report file at given path.",
    )
    group = parser.getgroup("bdd", "Cucumber HTML")
    group.addoption(
        "--cucumber-html",
        "--cucumberhtml",
        action="store",
        dest="cucumber_html_path",
        metavar="path",
        default=None,
        help="cucumber html report at given path.",
    )
    group.addoption(
        "--messages-coverage",
        action="store_true",
        dest="messages_coverage",
        default=False,
        help="Enable dynamic traceability and exhaustive schema validation for message payloads.",
    )


@pytest.hookimpl(trylast=True)
def pytest_configure(config: Config) -> None:
    config.pluginmanager.register(GherkinMessageReporter(config=config), name=GherkinMessageReporter.plugin_name)  # type: ignore[call-arg]


@pytest.hookimpl(tryfirst=True)
def pytest_unconfigure(config: Config) -> None:
    config.pluginmanager.unregister(name=GherkinMessageReporter.plugin_name)
