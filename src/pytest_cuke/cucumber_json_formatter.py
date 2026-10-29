"""Message-driven Cucumber JSON formatter backed by the official Cucumber package."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from pytest_cuke.compatibility.pytest import get_config_root_path
from pytest_cuke.cucumber_json import configured_cucumber_json_backend, configured_cucumber_json_output_value
from pytest_cuke.formatter_api import FormatterRequest, FormatterSelection

if TYPE_CHECKING:
    from pytest_cuke.compatibility.pytest import Config


_JSON_ADAPTER = r"""
import { EventEmitter } from "node:events";
import { createInterface } from "node:readline";

import {
  FormatterBuilder,
  JsonFormatter,
  formatterHelpers,
  supportCodeLibraryBuilder,
} from "@cucumber/cucumber";

const input = createInterface({ input: process.stdin, crlfDelay: Infinity });
const envelopes = [];
const stepDefinitionsById = new Map();
const picklesById = new Map();
const testCasesById = new Map();
const testCaseStarted = [];
const testCaseFinishedByStartedId = new Map();
const externalExamplesSourcesByPickleId = new Map();
let report = "";

const createSupportCodeLibrary = () => {
  let generatedId = 0;
  const nextId = () => `pytest-cuke-json-${++generatedId}`;
  supportCodeLibraryBuilder.reset(process.cwd(), nextId);
  const stepDefinitionIds = [...stepDefinitionsById.keys()];
  for (let index = 0; index < stepDefinitionIds.length; index += 1) {
    supportCodeLibraryBuilder.methods.defineStep(`pytest cuke JSON adapter placeholder ${index}`, () => {});
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
  const stepDefinition = envelope.stepDefinition;
  if (stepDefinition && typeof stepDefinition.id === "string") {
    stepDefinitionsById.set(stepDefinition.id, stepDefinition);
  }
  if (envelope.pickle && typeof envelope.pickle.id === "string") {
    picklesById.set(envelope.pickle.id, envelope.pickle);
  }
  if (envelope.testCase && typeof envelope.testCase.id === "string") {
    testCasesById.set(envelope.testCase.id, envelope.testCase);
  }
  if (envelope.testCaseStarted && typeof envelope.testCaseStarted.id === "string") {
    testCaseStarted.push(envelope.testCaseStarted);
  }
  if (envelope.testCaseFinished && typeof envelope.testCaseFinished.testCaseStartedId === "string") {
    testCaseFinishedByStartedId.set(
      envelope.testCaseFinished.testCaseStartedId,
      envelope.testCaseFinished,
    );
  }
  const attachment = envelope.attachment;
  if (
    attachment?.mediaType === "application/vnd.pytest-bdd.launch+json"
    && attachment.contentEncoding === "IDENTITY"
    && typeof attachment.body === "string"
  ) {
    const launch = JSON.parse(attachment.body);
    if (
      typeof launch.pickleId === "string"
      && launch.externalExamplesSource
      && typeof launch.externalExamplesSource.path === "string"
    ) {
      externalExamplesSourcesByPickleId.set(launch.pickleId, launch.externalExamplesSource);
    }
  }
  envelopes.push(envelope);
}

const eventBroadcaster = new EventEmitter();
const eventDataCollector = new formatterHelpers.EventDataCollector(eventBroadcaster);
await FormatterBuilder.build(JsonFormatter, {
  env: process.env,
  cwd: process.cwd(),
  eventBroadcaster,
  eventDataCollector,
  log: (output) => {
    if (output) report += output;
  },
  parsedArgvOptions: {},
  stream: process.stdout,
  cleanup: async () => {},
  supportCodeLibrary: createSupportCodeLibrary(),
});

for (const envelope of envelopes) {
  eventBroadcaster.emit("envelope", envelope);
}

const externalExamplesByFeatureAndName = new Map();
for (const started of testCaseStarted) {
  if (testCaseFinishedByStartedId.get(started.id)?.willBeRetried) continue;
  const testCase = testCasesById.get(started.testCaseId);
  const pickle = picklesById.get(testCase?.pickleId);
  const source = externalExamplesSourcesByPickleId.get(pickle?.id);
  if (!pickle || !source) continue;

  const key = JSON.stringify([pickle.uri, pickle.name]);
  const queue = externalExamplesByFeatureAndName.get(key) ?? [];
  queue.push({
    path: source.path,
    marker_line: source.markerLine,
    section_index: source.sectionIndex,
    row_index: source.rowIndex,
    source_line: source.sourceLine,
  });
  externalExamplesByFeatureAndName.set(key, queue);
}

const features = JSON.parse(report);
for (const feature of features) {
  for (const element of feature.elements ?? []) {
    const key = JSON.stringify([feature.uri, element.name]);
    const source = externalExamplesByFeatureAndName.get(key)?.shift();
    if (source) element.external_examples_source = source;
  }
}
process.stdout.write(JSON.stringify(features, null, 2));
""".strip()


def _formatter_request(*, working_directory: Path, output_path: Path | None) -> FormatterRequest:
    return FormatterRequest(
        name="cucumber-json",
        command=("node", "--input-type=module", "-e", _JSON_ADAPTER),
        output_path=output_path,
        working_directory=working_directory,
        required_executables=("node", "npm"),
        required_npm_packages=("@cucumber/cucumber",),
        timeout_seconds=60.0,
    )


def selected_cucumber_json_formatter_requests(config: Config) -> tuple[FormatterRequest, ...]:
    """Select the official message-driven formatter when it owns Cucumber JSON output."""
    output = configured_cucumber_json_output_value(config)
    if output is None or configured_cucumber_json_backend(config) != "cucumber":
        return ()
    return (_formatter_request(working_directory=get_config_root_path(config), output_path=Path(output)),)


def replay_cucumber_json_formatter_request(selection: FormatterSelection) -> FormatterRequest:
    """Build the formatter request used by standalone saved-stream replay."""
    return _formatter_request(working_directory=selection.working_directory, output_path=selection.destination)


__all__ = ["replay_cucumber_json_formatter_request", "selected_cucumber_json_formatter_requests"]
