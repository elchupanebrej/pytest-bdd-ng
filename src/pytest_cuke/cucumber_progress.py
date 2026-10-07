"""Built-in live adapter for Cucumber's compact progress and summary output."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from pytest_cuke.compatibility.pytest import get_config_root_path
from pytest_cuke.formatter_api import FormatterRequest

if TYPE_CHECKING:
    from pytest_cuke.compatibility.pytest import Config, Parser


_PROGRESS_ADAPTER = r"""
import { createInterface } from "node:readline";

import { CUCUMBER_THEME, SummaryPrinter } from "@cucumber/pretty-formatter";

const markerSeparator = __MARKER_SEPARATOR__;
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
const attempts = new Map();
const summary = new SummaryPrinter();
const input = createInterface({ input: process.stdin, crlfDelay: Infinity });

for await (const line of input) {
  if (!line.trim()) continue;
  const envelope = JSON.parse(line);
  const started = envelope.testCaseStarted;
  const stepFinished = envelope.testStepFinished;
  const caseFinished = envelope.testCaseFinished;

  if (started?.id) {
    attempts.set(String(started.id), "UNKNOWN");
  } else if (stepFinished?.testCaseStartedId) {
    const attemptId = String(stepFinished.testCaseStartedId);
    const current = normalizeStatus(attempts.get(attemptId));
    const next = normalizeStatus(stepFinished.testStepResult?.status);
    if (severity.get(next) >= severity.get(current)) attempts.set(attemptId, next);
  } else if (caseFinished?.testCaseStartedId) {
    const attemptId = String(caseFinished.testCaseStartedId);
    const status = normalizeStatus(attempts.get(attemptId));
    const character = CUCUMBER_THEME.status.progress[status] ?? "?";
    process.stdout.write(markerSeparator + character + markerSeparator);
    attempts.delete(attemptId);
  } else if (envelope.testRunFinished) {
    process.stdout.write("\n\n");
  }

  summary.update(envelope);
}
""".strip()


def add_options(parser: Parser) -> None:
    """Register the existing progress option and configuration setting."""
    group = parser.getgroup("cuke reporting", "reporting", after="general")
    group._addoption(
        "--cuke-progress",
        action="store_true",
        dest="cuke_progress",
        default=None,
        help="show live Cucumber scenario-attempt progress and a final summary",
    )
    parser.addini(
        "cuke_progress",
        "Show live Cucumber scenario-attempt progress in the terminal.",
        default=False,
        type="bool",
    )


def progress_formatter_selected(config: Config) -> bool:
    """Return whether the CLI or ini configuration enables live progress."""
    selected = config.getoption("cuke_progress", default=None)
    return bool(config.getini("cuke_progress") if selected is None else selected)


def _progress_adapter(config: Config) -> str:
    verbosity = config.getoption("verbose", default=0) or 0
    capture_mode = config.getoption("capture", default=None)
    marker_separator = "\n" if verbosity > 0 or capture_mode in {"no", "tee-sys"} else ""
    return _PROGRESS_ADAPTER.replace("__MARKER_SEPARATOR__", json.dumps(marker_separator))


def selected_progress_formatter_requests(config: Config) -> tuple[FormatterRequest, ...]:
    """Return the progress request only when the user enables it."""
    if not progress_formatter_selected(config):
        return ()

    return (
        FormatterRequest(
            name="cucumber-progress",
            command=("node", "--input-type=module", "-e", _progress_adapter(config)),
            bypass_capture=True,
            working_directory=get_config_root_path(config),
            required_executables=("node",),
            required_npm_packages=("@cucumber/pretty-formatter",),
            timeout_seconds=15.0,
        ),
    )


__all__ = ["add_options", "progress_formatter_selected", "selected_progress_formatter_requests"]
