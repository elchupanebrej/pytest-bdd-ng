from __future__ import annotations

import os
import tempfile
from pathlib import Path


def prefer_posix_temp_root() -> bool:
    if os.name != "posix" or not (posix_temp_root := Path("/tmp")).is_dir():  # noqa: S108
        return False
    try:
        Path(tempfile.gettempdir()).resolve().relative_to("/mnt")
    except ValueError:
        return False
    for env_name in ("TMPDIR", "TEMP", "TMP"):
        os.environ[env_name] = str(posix_temp_root)
    tempfile.tempdir = None
    return True
