"""Built-in adapter for Cucumber's machine-readable step-definition usage formatter."""

from __future__ import annotations

from argparse import ArgumentTypeError
from pathlib import Path
from typing import TYPE_CHECKING

from pytest_cuke.compatibility.pytest import get_config_root_path
from pytest_cuke.formatter_api import FormatterRequest

if TYPE_CHECKING:
    from pytest_cuke.compatibility.pytest import Config, Parser


_USAGE_JSON_ADAPTER = r"""
import { EventEmitter } from "node:events";
import { createInterface } from "node:readline";

import {
  FormatterBuilder,
  UsageJsonFormatter,
  formatterHelpers,
  supportCodeLibraryBuilder,
} from "@cucumber/cucumber";

const input = createInterface({ input: process.stdin, crlfDelay: Infinity });
const envelopes = [];
const parameterTypesByName = new Map();
const stepDefinitionsById = new Map();

const createSupportCodeLibrary = () => {
  let generatedId = 0;
  const nextId = () => `pytest-cuke-usage-json-${++generatedId}`;
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
      throw new Error(`Cucumber usage JSON received step definition ${stepDefinitionId} without a pattern source`);
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
await FormatterBuilder.build(UsageJsonFormatter, {
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
    """Register the required usage JSON output path and its equivalent ini setting."""
    group = parser.getgroup("cuke reporting", "reporting", after="general")
    group._addoption(
        "--cuke-usage-json",
        action="store",
        dest="cuke_usage_json",
        metavar="PATH",
        type=_required_output_path,
        default=None,
        help="write Cucumber step-definition usage as JSON to PATH",
    )
    parser.addini(
        "cuke_usage_json",
        "Write Cucumber step-definition usage JSON to the configured path.",
        default="",
        type="string",
    )


def _required_output_path(value: str) -> str:
    if not value:
        raise ArgumentTypeError("usage JSON output path must not be empty")
    return value


def _configured_usage_json_path(config: Config) -> str | None:
    selected = config.getoption("cuke_usage_json", default=None)
    if selected is None:
        selected = config.getini("cuke_usage_json")
    return selected if isinstance(selected, str) and selected else None


def selected_usage_json_formatter_requests(config: Config) -> tuple[FormatterRequest, ...]:
    """Return the usage JSON request only when a file path is selected."""
    configured_path = _configured_usage_json_path(config)
    if configured_path is None:
        return ()

    return (
        FormatterRequest(
            name="cucumber-usage-json",
            command=("node", "--input-type=module", "-e", _USAGE_JSON_ADAPTER),
            output_path=Path(configured_path),
            working_directory=get_config_root_path(config),
            required_executables=("node", "npm"),
            required_npm_packages=("@cucumber/cucumber",),
            timeout_seconds=30.0,
        ),
    )


__all__ = ["add_options", "selected_usage_json_formatter_requests"]
