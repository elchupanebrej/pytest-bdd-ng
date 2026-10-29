"""Built-in adapter for Cucumber's undefined-step snippets formatter."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pytest_cuke.compatibility.pytest import get_config_root_path
from pytest_cuke.formatter_api import FormatterRequest

if TYPE_CHECKING:
    from pytest_cuke.compatibility.pytest import Config, Parser


_SNIPPETS_ADAPTER = r"""
import { EventEmitter } from "node:events";
import { createInterface } from "node:readline";

import {
  FormatterBuilder,
  SnippetsFormatter,
  formatterHelpers,
  supportCodeLibraryBuilder,
} from "@cucumber/cucumber";

const input = createInterface({ input: process.stdin, crlfDelay: Infinity });
const envelopes = [];
const parameterTypesByName = new Map();
const stepDefinitionsById = new Map();
const formatterEnvelopeNames = [
  "attachment",
  "gherkinDocument",
  "parameterType",
  "pickle",
  "testCase",
  "testCaseFinished",
  "testCaseStarted",
  "testRunFinished",
  "testStepFinished",
];

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
  if (formatterEnvelopeNames.some((name) => envelope[name] !== undefined)) {
    envelopes.push(envelope);
  }
}

let generatedId = 0;
const nextId = () => `pytest-cuke-snippet-${++generatedId}`;
const resetSupportCodeLibrary = () => supportCodeLibraryBuilder.reset(process.cwd(), nextId);

resetSupportCodeLibrary();
const builtInParameterTypeNames = new Set(
  supportCodeLibraryBuilder.finalize().parameterTypeRegistry.parameterTypes.map((item) => item.name),
);
resetSupportCodeLibrary();

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

const stepDefinitionIds = new Set(stepDefinitionsById.keys());
for (const envelope of envelopes) {
  for (const testStep of envelope.testCase?.testSteps ?? []) {
    for (const stepDefinitionId of testStep.stepDefinitionIds ?? []) {
      stepDefinitionIds.add(stepDefinitionId);
      if (!stepDefinitionsById.has(stepDefinitionId)) {
        stepDefinitionsById.set(stepDefinitionId, {
          id: stepDefinitionId,
          sourceReference: { uri: process.cwd(), location: { line: 1 } },
        });
      }
    }
  }
}

for (const _stepDefinitionId of stepDefinitionIds) {
  supportCodeLibraryBuilder.methods.defineStep(/(?!)/, () => {});
}
const supportCodeLibrary = supportCodeLibraryBuilder.finalize({
  stepDefinitionIds: [...stepDefinitionIds],
});
for (const stepDefinition of supportCodeLibrary.stepDefinitions) {
  const message = stepDefinitionsById.get(stepDefinition.id);
  if (message?.sourceReference?.uri) stepDefinition.uri = message.sourceReference.uri;
  if (Number.isInteger(message?.sourceReference?.location?.line)) {
    stepDefinition.line = message.sourceReference.location.line;
  }
}
const eventBroadcaster = new EventEmitter();
const eventDataCollector = new formatterHelpers.EventDataCollector(eventBroadcaster);
await FormatterBuilder.build(SnippetsFormatter, {
  env: process.env,
  cwd: process.cwd(),
  eventBroadcaster,
  eventDataCollector,
  log: (output) => {
    if (output) process.stdout.write(`${output}\n`);
  },
  parsedArgvOptions: {},
  stream: process.stdout,
  cleanup: async () => {},
  supportCodeLibrary,
});

for (const envelope of envelopes) {
  eventBroadcaster.emit("envelope", envelope);
}
""".strip()


def add_options(parser: Parser) -> None:
    """Register snippets selection and its equivalent ini setting."""
    group = parser.getgroup("cuke reporting", "reporting", after="general")
    group._addoption(
        "--cuke-snippets",
        action="store_true",
        dest="cuke_snippets",
        default=None,
        help="print Cucumber JavaScript suggestions for undefined steps",
    )
    parser.addini(
        "cuke_snippets",
        "Print Cucumber JavaScript suggestions for undefined steps.",
        default=False,
        type="bool",
    )


def snippets_formatter_selected(config: Config) -> bool:
    """Return whether CLI or pytest configuration enables snippets output."""
    selected = config.getoption("cuke_snippets", default=None)
    return bool(config.getini("cuke_snippets") if selected is None else selected)


def selected_snippets_formatter_requests(config: Config) -> tuple[FormatterRequest, ...]:
    """Return the snippets request only when the user enables it."""
    if not snippets_formatter_selected(config):
        return ()

    return (
        FormatterRequest(
            name="cucumber-snippets",
            command=("node", "--input-type=module", "-e", _SNIPPETS_ADAPTER),
            bypass_capture=True,
            working_directory=get_config_root_path(config),
            required_executables=("node", "npm"),
            required_npm_packages=("@cucumber/cucumber",),
            timeout_seconds=30.0,
        ),
    )


__all__ = [
    "add_options",
    "selected_snippets_formatter_requests",
    "snippets_formatter_selected",
]
