"""Provide webloc helpers."""

from __future__ import annotations

import plistlib
from pathlib import Path
from typing import TYPE_CHECKING, cast

from returns.maybe import Nothing

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping
    from os import PathLike


def read(path: str | PathLike[str]) -> str | None:
    """
    Read URL from a .webloc file.

    Args:
        path: Path to the .webloc file.

    Returns:
        URL string or None if not found.

    """
    load = getattr(plistlib, "load", None)
    if load is not None:
        with Path(path).open("rb") as f:
            return cast("str | None", cast("Mapping[str, object]", load(f)).get("URL"))
    read_plist = getattr(plistlib, "readPlist", None)
    if read_plist is not None:
        return cast("str | None", cast("Mapping[str, object]", read_plist(path)).get("URL"))
    return Nothing.value_or(None)


def write(path: str | PathLike[str], url: object) -> None:
    """Write url to webloc file."""
    data = {"URL": str(url)}
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    dump = getattr(plistlib, "dump", None)
    if dump is not None:
        with Path(path).open("wb") as f:
            cast("Callable[[Mapping[str, object], object], object]", dump)(data, f)
        return
    write_plist = getattr(plistlib, "writePlist", None)
    if write_plist is not None:
        cast("Callable[[Mapping[str, object], object], object]", write_plist)(data, path)
