"""Temporary-directory helpers for local test environments."""

import os
import tempfile
from pathlib import Path


def prefer_posix_temp_root() -> bool:
    """
    Use POSIX temp storage when WSL inherits a Windows temp root.

    Returns:
        True when environment variables were rewritten.

    """
    if os.name != "posix":
        return False

    posix_temp_root = Path("/tmp")  # noqa: S108
    if not posix_temp_root.is_dir():
        return False

    current_temp_root = Path(tempfile.gettempdir()).resolve()
    try:
        current_temp_root.relative_to("/mnt")
    except ValueError:
        return False

    temp_root = str(posix_temp_root)
    for env_name in ("TMPDIR", "TEMP", "TMP"):
        os.environ[env_name] = temp_root
    tempfile.tempdir = None
    return True
