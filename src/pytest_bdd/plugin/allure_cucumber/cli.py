"""CLI entry point for allure-cucumber converter."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .converter import convert


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """
    Parse command-line arguments.

    Returns:
        Parsed arguments namespace.

    """
    parser = argparse.ArgumentParser(
        description="Convert Cucumber Messages NDJSON to Allure3 JSON results",
    )
    parser.add_argument(
        "messages_ndjson",
        type=Path,
        help="Path to Cucumber Messages NDJSON file.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("allure-results"),
        help="Output directory for Allure result JSON files.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """
    Run the allure-cucumber converter.

    Returns:
        Exit code (0 for success, 1 for failure).

    """
    args = parse_args(argv)
    messages_path = args.messages_ndjson
    if not messages_path.is_absolute():
        messages_path = Path.cwd().resolve() / messages_path
    if not messages_path.exists():
        _emit_error(f"Messages NDJSON file was not found: {messages_path}")
        return 1

    try:
        convert(messages_path, args.output)
    except (OSError, ValueError) as exc:
        _emit_error(f"Conversion failed: {exc}")
        return 1

    return 0


def _emit_error(message: str) -> None:
    """Emit error message to stderr."""
    sys.stderr.write(message)
    sys.stderr.write("\n")


if __name__ == "__main__":
    raise SystemExit(main())
