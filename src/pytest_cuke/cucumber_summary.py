"""Built-in adapter for Cucumber's official scenario and step summary."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pytest_cuke.compatibility.pytest import get_config_root_path
from pytest_cuke.formatter_api import FormatterRequest

if TYPE_CHECKING:
    from pytest_cuke.compatibility.pytest import Config, Parser


_SUMMARY_ADAPTER = r"""
import { EventEmitter } from "node:events";
import { createInterface } from "node:readline";

import {
  FormatterBuilder,
  SummaryFormatter,
  formatterHelpers,
  supportCodeLibraryBuilder,
} from "@cucumber/cucumber";

const input = createInterface({ input: process.stdin, crlfDelay: Infinity });
const bufferedEnvelopes = [];
const parameterTypesByName = new Map();
const stepDefinitionsById = new Map();
const formatterEnvelopeNames = [
  "attachment",
  "gherkinDocument",
  "parameterType",
  "pickle",
  "stepDefinition",
  "testCase",
  "testCaseFinished",
  "testCaseStarted",
  "testRunFinished",
  "testRunStarted",
  "testStepFinished",
];
let eventBroadcaster;
let supportCodeLibrary;

const addStepDefinitionToLibrary = (stepDefinitionId, message) => {
  if (!supportCodeLibrary) return;
  let stepDefinition = supportCodeLibrary.stepDefinitions.find((item) => item.id === stepDefinitionId);
  if (!stepDefinition) {
    stepDefinition = { id: stepDefinitionId, uri: process.cwd(), line: 1 };
    supportCodeLibrary.stepDefinitions.push(stepDefinition);
  }
  if (message?.sourceReference?.uri) stepDefinition.uri = message.sourceReference.uri;
  if (Number.isInteger(message?.sourceReference?.location?.line)) {
    stepDefinition.line = message.sourceReference.location.line;
  }
};

const updateSupportCodeLibrary = (envelope) => {
  const stepDefinition = envelope.stepDefinition;
  if (stepDefinition && typeof stepDefinition.id === "string") {
    addStepDefinitionToLibrary(stepDefinition.id, stepDefinition);
  }
  for (const testStep of envelope.testCase?.testSteps ?? []) {
    for (const stepDefinitionId of testStep.stepDefinitionIds ?? []) {
      addStepDefinitionToLibrary(stepDefinitionId, stepDefinitionsById.get(stepDefinitionId));
    }
  }
};

const createSupportCodeLibrary = () => {
  let generatedId = 0;
  const nextId = () => `pytest-cuke-summary-${++generatedId}`;
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

  for (const envelope of bufferedEnvelopes) {
    const stepDefinition = envelope.stepDefinition;
    if (stepDefinition && typeof stepDefinition.id === "string") {
      stepDefinitionsById.set(stepDefinition.id, stepDefinition);
    }
    for (const testStep of envelope.testCase?.testSteps ?? []) {
      for (const stepDefinitionId of testStep.stepDefinitionIds ?? []) {
        if (!stepDefinitionsById.has(stepDefinitionId)) {
          stepDefinitionsById.set(stepDefinitionId, {
            id: stepDefinitionId,
            sourceReference: { uri: process.cwd(), location: { line: 1 } },
          });
        }
      }
    }
  }

  const stepDefinitionIds = new Set(stepDefinitionsById.keys());
  for (const _stepDefinitionId of stepDefinitionIds) {
    supportCodeLibraryBuilder.methods.defineStep(/(?!)/, () => {});
  }
  supportCodeLibrary = supportCodeLibraryBuilder.finalize({ stepDefinitionIds: [...stepDefinitionIds] });
  for (const stepDefinition of supportCodeLibrary.stepDefinitions) {
    const message = stepDefinitionsById.get(stepDefinition.id);
    addStepDefinitionToLibrary(stepDefinition.id, message);
  }
  return supportCodeLibrary;
};

const startFormatter = async () => {
  eventBroadcaster = new EventEmitter();
  const eventDataCollector = new formatterHelpers.EventDataCollector(eventBroadcaster);
  await FormatterBuilder.build(SummaryFormatter, {
    env: process.env,
    cwd: process.cwd(),
    eventBroadcaster,
    eventDataCollector,
    log: (output) => {
      if (!output) return;
      process.stdout.write(output.endsWith("\n") ? output : `${output}\n`);
    },
    parsedArgvOptions: {},
    stream: process.stdout,
    cleanup: async () => {},
    supportCodeLibrary: createSupportCodeLibrary(),
  });
  for (const envelope of bufferedEnvelopes) eventBroadcaster.emit("envelope", envelope);
  bufferedEnvelopes.length = 0;
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

  updateSupportCodeLibrary(envelope);
  if (!eventBroadcaster) {
    if (formatterEnvelopeNames.some((name) => envelope[name] !== undefined)) {
      bufferedEnvelopes.push(envelope);
    }
    if (envelope.testRunStarted) await startFormatter();
  } else {
    eventBroadcaster.emit("envelope", envelope);
  }
}
""".strip()


def add_options(parser: Parser) -> None:
    """Register Cucumber summary selection and its equivalent ini setting."""
    group = parser.getgroup("cuke reporting", "reporting", after="general")
    group._addoption(
        "--cuke-summary",
        action="store_true",
        dest="cuke_summary",
        default=None,
        help="show Cucumber scenario and step totals after the run",
    )
    parser.addini(
        "cuke_summary",
        "Show Cucumber scenario and step totals after the run.",
        default=False,
        type="bool",
    )


def summary_formatter_selected(config: Config) -> bool:
    """Return whether CLI or pytest configuration enables the summary formatter."""
    selected = config.getoption("cuke_summary", default=None)
    return bool(config.getini("cuke_summary") if selected is None else selected)


def selected_summary_formatter_requests(config: Config) -> tuple[FormatterRequest, ...]:
    """Return the Cucumber summary request only when the user enables it."""
    if not summary_formatter_selected(config):
        return ()

    return (
        FormatterRequest(
            name="cucumber-summary",
            command=("node", "--input-type=module", "-e", _SUMMARY_ADAPTER),
            bypass_capture=True,
            working_directory=get_config_root_path(config),
            required_executables=("node", "npm"),
            required_npm_packages=("@cucumber/cucumber",),
            timeout_seconds=30.0,
        ),
    )


__all__ = ["add_options", "selected_summary_formatter_requests", "summary_formatter_selected"]
