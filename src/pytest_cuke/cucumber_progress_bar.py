"""Built-in live adapter for Cucumber's width-aware progress bar."""

from __future__ import annotations

import json
import os
from typing import TYPE_CHECKING

from pytest_cuke.compatibility.pytest import get_config_root_path
from pytest_cuke.formatter_api import FormatterRequest

if TYPE_CHECKING:
    from pytest_cuke.compatibility.pytest import Config, Parser


_PROGRESS_BAR_ADAPTER = r"""
import { createInterface } from "node:readline";

import { CUCUMBER_THEME, SummaryPrinter } from "@cucumber/pretty-formatter";

const useTtyLayout = __USE_TTY_LAYOUT__;
const terminalColumns = __TERMINAL_COLUMNS__;
const severity = new Map([
  ["FAILED", 60],
  ["AMBIGUOUS", 50],
  ["UNDEFINED", 40],
  ["PENDING", 30],
  ["SKIPPED", 20],
  ["PASSED", 10],
  ["UNKNOWN", 0],
]);
const normalizeStatus = (status) => {
  const normalized = typeof status === "string" ? status.toUpperCase() : "UNKNOWN";
  return severity.has(normalized) ? normalized : "UNKNOWN";
};
const worseStatus = (current, next) => {
  const currentStatus = normalizeStatus(current);
  const nextStatus = normalizeStatus(next);
  return severity.get(nextStatus) > severity.get(currentStatus) ? nextStatus : currentStatus;
};
const progressCharacter = (status) => CUCUMBER_THEME.status.progress[normalizeStatus(status)] ?? "?";
const pickleIds = new Set();
const testCaseIds = new Set();
const pickleIdsByTestCaseId = new Map();
const pickleIdsByStartedId = new Map();
const attemptStatuses = new Map();
const completedPickleIds = new Set();
const summary = new SummaryPrinter();
const input = createInterface({ input: process.stdin, crlfDelay: Infinity });
let completedAttempts = 0;

const writeProgress = (status) => {
  const marker = progressCharacter(status);
  if (!useTtyLayout) {
    process.stdout.write(marker);
    return;
  }

  const total = Math.max(pickleIds.size, testCaseIds.size, 1);
  const completed = Math.min(
    completedPickleIds.size > 0 ? completedPickleIds.size : completedAttempts,
    total,
  );
  const ratio = Math.min(completed / total, 1);
  const count = `${completed}/${total}`;
  const markerSuffix = ` ${marker}`;
  let prefix = `${count} scenarios `;
  let barWidth = terminalColumns - prefix.length - markerSuffix.length - 2;
  if (barWidth < 1) {
    prefix = `${count} `;
    barWidth = terminalColumns - prefix.length - markerSuffix.length - 2;
  }

  if (barWidth < 1) {
    process.stdout.write(`\r${`${count}${markerSuffix}`.slice(0, terminalColumns)}\u001b[0K`);
    return;
  }

  const filledWidth = Math.round(barWidth * ratio);
  const bar = `${"#".repeat(filledWidth)}${"-".repeat(Math.max(barWidth - filledWidth, 0))}`;
  process.stdout.write(`\r${prefix}[${bar}]${markerSuffix}\u001b[0K`);
};

for await (const line of input) {
  if (!line.trim()) continue;
  const envelope = JSON.parse(line);
  const pickle = envelope.pickle;
  const testCase = envelope.testCase;
  const started = envelope.testCaseStarted;
  const stepFinished = envelope.testStepFinished;
  const caseFinished = envelope.testCaseFinished;

  if (pickle?.id) {
    pickleIds.add(String(pickle.id));
  } else if (testCase?.id) {
    const testCaseId = String(testCase.id);
    testCaseIds.add(testCaseId);
    if (testCase.pickleId) {
      const pickleId = String(testCase.pickleId);
      pickleIds.add(pickleId);
      pickleIdsByTestCaseId.set(testCaseId, pickleId);
    }
  } else if (started?.id) {
    const startedId = String(started.id);
    attemptStatuses.set(startedId, "UNKNOWN");
    if (started.testCaseId) {
      const pickleId = pickleIdsByTestCaseId.get(String(started.testCaseId));
      if (pickleId) pickleIdsByStartedId.set(startedId, pickleId);
    }
  } else if (stepFinished?.testCaseStartedId) {
    const startedId = String(stepFinished.testCaseStartedId);
    attemptStatuses.set(
      startedId,
      worseStatus(attemptStatuses.get(startedId), stepFinished.testStepResult?.status),
    );
  } else if (caseFinished?.testCaseStartedId) {
    const startedId = String(caseFinished.testCaseStartedId);
    const status = normalizeStatus(attemptStatuses.get(startedId));
    completedAttempts += 1;
    const pickleId = pickleIdsByStartedId.get(startedId);
    if (pickleId) completedPickleIds.add(pickleId);
    writeProgress(status);
    attemptStatuses.delete(startedId);
  } else if (envelope.testRunFinished) {
    process.stdout.write("\n\n");
  }

  summary.update(envelope);
}
""".strip()


def add_options(parser: Parser) -> None:
    """Register the progress-bar option and its equivalent ini setting."""
    group = parser.getgroup("cuke reporting", "reporting", after="general")
    group._addoption(
        "--cuke-progress-bar",
        action="store_true",
        dest="cuke_progress_bar",
        default=None,
        help="show a live Cucumber progress bar in a TTY and progress markers in piped output",
    )
    parser.addini(
        "cuke_progress_bar",
        "Show a live Cucumber progress bar or piped progress markers.",
        default=False,
        type="bool",
    )


def progress_bar_formatter_selected(config: Config) -> bool:
    """Return whether CLI or pytest configuration enables the progress bar."""
    selected = config.getoption("cuke_progress_bar", default=None)
    return bool(config.getini("cuke_progress_bar") if selected is None else selected)


def _is_terminal(config: Config) -> bool:
    terminal_reporter = config.pluginmanager.get_plugin("terminalreporter")
    isatty = getattr(terminal_reporter, "isatty", None)
    if callable(isatty):
        return bool(isatty())
    if isatty is not None:
        return bool(isatty)
    terminal_writer = getattr(terminal_reporter, "_tw", None)
    terminal_stream = getattr(terminal_writer, "_file", None)
    stream_isatty = getattr(terminal_stream, "isatty", None)
    return bool(stream_isatty()) if callable(stream_isatty) else False


def _terminal_columns(config: Config) -> int:
    terminal_reporter = config.pluginmanager.get_plugin("terminalreporter")
    terminal_writer = getattr(terminal_reporter, "_tw", None)
    terminal_stream = getattr(terminal_writer, "_file", None)
    fileno = getattr(terminal_stream, "fileno", None)
    if callable(fileno):
        try:
            columns = os.get_terminal_size(fileno()).columns
        except (OSError, ValueError):
            columns = None
        if isinstance(columns, int) and columns > 0:
            return columns

    configured_columns = os.environ.get("COLUMNS")
    if configured_columns is not None:
        try:
            columns = int(configured_columns)
        except ValueError:
            columns = None
        if isinstance(columns, int) and columns > 0:
            return columns
    return 80


def _progress_bar_adapter(config: Config) -> str:
    return (
        _PROGRESS_BAR_ADAPTER.replace("__USE_TTY_LAYOUT__", json.dumps(_is_terminal(config))).replace(
            "__TERMINAL_COLUMNS__", str(_terminal_columns(config))
        )
    )


def selected_progress_bar_formatter_requests(config: Config) -> tuple[FormatterRequest, ...]:
    """Return a terminal progress-bar request only when it is selected."""
    if not progress_bar_formatter_selected(config):
        return ()

    return (
        FormatterRequest(
            name="cucumber-progress-bar",
            command=("node", "--input-type=module", "-e", _progress_bar_adapter(config)),
            bypass_capture=True,
            working_directory=get_config_root_path(config),
            required_executables=("node",),
            required_npm_packages=("@cucumber/pretty-formatter",),
            timeout_seconds=15.0,
        ),
    )


__all__ = [
    "add_options",
    "progress_bar_formatter_selected",
    "selected_progress_bar_formatter_requests",
]
