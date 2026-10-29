"""Replay built-in reports with the same Node adapters used during live runs."""

from __future__ import annotations

import json
import shutil
import sys

from pytest_cuke.cucumber_pretty import _PRETTY_ADAPTER
from pytest_cuke.cucumber_progress import _PROGRESS_ADAPTER
from pytest_cuke.cucumber_progress_bar import _PROGRESS_BAR_ADAPTER
from pytest_cuke.cucumber_snippets import _SNIPPETS_ADAPTER
from pytest_cuke.cucumber_summary import _SUMMARY_ADAPTER
from pytest_cuke.cucumber_usage import _USAGE_ADAPTER
from pytest_cuke.cucumber_usage_json import _USAGE_JSON_ADAPTER
from pytest_cuke.formatter_api import FormatterRequest, FormatterSelection

_ADAPTERS = {
    "pretty": (_PRETTY_ADAPTER, "@cucumber/pretty-formatter"),
    "progress": (_PROGRESS_ADAPTER, "@cucumber/pretty-formatter"),
    "progress-bar": (_PROGRESS_BAR_ADAPTER, "@cucumber/pretty-formatter"),
    "snippets": (_SNIPPETS_ADAPTER, "@cucumber/cucumber"),
    "summary": (_SUMMARY_ADAPTER, "@cucumber/cucumber"),
    "usage": (_USAGE_ADAPTER, "@cucumber/cucumber"),
    "usage-json": (_USAGE_JSON_ADAPTER, "@cucumber/cucumber"),
}


def replay_builtin_formatter_request(selection: FormatterSelection) -> FormatterRequest:
    """Configure a built-in adapter for terminal or staged file output."""
    adapter, package = _ADAPTERS[selection.name]
    use_tty_layout = selection.destination is None and sys.stdout.isatty()
    adapter = (
        adapter.replace("__USE_TTY_LAYOUT__", json.dumps(use_tty_layout))
        .replace("__TERMINAL_COLUMNS__", str(shutil.get_terminal_size(fallback=(80, 24)).columns))
        .replace("__MARKER_SEPARATOR__", json.dumps(""))
    )
    return FormatterRequest(
        name=selection.name,
        command=("node", "--input-type=module", "-e", adapter),
        output_path=selection.destination,
        working_directory=selection.working_directory,
        required_executables=("node",),
        required_npm_packages=(package,),
        timeout_seconds=30.0,
    )


__all__ = ["replay_builtin_formatter_request"]
