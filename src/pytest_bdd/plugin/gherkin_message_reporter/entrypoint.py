import os
from contextlib import suppress
from pathlib import Path
from typing import Any, ClassVar, TextIO, cast

import pytest
from attrs import frozen

from pytest_bdd.compatibility.pytest import Config, Parser, PytestPluginManager, TerminalReporter
from pytest_bdd.model.stash_access import StashBound
from pytest_bdd.plugin.gherkin_message_reporter.runtime_contract import ReporterLifecycleContract
from pytest_bdd.util.cucumber_formatters import (
    any_cucumber_formatter_requested,
    terminal_formatter_flags_requested,
)
from pytest_bdd.util.cucumber_formatters import (
    pytest_capture_already_configured as _pytest_capture_already_configured_impl,
)

from .plugin import (
    CucumberFormatterConfigurationError,
    GherkinMessageReporter,
)

_REPORTING_OUTPUT_OPTION_FLAGS = (
    "--messagesndjson",
    "--messages-ndjson",
    "--messagesjsonl",
    "--messages-jsonl",
    "--cucumber-html",
    "--cucumberhtml",
)
_REPORTER_STATE_ATTR = "_pytest_bdd_gherkin_message_reporter_state"


@frozen
class _ReporterStateEntry(StashBound):
    STASH_KEY: ClassVar[str] = _REPORTER_STATE_ATTR
    reporter: object


class _QuietTerminalReporter(TerminalReporter):  # type: ignore[misc]
    def __init__(self, config: Config, quiet_stream: TextIO) -> None:
        self._quiet_stream = quiet_stream
        super().__init__(config, file=quiet_stream)

    def pytest_unconfigure(self) -> None:
        super().pytest_unconfigure()
        with suppress(OSError, ValueError):
            self._quiet_stream.close()


def _reporting_requested(config: Config) -> bool:
    return any(
        [
            getattr(config.option, "messages_ndjson_path", None) is not None,
            getattr(config.option, "cucumber_html_path", None) is not None,
            any_cucumber_formatter_requested(config.option),
        ]
    )


def _reporting_requested_from_args(args: list[str]) -> bool:
    for arg in args:
        if arg in _REPORTING_OUTPUT_OPTION_FLAGS:
            return True
        if any(arg.startswith(f"{option_flag}=") for option_flag in _REPORTING_OUTPUT_OPTION_FLAGS):
            return True
        if arg.startswith("--cucumber-"):
            return True
    return False


def _terminal_formatter_flags_requested(args: list[str]) -> bool:
    return terminal_formatter_flags_requested(args)


def _pytest_capture_already_configured(args: list[str]) -> bool:
    return _pytest_capture_already_configured_impl(args)


def _running_on_windows() -> bool:
    return os.name == "nt"


def _remote_xdist_requested(args: list[str]) -> bool:
    return any(
        arg in {"--tx", "--px"} or arg.startswith("--tx=") or arg.startswith("--px=")
        for arg in args
    )


def _pytest_cache_already_configured(args: list[str]) -> bool:
    for index, arg in enumerate(args):
        if arg == "-p" and index + 1 < len(args):
            if args[index + 1] in {"cacheprovider", "no:cacheprovider"}:
                return True
            continue
        if arg.startswith("--override-ini=cache_dir="):
            return True
        if arg == "--override-ini" and index + 1 < len(args) and args[index + 1].startswith("cache_dir="):
            return True
        if arg == "-o" and index + 1 < len(args) and args[index + 1].startswith("cache_dir="):
            return True
    return False


def _replace_terminal_reporter_with_quiet_variant(config: Config):
    current_reporter = config.pluginmanager.getplugin("terminalreporter")
    if current_reporter is None or current_reporter.__class__ != TerminalReporter:
        return None

    quiet_stream = Path(os.devnull).open("w", encoding="utf-8")  # noqa: SIM115
    quiet_reporter = _QuietTerminalReporter(config, quiet_stream=quiet_stream)
    config.pluginmanager.unregister(current_reporter)
    config.pluginmanager.register(quiet_reporter, "terminalreporter")

    restored = False

    def restore() -> None:
        nonlocal restored
        if restored:
            return
        restored = True
        current_plugin = config.pluginmanager.getplugin("terminalreporter")
        if current_plugin is quiet_reporter:
            config.pluginmanager.unregister(quiet_reporter)
        if config.pluginmanager.getplugin("terminalreporter") is None:
            config.pluginmanager.register(current_reporter, "terminalreporter")
        quiet_reporter.pytest_unconfigure()

    return restore


def _config_stash(config: Config) -> Any:
    stash = getattr(config, "stash", None)
    if stash is None:
        stash = {}
        config.stash = stash
    return stash


def _store_reporter_state(config: Config, reporter: object) -> None:
    _ReporterStateEntry(reporter=reporter).set_in_stash(_config_stash(config))


def _resolve_reporter_state(config: Config) -> object | None:
    state = _ReporterStateEntry.find_in_stash(_config_stash(config))
    return None if state is None else state.reporter


def _clear_reporter_state(config: Config) -> None:
    stash = getattr(config, "stash", None)
    if stash is None:
        return
    with suppress(KeyError, AttributeError):
        del cast(Any, stash)[_ReporterStateEntry.STASH_KEY]


def _require_reporter_lifecycle_contract(reporter: object) -> ReporterLifecycleContract:
    if not isinstance(reporter, ReporterLifecycleContract):
        message = (
            "Configured gherkin message reporter does not satisfy the explicit lifecycle contract. "
            "Expected configure(pluginmanager=..., quiet_terminal_replacer=...) and "
            "unconfigure(pluginmanager=...)."
        )
        raise TypeError(message)
    return reporter


def _configure_reporter_instance(reporter: object, pluginmanager: PytestPluginManager) -> None:
    lifecycle = _require_reporter_lifecycle_contract(reporter)
    lifecycle.configure(
        pluginmanager=pluginmanager,
        quiet_terminal_replacer=_replace_terminal_reporter_with_quiet_variant,
    )


def _unconfigure_reporter_instance(reporter: object, pluginmanager: PytestPluginManager) -> None:
    lifecycle = _require_reporter_lifecycle_contract(reporter)
    lifecycle.unconfigure(pluginmanager=pluginmanager)


def pytest_addhooks(pluginmanager: PytestPluginManager) -> None:
    """Register plugin hooks."""
    from .hook import GherkinMessageReporterHookSpec

    pluginmanager.add_hookspecs(GherkinMessageReporterHookSpec)


@pytest.hookimpl(tryfirst=True)
def pytest_load_initial_conftests(early_config, parser, args) -> None:  # noqa: ARG001
    if (
        _running_on_windows()
        and _reporting_requested_from_args(list(args))
        and _remote_xdist_requested(list(args))
        and not _pytest_cache_already_configured(list(args))
    ):
        args[:] = ["-p", "no:cacheprovider", *args]
    if not _terminal_formatter_flags_requested(list(args)):
        return
    if _pytest_capture_already_configured(list(args)):
        return
    args[:] = ["--capture=no", *args]


def pytest_addoption(parser: Parser) -> None:
    """Add pytest-bdd options."""
    parser.addini(
        "pytest_bdd_transport_fail_workers",
        "internal testing hook for forcing xdist transport publication failures by worker id.",
        default="",
    )
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
    reporter = None
    try:
        reporter = GherkinMessageReporter(config=config)
    except CucumberFormatterConfigurationError as exc:
        raise pytest.UsageError(str(exc)) from exc
    try:
        _store_reporter_state(config, reporter)
        _configure_reporter_instance(reporter, config.pluginmanager)
    except Exception:
        if reporter is not None:
            _unconfigure_reporter_instance(reporter, config.pluginmanager)
        _clear_reporter_state(config)
        raise


@pytest.hookimpl(optionalhook=True, tryfirst=True)
def pytest_xdist_getremotemodule():
    from pytest_bdd_worker_bootstrap import xdist_remote

    return xdist_remote


@pytest.hookimpl(tryfirst=True)
def pytest_unconfigure(config: Config) -> None:
    reporter = _resolve_reporter_state(config)
    if reporter is not None:
        _unconfigure_reporter_instance(reporter, config.pluginmanager)
    _clear_reporter_state(config)
