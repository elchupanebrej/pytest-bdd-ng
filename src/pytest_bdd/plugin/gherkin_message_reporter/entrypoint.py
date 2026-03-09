import os

import pytest

from pytest_bdd.compatibility.pytest import Config, Parser, PytestPluginManager

from .plugin import GherkinMessageReporter

_REPORTING_REMOTE_MODULE_REQUIRED = False


def _reporting_requested(config: Config) -> bool:
    return any(
        [
            getattr(config.option, "messages_ndjson_path", None) is not None,
            getattr(config.option, "cucumber_html_path", None) is not None,
        ]
    )


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


@pytest.hookimpl(trylast=True)
def pytest_configure(config: Config) -> None:
    global _REPORTING_REMOTE_MODULE_REQUIRED
    _REPORTING_REMOTE_MODULE_REQUIRED = _reporting_requested(config)
    config.pluginmanager.register(GherkinMessageReporter(config=config), name=GherkinMessageReporter.plugin_name)  # type: ignore[call-arg]


@pytest.hookimpl(optionalhook=True, tryfirst=True)
def pytest_xdist_getremotemodule():
    if os.environ.get("PYTEST_XDIST_WORKER"):
        return None
    if not _REPORTING_REMOTE_MODULE_REQUIRED:
        import xdist.remote  # type: ignore[import-untyped]

        return xdist.remote
    from . import xdist_remote

    return xdist_remote


@pytest.hookimpl(tryfirst=True)
def pytest_unconfigure(config: Config) -> None:
    global _REPORTING_REMOTE_MODULE_REQUIRED
    _REPORTING_REMOTE_MODULE_REQUIRED = False
    config.pluginmanager.unregister(name=GherkinMessageReporter.plugin_name)
