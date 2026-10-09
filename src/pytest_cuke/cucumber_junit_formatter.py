"""Official message-driven Cucumber JUnit XML formatter adapter."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from pytest_cuke.compatibility.pytest import get_config_root_path
from pytest_cuke.cucumber_junit import configured_cucumber_junit_output_value
from pytest_cuke.formatter_api import FormatterRequest, FormatterSelection

if TYPE_CHECKING:
    from pytest_cuke.compatibility.pytest import Config


_JUNIT_ADAPTER = r"""
import { createInterface } from "node:readline";

import junitXmlFormatter from "@cucumber/junit-xml-formatter";

const input = createInterface({ input: process.stdin, crlfDelay: Infinity });
const messageHandlers = [];

junitXmlFormatter.formatter({
  options: {},
  on: (type, handler) => {
    if (type !== "message") throw new Error(`Unsupported formatter event ${type}`);
    messageHandlers.push(handler);
  },
  write: (content) => {
    process.stdout.write(content);
  },
});

for await (const line of input) {
  if (!line.trim()) continue;
  const envelope = JSON.parse(line);
  for (const handler of messageHandlers) handler(envelope);
}
""".strip()


def _formatter_request(*, working_directory: Path, output_path: Path | None) -> FormatterRequest:
    return FormatterRequest(
        name="cucumber-junit",
        command=("node", "--input-type=module", "-e", _JUNIT_ADAPTER),
        output_path=output_path,
        working_directory=working_directory,
        required_executables=("node", "npm"),
        required_npm_packages=("@cucumber/junit-xml-formatter",),
        timeout_seconds=60.0,
    )


def selected_cucumber_junit_formatter_requests(config: Config) -> tuple[FormatterRequest, ...]:
    """Select the official message-driven JUnit XML formatter for a live pytest run."""
    output = configured_cucumber_junit_output_value(config)
    if output is None:
        return ()
    return (_formatter_request(working_directory=get_config_root_path(config), output_path=Path(output)),)


def replay_cucumber_junit_formatter_request(selection: FormatterSelection) -> FormatterRequest:
    """Build the formatter request used for standalone saved-stream conversion."""
    return _formatter_request(working_directory=selection.working_directory, output_path=selection.destination)


__all__ = ["replay_cucumber_junit_formatter_request", "selected_cucumber_junit_formatter_requests"]
