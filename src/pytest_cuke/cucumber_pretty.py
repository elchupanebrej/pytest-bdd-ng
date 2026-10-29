"""Built-in live adapter for Cucumber's official pretty formatter."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pytest_cuke.compatibility.pytest import get_config_root_path
from pytest_cuke.formatter_api import FormatterRequest

if TYPE_CHECKING:
    from pytest_cuke.compatibility.pytest import Config


_PRETTY_ADAPTER = r"""
import { createInterface } from "node:readline";
import { Writable } from "node:stream";

import { PrettyPrinter } from "@cucumber/pretty-formatter";

const output = new Writable({
  write(chunk, _encoding, callback) {
    process.stdout.write(chunk, callback);
  },
});
const printer = new PrettyPrinter({ stream: output });
const input = createInterface({ input: process.stdin, crlfDelay: Infinity });

for await (const line of input) {
  if (line) printer.update(JSON.parse(line));
}
""".strip()


def selected_pretty_formatter_requests(config: Config) -> tuple[FormatterRequest, ...]:
    """Return the pretty request only when the user enables it."""
    selected = config.getoption("cuke_pretty", default=None)
    if selected is None:
        selected = config.getini("cuke_pretty")
    if not selected:
        return ()

    return (
        FormatterRequest(
            name="cucumber-pretty",
            command=("node", "--input-type=module", "-e", _PRETTY_ADAPTER),
            bypass_capture=True,
            working_directory=get_config_root_path(config),
            required_executables=("node",),
            required_npm_packages=("@cucumber/pretty-formatter",),
            timeout_seconds=15.0,
        ),
    )


__all__ = ["selected_pretty_formatter_requests"]
