"""Request and option helpers for code generation."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import py

    from pytest_bdd.compatibility.pytest import Config, Session


def check_existence(file_name: str) -> Path:
    """
    Check file or directory name for existence.

    Args:
        file_name: File or directory name.

    Returns:
        Path object if exists.

    Raises:
        argparse.ArgumentTypeError: If the file or directory does not exist.

    """
    if not Path(file_name).exists():
        msg = f"{file_name} is an invalid file or directory name"
        raise argparse.ArgumentTypeError(msg)
    return Path(file_name)


def validate_feature_option(config: Config, session: Session, tw: py.io.TerminalWriter) -> bool:
    """
    Validate if the --feature parameter is provided.

    Returns:
        True if valid, False otherwise.

    """
    if config.option.features is None:
        tw.line("The --feature parameter is required.", red=True)
        session.exitstatus = 100
        return False
    return True
