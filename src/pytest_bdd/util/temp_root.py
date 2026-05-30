r"""
Temporary-directory root normalisation for WSL (Windows Subsystem for Linux).

Background
----------
When a pytest session is launched from a Windows terminal that has sourced a
WSL shell (e.g. ``wt.exe`` → ``wsl`` → ``uv run pytest``), the child process
inherits the Windows environment block.  That block typically contains::

    TEMP=C:\\Users\\<user>\\AppData\\Local\\Temp
    TMP=C:\\Users\\<user>\\AppData\\Local\\Temp
    TMPDIR=(unset or same Windows path)

Python's :func:`tempfile.gettempdir` resolves these environment variables first
and therefore returns a path under ``/mnt/c/...`` inside the WSL filesystem.
Paths on the 9P-mounted Windows filesystem (``/mnt/...``) have two important
deficiencies compared to native POSIX storage:

* **Performance** - every read/write crosses the 9P virtio boundary, adding
  several milliseconds of latency per operation.  Pytest's pytester fixture,
  ``tmp_path``, and internal cache writes all use ``tempfile``; with hundreds of
  test-generated temp directories the overhead is measurable.
* **Reliability** - some POSIX locking primitives (``fcntl``, ``flock``) are not
  supported or behave differently on 9P mounts, causing intermittent failures in
  tests that rely on ``filelock`` or ``pytest-xdist`` worker barriers.

Fix
---
:func:`prefer_posix_temp_root` is called from
``pytest_bdd.plugin.scenario_test_collector.entrypoint.pytest_load_initial_conftests``,
which is the earliest pytest hook that fires before capture opens temp files or
the pytester fixture allocates directories.  The function rewrites
``TMPDIR``/``TEMP``/``TMP`` to ``/tmp`` and resets :attr:`tempfile.tempdir` so
that all subsequent :func:`tempfile.gettempdir` calls return the native POSIX
path for the remainder of the process lifetime.

The fix is intentionally **idempotent and no-op on non-WSL environments**:

* On Windows (``os.name == 'nt'``) it returns immediately - Windows has no
  ``/tmp``.
* On native Linux / macOS the inherited temp path is already under a POSIX
  root, so ``current_temp_root.relative_to("/mnt")`` raises :exc:`ValueError`
  and the function exits without touching anything.
* Inside WSL with a Windows-inherited temp path the ``/mnt/`` prefix check
  succeeds and the rewrite proceeds.
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path


def prefer_posix_temp_root() -> bool:
    """
    Redirect temp-file creation from an inherited Windows path to native ``/tmp``.

    Must be called before any code that invokes :func:`tempfile.gettempdir`,
    including pytest's ``tmp_path`` fixture allocation, pytester setup, and
    ``filelock``-backed xdist worker barriers.

    Returns:
        ``True`` when the environment was rewritten (WSL with Windows temp
        root detected); ``False`` when no action was needed.

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
