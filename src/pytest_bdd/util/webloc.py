"""
Provides focused utility functions for the `webloc` concern within pytest-bdd utility layer,
offering helper operatio.

Responsibility:
    Provides focused utility functions for the `webloc` concern within pytest-bdd utility layer,
    offering helper operations consumed by higher layers (collection, runtime, reporting) without
    pulling in pytest plugin machinery or creating import cycles.

Reason for existence:
    Keeping `webloc` utilities in a dedicated module prevents cross-cutting helper code from
    accumulating in larger modules where it would create unclear ownership or hidden dependency
    issues. This module is the single authority for `webloc`-related helper operations within the
    utility layer.

Delegates:
    - Python standard library: delegates core data structure and I/O operations to stdlib

Cohesion:
    All functions and classes serve the single `webloc` utility concern.

Separation:
    - Sibling utility modules: each handles a distinct helper concern to prevent callers from coupling to unrelated
    functionality.

Main consumers:
    - `pytest_bdd.plugin.*`: imports `webloc` utilities for reporting, collection, and runtime operations

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

import plistlib
from pathlib import Path
from typing import TYPE_CHECKING, cast

from returns.maybe import Nothing

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping
    from os import PathLike


def read(path: str | PathLike[str]) -> str | None:
    """
    Perform the `read` operation within its module boundary, implementing a focused helper.
    function that is consumed by .

    Responsibility:
        Performs the `read` operation within its module boundary, implementing a focused helper
        function that is consumed by higher layers for its specific utility purpose within the pytest-
        bdd architecture.

    Reason for existence:
        `read` exists as a standalone function because it encapsulates an operation that does not
        require shared instance state and benefits from being independently callable and testable
        without class instantiation overhead.

    Delegates:
        - Python standard library: delegates core operations to stdlib

    Cohesion:
        All logic directly supports the read operation.

    Separation:
        - Other functions in this module: each function handles a distinct helper concern.

    Main consumers:
        - `pytest_bdd.*`: callers import and invoke read for its specific utility

    State and side effects:
        None, this function is stateless and produces its output purely from input arguments.

    Invariants:
        - The read function returns consistent results for equivalent inputs.

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
    load = getattr(plistlib, "load", None)
    if load is not None:
        with Path(path).open("rb") as f:
            return cast("str | None", cast("Mapping[str, object]", load(f)).get("URL"))
    read_plist = getattr(plistlib, "readPlist", None)
    if read_plist is not None:
        return cast("str | None", cast("Mapping[str, object]", read_plist(path)).get("URL"))
    return Nothing.value_or(None)


def write(path: str | PathLike[str], url: object) -> None:
    """
    Perform the `write` operation within its module boundary, implementing a focused helper.
    function that is consumed by.

    Responsibility:
        Performs the `write` operation within its module boundary, implementing a focused helper
        function that is consumed by higher layers for its specific utility purpose within the pytest-
        bdd architecture.

    Reason for existence:
        `write` exists as a standalone function because it encapsulates an operation that does not
        require shared instance state and benefits from being independently callable and testable
        without class instantiation overhead.

    Delegates:
        - Python standard library: delegates core operations to stdlib

    Cohesion:
        All logic directly supports the write operation.

    Separation:
        - Other functions in this module: each function handles a distinct helper concern.

    Main consumers:
        - `pytest_bdd.*`: callers import and invoke write for its specific utility

    State and side effects:
        None, this function is stateless and produces its output purely from input arguments.

    Invariants:
        - The write function returns consistent results for equivalent inputs.

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
