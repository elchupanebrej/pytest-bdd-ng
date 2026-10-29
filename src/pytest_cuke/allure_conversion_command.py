"""Standalone command-line interface for converting Cucumber Messages to Allure."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from pytest_cuke.allure_conversion import AllureConversionError, convert_allure_messages


def configure_allure_conversion_parser(parser: argparse.ArgumentParser) -> None:
    """Add arguments for ``cuke convert allure``."""
    parser.add_argument("messages", type=Path, metavar="MESSAGES_NDJSON", help="saved Cucumber Messages NDJSON file")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("allure-results"),
        help="directory for Allure result and container files (default: allure-results)",
    )


def run_allure_conversion_command(arguments: argparse.Namespace) -> int:
    """Convert the supplied stream and report input/output errors to stderr."""
    try:
        convert_allure_messages(arguments.messages, arguments.output)
    except AllureConversionError as exc:
        print(f"cuke convert allure: {exc}", file=sys.stderr)
        return 2
    return 0


__all__ = ["configure_allure_conversion_parser", "run_allure_conversion_command"]
