"""Command-line options for report presentation."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import argparse


def configure_report_policy_parser(parser: argparse.ArgumentParser) -> None:
    """Add common report presentation options to a standalone command."""
    parser.add_argument("--report-policy", choices=("normal", "diagnostic"), default="normal")
    for category in ("xfail", "skip", "tolerated", "wip"):
        parser.add_argument(
            f"--{category}-as-failed",
            dest=f"{category}_as_failed",
            action="store_true",
            default=None,
            help=f"show {category} outcomes as failures in the report",
        )
        parser.add_argument(
            f"--no-{category}-as-failed",
            dest=f"{category}_as_failed",
            action="store_false",
            default=None,
            help=f"show {category} outcomes normally, overriding the report policy",
        )


