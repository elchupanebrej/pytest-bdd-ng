"""CLI adapter for Cucumber Messages schema synchronization."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import TYPE_CHECKING

from pytest_cuke.message_schema_sync import (
    MESSAGES_DISTRIBUTION,
    UPSTREAM_REPOSITORY,
    SchemaSyncError,
    sync_message_schemas,
)

if TYPE_CHECKING:
    import argparse


def configure_message_schema_parser(parser: argparse.ArgumentParser) -> None:
    """Add options for the ``sync messages schemas`` command."""
    parser.add_argument(
        "--schema-path",
        required=True,
        type=Path,
        help="output directory containing the vendored schema assets",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="report schema drift without modifying files",
    )
    parser.add_argument(
        "--source-dir",
        type=Path,
        help="read a local pinned schema fixture or checkout instead of downloading the pinned release",
    )


def run_message_schema_command(arguments: argparse.Namespace) -> int:
    """Run schema synchronization and print deterministic diagnostics."""
    try:
        result = sync_message_schemas(
            arguments.schema_path,
            check=arguments.check,
            source_dir=arguments.source_dir,
        )
    except SchemaSyncError as error:
        print(f"cuke sync messages schemas: error: {error}", file=sys.stderr)
        return 2

    print(
        f"{MESSAGES_DISTRIBUTION}=={result.contract_version} maps to {result.release.tag} "
        f"({result.release.commit}) from {UPSTREAM_REPOSITORY}"
    )
    drift = result.drift
    if drift.is_clean:
        print("Cucumber Messages schemas are up to date.")
        return 0

    for label, names in (("changed", drift.changed), ("missing", drift.missing), ("extra", drift.extra)):
        if names:
            print(f"{label}:")
            for name in names:
                print(f"  {name}")

    if arguments.check:
        print("schema drift detected; run `cuke sync messages schemas` to update the schema directory")
        return 1
    print(f"synchronized schema directory: {arguments.schema_path}")
    return 0


__all__ = ["configure_message_schema_parser", "run_message_schema_command"]
