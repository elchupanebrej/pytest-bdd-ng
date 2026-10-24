from __future__ import annotations

import plistlib
from pathlib import Path
from typing import TYPE_CHECKING, cast

if TYPE_CHECKING:
    from os import PathLike


def read(path: str | PathLike[str]) -> str | None:
    try:
        with Path(path).open("rb") as f:
            data = plistlib.load(f)
            return cast("str | None", data.get("URL"))
    except Exception:
        return None


def write(path: str | PathLike[str], url: object) -> None:
    data = {"URL": str(url)}
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("wb") as f:
        plistlib.dump(data, f)
