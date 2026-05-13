"""Local interpreter bootstrap for WSL temp-directory stability."""

import os
import tempfile
from pathlib import Path


def _prefer_posix_temp_root() -> None:
    """Use POSIX temp storage when WSL inherits a Windows temp root."""
    if os.name != "posix":
        return

    posix_temp_root = Path("/tmp")  # noqa: S108
    if not posix_temp_root.is_dir():
        return

    current_temp_root = Path(tempfile.gettempdir()).resolve()
    try:
        current_temp_root.relative_to("/mnt")
    except ValueError:
        return

    temp_root = str(posix_temp_root)
    for env_name in ("TMPDIR", "TEMP", "TMP"):
        os.environ[env_name] = temp_root
    tempfile.tempdir = None


_prefer_posix_temp_root()
