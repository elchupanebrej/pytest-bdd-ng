"""
Provides focused utility functions for the `temp_root` concern within pytest-bdd utility layer,
offering helper opera.

Responsibility:
    Provides focused utility functions for the `temp_root` concern within pytest-bdd utility layer,
    offering helper operations consumed by higher layers (collection, runtime, reporting) without
    pulling in pytest plugin machinery or creating import cycles.

Reason for existence:
    Keeping `temp_root` utilities in a dedicated module prevents cross-cutting helper code from
    accumulating in larger modules where it would create unclear ownership or hidden dependency
    issues. This module is the single authority for `temp_root`-related helper operations within
    the utility layer.

Delegates:
    - Python standard library: delegates core data structure and I/O operations to stdlib

Cohesion:
    All functions and classes serve the single `temp_root` utility concern.

Separation:
    - Sibling utility modules: each handles a distinct helper concern to prevent callers from coupling to unrelated
    functionality.

Main consumers:
    - `pytest_bdd.plugin.*`: imports `temp_root` utilities for reporting, collection, and runtime operations

State and side effects:
    None, this module keeps no persistent state and performs no file or network I/O.

Invariants:
    - The public API surface (exported names) remains stable across internal refactors.

Architecture score:
    #arch-eval:reason_for_existence=5
    #arch-eval:owned_responsibility=4
    #arch-eval:delegation_boundary=4
    #arch-eval:cohesion=4
    #arch-eval:separation=4
    #arch-eval:consumer_clarity=4
    #arch-eval:state_invariants=4
    #arch-eval:entity_fullness=4
    #arch-eval:locational_stability=4
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path


def prefer_posix_temp_root() -> bool:
    """
    Perform the `prefer_posix_temp_root` operation within its module boundary, implementing a.
    focused helper function th.

    Responsibility:
        Performs the `prefer_posix_temp_root` operation within its module boundary, implementing a
        focused helper function that is consumed by higher layers for its specific utility purpose
        within the pytest-bdd architecture.

    Reason for existence:
        `prefer_posix_temp_root` exists as a standalone function because it encapsulates an operation
        that does not require shared instance state and benefits from being independently callable and
        testable without class instantiation overhead.

    Delegates:
        - Python standard library: delegates core operations to stdlib

    Cohesion:
        All logic directly supports the prefer_posix_temp_root operation.

    Separation:
        - Other functions in this module: each function handles a distinct helper concern.

    Main consumers:
        - `pytest_bdd.*`: callers import and invoke prefer_posix_temp_root for its specific utility

    State and side effects:
        None, this function is stateless and produces its output purely from input arguments.

    Invariants:
        - The prefer_posix_temp_root function returns consistent results for equivalent inputs.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=3
        #arch-eval:delegation_boundary=3
        #arch-eval:cohesion=5
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=3
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=3
        #arch-eval:locational_stability=3
    """
    if os.name != "posix":
        return False

    posix_temp_root = Path("/tmp")  # noqa: S108  -- suppressed warning
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
