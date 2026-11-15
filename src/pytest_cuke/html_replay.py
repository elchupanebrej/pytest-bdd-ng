"""Offline Cucumber HTML replay formatter factory."""

from __future__ import annotations

import sys

from pytest_cuke.formatter_api import FormatterRequest, FormatterSelection


def replay_html_formatter_request(selection: FormatterSelection) -> FormatterRequest:
    """Run the HTML renderer as a formatter child over the saved Messages stream."""
    return FormatterRequest(
        name=selection.name,
        command=(sys.executable, "-m", "pytest_cuke.html_replay_worker"),
        output_path=selection.destination,
        working_directory=selection.working_directory,
        required_npm_packages=("@cucumber/html-formatter",),
        timeout_seconds=120.0,
    )


__all__ = ["replay_html_formatter_request"]
