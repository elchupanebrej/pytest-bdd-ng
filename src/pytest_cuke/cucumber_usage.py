"""Built-in adapter for Cucumber's step-definition usage formatter."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import TYPE_CHECKING

from pytest_cuke.compatibility.pytest import get_config_root_path
from pytest_cuke.formatter_api import FormatterRequest

if TYPE_CHECKING:
    from pytest_cuke.compatibility.pytest import Config, Parser


_USAGE_ADAPTER = r"""
import { EventEmitter } from "node:events";
import { createRequire } from "node:module";
import { createInterface } from "node:readline";

import {
  FormatterBuilder,
  UsageFormatter,
  formatterHelpers,
  supportCodeLibraryBuilder,
} from "@cucumber/cucumber";

const useTtyLayout = __USE_TTY_LAYOUT__;
const terminalColumns = __TERMINAL_COLUMNS__;
const input = createInterface({ input: process.stdin, crlfDelay: Infinity });
const envelopes = [];
const parameterTypesByName = new Map();
const stepDefinitionsById = new Map();

if (useTtyLayout) {
  const require = createRequire(import.meta.resolve("@cucumber/cucumber"));
  const Table = require("cli-table3");
  const renderTable = Table.prototype.toString;
  Table.prototype.toString = function (...args) {
    if (this.options?.head?.[0] === "Pattern / Text") {
      const availableWidth = Math.max(30, terminalColumns - 4);
      const durationWidth = Math.min(14, Math.max(10, Math.floor(availableWidth * 0.2)));
      const locationWidth = Math.min(24, Math.max(12, Math.floor(availableWidth * 0.28)));
      const patternWidth = Math.max(12, availableWidth - durationWidth - locationWidth);
      this.options.colWidths = [patternWidth, durationWidth, locationWidth];
      this.options.wordWrap = true;
    }
    return renderTable.apply(this, args);
  };
}

const createSupportCodeLibrary = () => {
  let generatedId = 0;
  const nextId = () => `pytest-cuke-usage-${++generatedId}`;
  supportCodeLibraryBuilder.reset(process.cwd(), nextId);
  const builtInParameterTypeNames = new Set(
    supportCodeLibraryBuilder.finalize().parameterTypeRegistry.parameterTypes.map((item) => item.name),
  );
  supportCodeLibraryBuilder.reset(process.cwd(), nextId);

  for (const parameterType of parameterTypesByName.values()) {
    if (builtInParameterTypeNames.has(parameterType.name)) continue;
    if (!Array.isArray(parameterType.regularExpressions) || parameterType.regularExpressions.length === 0) continue;
    supportCodeLibraryBuilder.methods.defineParameterType({
      name: parameterType.name,
      regexp: parameterType.regularExpressions,
      transformer: (value) => value,
      useForSnippets: parameterType.useForSnippets,
      preferForRegexpMatch: parameterType.preferForRegularExpressionMatch,
    });
  }

  const stepDefinitionIds = [...stepDefinitionsById.keys()];
  for (const stepDefinitionId of stepDefinitionIds) {
    const message = stepDefinitionsById.get(stepDefinitionId);
    const source = message?.pattern?.source;
    const type = message?.pattern?.type;
    if (typeof source !== "string") {
      throw new Error(`Cucumber usage received step definition ${stepDefinitionId} without a pattern source`);
    }
    const expression = type === "REGULAR_EXPRESSION" ? new RegExp(source) : source;
    supportCodeLibraryBuilder.methods.defineStep(expression, () => {});
  }

  const supportCodeLibrary = supportCodeLibraryBuilder.finalize({ stepDefinitionIds });
  for (const stepDefinition of supportCodeLibrary.stepDefinitions) {
    const message = stepDefinitionsById.get(stepDefinition.id);
    if (message?.sourceReference?.uri) stepDefinition.uri = message.sourceReference.uri;
    if (Number.isInteger(message?.sourceReference?.location?.line)) {
      stepDefinition.line = message.sourceReference.location.line;
    }
  }
  return supportCodeLibrary;
};

for await (const line of input) {
  if (!line.trim()) continue;
  const envelope = JSON.parse(line);
  const parameterType = envelope.parameterType;
  if (parameterType && typeof parameterType.name === "string") {
    parameterTypesByName.set(parameterType.name, parameterType);
  }
  const stepDefinition = envelope.stepDefinition;
  if (stepDefinition && typeof stepDefinition.id === "string") {
    stepDefinitionsById.set(stepDefinition.id, stepDefinition);
  }
  envelopes.push(envelope);
}

const eventBroadcaster = new EventEmitter();
const eventDataCollector = new formatterHelpers.EventDataCollector(eventBroadcaster);
await FormatterBuilder.build(UsageFormatter, {
  env: process.env,
  cwd: process.cwd(),
  eventBroadcaster,
  eventDataCollector,
  log: (output) => {
    if (output) process.stdout.write(output);
  },
  parsedArgvOptions: {},
  stream: process.stdout,
  cleanup: async () => {},
  supportCodeLibrary: createSupportCodeLibrary(),
});

for (const envelope of envelopes) {
  eventBroadcaster.emit("envelope", envelope);
}
""".strip()


def add_options(parser: Parser) -> None:
    """Register usage selection and its equivalent ini setting."""
    group = parser.getgroup("cuke reporting", "reporting", after="general")
    group._addoption(
        "--cuke-usage",
        action="store",
        nargs="?",
        const="-",
        dest="cuke_usage",
        metavar="PATH",
        default=None,
        help="show step-definition usage in the terminal or write it to PATH",
    )
    parser.addini(
        "cuke_usage",
        "Write Cucumber step-definition usage to the terminal or the configured path.",
        default="",
        type="string",
    )


def _configured_usage_path(config: Config) -> str | None:
    selected = config.getoption("cuke_usage", default=None)
    if selected is None:
        selected = config.getini("cuke_usage")
    return selected if isinstance(selected, str) and selected else None


def usage_formatter_selected(config: Config) -> bool:
    """Return whether a CLI option or pytest ini value enables usage output."""
    return _configured_usage_path(config) is not None


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


def _usage_adapter(config: Config, *, output_path: Path | None) -> str:
    use_tty_layout = output_path is None and _is_terminal(config)
    return _USAGE_ADAPTER.replace("__USE_TTY_LAYOUT__", json.dumps(use_tty_layout)).replace(
        "__TERMINAL_COLUMNS__", str(_terminal_columns(config))
    )


def selected_usage_formatter_requests(config: Config) -> tuple[FormatterRequest, ...]:
    """Return the Cucumber usage request only when the user enables it."""
    configured_path = _configured_usage_path(config)
    if configured_path is None:
        return ()

    output_path = None if configured_path == "-" else Path(configured_path)
    return (
        FormatterRequest(
            name="cucumber-usage",
            command=("node", "--input-type=module", "-e", _usage_adapter(config, output_path=output_path)),
            output_path=output_path,
            working_directory=get_config_root_path(config),
            required_executables=("node", "npm"),
            required_npm_packages=("@cucumber/cucumber",),
            bypass_capture=output_path is None,
            timeout_seconds=30.0,
        ),
    )


__all__ = [
    "add_options",
    "selected_usage_formatter_requests",
    "usage_formatter_selected",
]
