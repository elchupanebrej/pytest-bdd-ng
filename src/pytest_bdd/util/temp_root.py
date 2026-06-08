"""
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

Responsibility:
    Temporary-directory root normalisation for WSL (Windows Subsystem for Linux). It directly owns the observable
    contract, local decisions, and maintenance boundary for this module.

Reason for existence:
    This entity is the information expert for `pytest_bdd.util.temp_root` because it keeps the nearest code, data shape,
    call signature, and failure knowledge together.

Delegates:
    - prefer_posix_temp_root: owns nested behavior below this boundary

Cohesion:
    The implementation stays together because its imports, calls, state writes, and return contract describe one
    maintainable decision unit.

Separation:
    - module peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
      widening caller knowledge.

Main consumers:
    - src/pytest_bdd/plugin/scenario_test_collector/entrypoint.py: imports or references `temp_root`

State and side effects:
    mutates posix_temp_root, current_temp_root, temp_root, tempfile.tempdir; depends on __future__.annotations, os,
    tempfile, pathlib.Path.

Invariants:
    - `pytest_bdd.util.temp_root` keeps its documented import path, ownership boundary, and observable behavior stable
      for callers.

Architecture score:
    #arch-eval:reason_for_existence=4
    #arch-eval:owned_responsibility=4
    #arch-eval:delegation_boundary=4
    #arch-eval:cohesion=3
    #arch-eval:separation=3
    #arch-eval:consumer_clarity=4
    #arch-eval:state_invariants=4
    #arch-eval:entity_fullness=3
    #arch-eval:locational_stability=3
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

    Responsibility:
        Redirect temp-file creation from an inherited Windows path to native ``/tmp``. It directly owns the observable
        contract, local decisions, and maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.util.temp_root.prefer_posix_temp_root` because it keeps
        the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - Path: collaborator call used by this boundary
        - posix_temp_root.is_dir: collaborator call used by this boundary
        - Path.resolve: collaborator call used by this boundary
        - tempfile.gettempdir: collaborator call used by this boundary
        - current_temp_root.relative_to: collaborator call used by this boundary
        - str: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/scenario_test_collector/entrypoint.py: imports or references `prefer_posix_temp_root`

    State and side effects:
        mutates posix_temp_root, current_temp_root, temp_root, tempfile.tempdir.

    Invariants:
        - `pytest_bdd.util.temp_root.prefer_posix_temp_root` keeps its documented import path, ownership boundary, and
          observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=3

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
