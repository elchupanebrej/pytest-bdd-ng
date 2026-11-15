"""Standalone command-line interface for converting Cucumber Messages to Allure."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import TYPE_CHECKING

from pytest_cuke.allure_conversion import AllureConversionError, convert_allure_messages
from pytest_cuke.model.report_presentation import resolve_report_policy
from pytest_cuke.report_policy_cli import configure_report_policy_parser

if TYPE_CHECKING:
    import argparse


def configure_allure_conversion_parser(parser: argparse.ArgumentParser) -> None:
    """Add arguments for ``cuke convert allure``."""
    parser.add_argument("messages", type=Path, metavar="MESSAGES_NDJSON", help="saved Cucumber Messages NDJSON file")
    configure_report_policy_parser(parser)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("allure-results"),
        help="directory for Allure result and container files (default: allure-results)",
    )


def run_allure_conversion_command(arguments: argparse.Namespace) -> int:
    """Convert the supplied stream and report input/output errors to stderr."""
    try:
        convert_allure_messages(
            arguments.messages,
            arguments.output,
            **resolve_report_policy(
                getattr(arguments, "report_policy", "normal"),
                xfail_as_failed=getattr(arguments, "xfail_as_failed", None),
                skip_as_failed=getattr(arguments, "skip_as_failed", None),
                tolerated_as_failed=getattr(arguments, "tolerated_as_failed", None),
                wip_as_failed=getattr(arguments, "wip_as_failed", None),
            ),
        )
    except AllureConversionError as exc:
        print(f"cuke convert allure: {exc}", file=sys.stderr)
        return 2
    return 0


__all__ = ["configure_allure_conversion_parser", "run_allure_conversion_command"]
