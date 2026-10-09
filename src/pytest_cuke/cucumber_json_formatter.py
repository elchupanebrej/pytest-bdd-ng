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
