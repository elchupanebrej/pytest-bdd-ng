"""Provide path helpers."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from os import PathLike


def relpath(path: str | PathLike[str], start: str | PathLike[str] = os.curdir) -> str | PathLike[str]:
    """
    Handle relpath.

    Returns:
        Relative path from start to path.

    Raises:
        ValueError: If relative path resolution fails on a non-Windows platform.

    """
    try:
        return os.path.relpath(path, start)
    except ValueError:
        if sys.platform == "win32":
            return path
        raise


def resolvepath(path: str | PathLike[str], start: str | PathLike[str] = os.curdir) -> str | PathLike[str]:
    """
    Resolve an absolute path from a base directory.

    Args:
        path: Target path (relative or absolute).
        start: Base directory to resolve from (defaults to current working directory).

    Returns:
        Resolved absolute path by joining start with the relative path.

    """
    return os.path.normpath((Path(start) / relpath(path, start)).resolve())
