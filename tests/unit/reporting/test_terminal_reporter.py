from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from pytest_bdd.compatibility.pytest import TerminalReporter
from pytest_bdd.gherkin_terminal_reporter import (
    GherkinTerminalReporter,
    add_options,
    configure,
)


def test_terminal_reporter_add_options() -> None:
    parser = MagicMock()
    group = MagicMock()
    parser.getgroup.return_value = group

    add_options(parser)
    parser.getgroup.assert_called_once_with("terminal reporting", "reporting", after="general")
    group._addoption.assert_called_once()
    args, kwargs = group._addoption.call_args
    assert "--gherkin-terminal-reporter" in args
    assert kwargs["dest"] == "gherkin_terminal_reporter"


def test_terminal_reporter_configure() -> None:
    config = MagicMock()
    config.option.gherkin_terminal_reporter = True
    current_reporter = TerminalReporter(config)
    config.pluginmanager.getplugin.side_effect = lambda name: current_reporter if name == "terminalreporter" else None

    configure(config)
    config.pluginmanager.unregister.assert_called_once_with(current_reporter)
    config.pluginmanager.register.assert_called_once()


def test_terminal_reporter_configure_incompatible_class() -> None:
    config = MagicMock()
    config.option.gherkin_terminal_reporter = True
    config.pluginmanager.getplugin.return_value = MagicMock()  # not TerminalReporter instance

    with pytest.raises(Exception, match="gherkin-terminal-reporter is not compatible with any other terminal reporter"):
        configure(config)


def test_terminal_reporter_logreport_verbosity_low() -> None:
    config = MagicMock()
    config.option.verbose = 0
    config.hook.pytest_report_teststatus.return_value = ("passed", ".", "PASSED")
    reporter = GherkinTerminalReporter(config)

    report = MagicMock()
    report.passed = True
    report.failed = False
    report.skipped = False
    report.scenario = {"name": "sc"}

    with pytest.MonkeyPatch.context() as mp:
        super_mock = MagicMock()
        mp.setattr(TerminalReporter, "pytest_runtest_logreport", super_mock)
        reporter.pytest_runtest_logreport(report)
        super_mock.assert_called_once_with(report)


def test_terminal_reporter_logreport_verbosity_high() -> None:
    config = MagicMock()
    config.option.verbose = 2
    config.hook.pytest_report_teststatus.return_value = ("passed", ".", "PASSED")
    reporter = GherkinTerminalReporter(config)
    reporter._tw = MagicMock()
    reporter.ensure_newline = MagicMock()

    report = MagicMock()
    report.passed = True
    report.failed = False
    report.skipped = False
    report.scenario = {
        "name": "Scenario Title",
        "feature": {"name": "Feature Title"},
        "steps": [
            {"keyword": "Given", "name": "step 1", "failed": False},
            {"keyword": "When", "name": "step 2", "failed": True},
        ],
    }

    reporter.pytest_runtest_logreport(report)
    reporter.ensure_newline.assert_called_once()
    assert reporter._tw.write.call_count >= 3
