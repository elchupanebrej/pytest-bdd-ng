"""Command line support for standalone Cucumber formatter replay."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import TYPE_CHECKING

from pytest_cuke.formatter_api import FormatterSelection
from pytest_cuke.formatter_catalog import FormatterCatalogError, resolve_replay_formatter_requests
from pytest_cuke.formatter_replay import replay_messages
from pytest_cuke.formatter_runtime import FormatterRuntimeError
from pytest_cuke.model.report_presentation import resolve_report_policy
from pytest_cuke.report_policy_cli import configure_report_policy_parser

if TYPE_CHECKING:
    import argparse


def configure_formatter_replay_parser(parser: argparse.ArgumentParser) -> None:
    """Add arguments for ``cuke replay``."""
    parser.add_argument("messages", type=Path, metavar="MESSAGES_NDJSON", help="saved Cucumber Messages NDJSON file")
    configure_report_policy_parser(parser)
    parser.add_argument(
        "--formatter",
        action="append",
        required=True,
        metavar="NAME=DESTINATION",
        help="select an installed formatter and output path; use '-' to write to the terminal (repeatable)",
    )


def _selection(raw: str, *, root: Path) -> FormatterSelection:
    name, separator, destination = raw.partition("=")
    if not separator or not name or name != name.strip() or not destination:
        raise FormatterCatalogError(
            f"Invalid formatter selection {raw!r}; expected NAME=DESTINATION with non-empty values."
        )
    output_path = None if destination == "-" else Path(destination)
    return FormatterSelection(name=name, destination=output_path, working_directory=root)


def run_formatter_replay_command(arguments: argparse.Namespace) -> int:
    """Resolve and run selected formatters, reporting actionable errors to stderr."""
    root = Path.cwd().resolve()
    source = Path(arguments.messages)
    if not source.is_absolute():
        source = root / source
    source = source.resolve(strict=False)
    if not source.is_file():
        print(f"cuke replay: Messages NDJSON file does not exist: {source}", file=sys.stderr)
        return 2

    try:
        raw_selections = arguments.formatter
        if not isinstance(raw_selections, list):
            raise FormatterCatalogError("At least one --formatter NAME=DESTINATION selection is required.")
        selections = tuple(_selection(raw, root=root) for raw in raw_selections)
        requests = resolve_replay_formatter_requests(selections, root=root)
        replay_messages(
            source,
            requests,
            **resolve_report_policy(
                getattr(arguments, "report_policy", "normal"),
                xfail_as_failed=getattr(arguments, "xfail_as_failed", None),
                skip_as_failed=getattr(arguments, "skip_as_failed", None),
                tolerated_as_failed=getattr(arguments, "tolerated_as_failed", None),
                wip_as_failed=getattr(arguments, "wip_as_failed", None),
            ),
        )
    except (FormatterCatalogError, FormatterRuntimeError, OSError, ValueError) as error:
        print(f"cuke replay: {error}", file=sys.stderr)
        return 2
    return 0


__all__ = ["configure_formatter_replay_parser", "run_formatter_replay_command"]
