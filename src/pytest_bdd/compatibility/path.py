from __future__ import annotations

import os
import sys
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from os import PathLike


def relpath(path: str | PathLike[str], start: str | PathLike[str] = os.curdir) -> str | PathLike[str]:
    try:
        return os.path.relpath(path, start)
    except ValueError:
        if sys.platform == "win32":
            return path
        raise
