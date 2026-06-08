"""
Provide webloc helpers.

Responsibility:
    Provide webloc helpers. It directly owns the observable contract, local decisions, and maintenance boundary for this
    module. That boundary is intentionally stated in prose so maintainers can distinguish owned work from collaborators
    before editing.

Reason for existence:
    This entity is the information expert for `pytest_bdd.util.webloc` because it keeps the nearest code, data shape,
    call signature, and failure knowledge together.

Delegates:
    - read: owns nested behavior below this boundary
    - write: owns nested behavior below this boundary

Cohesion:
    The implementation stays together because its imports, calls, state writes, and return contract describe one
    maintainable decision unit.

Separation:
    - module peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
      widening caller knowledge.

Main consumers:
    - src/pytest_bdd/collector.py: imports or references `webloc`
    - src/pytest_bdd/mimetype.py: imports or references `webloc`

State and side effects:
    mutates load, read_plist, data, dump, write_plist; depends on __future__.annotations, plistlib, pathlib.Path,
    typing.TYPE_CHECKING, typing.cast.

Invariants:
    - `pytest_bdd.util.webloc` keeps its documented import path, ownership boundary, and observable behavior stable for
      callers.

Architecture score:
    #arch-eval:reason_for_existence=4
    #arch-eval:owned_responsibility=4
    #arch-eval:delegation_boundary=4
    #arch-eval:cohesion=3
    #arch-eval:separation=3
    #arch-eval:consumer_clarity=4
    #arch-eval:state_invariants=4
    #arch-eval:entity_fullness=4
    #arch-eval:locational_stability=3
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
    Read URL from a .webloc file.

    Args:
        path: Path to the .webloc file.

    Returns:
        URL string or None if not found.

    Responsibility:
        Read URL from a .webloc file. It directly owns the observable contract, local decisions, and maintenance
        boundary for this function. That boundary is intentionally stated in prose so maintainers can distinguish owned
        work from collaborators before editing.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.util.webloc.read` because it keeps the nearest code, data
        shape, call signature, and failure knowledge together.

    Delegates:
        - cast: collaborator call used by this boundary
        - getattr: collaborator call used by this boundary
        - cast.get: collaborator call used by this boundary
        - Path.open: collaborator call used by this boundary
        - Path: collaborator call used by this boundary
        - load: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/collector.py: imports or references `read`
        - src/pytest_bdd/collector_batch.py: imports or references `read`
        - src/pytest_bdd/plugin/gherkin_message_reporter/attachment_runtime.py: imports or references `read`
        - src/pytest_bdd/plugin/gherkin_message_reporter/stream_relay.py: imports or references `read`
        - src/pytest_bdd/plugin/struct_bdd/parser.py: imports or references `read`

    State and side effects:
        mutates load, read_plist.

    Invariants:
        - `pytest_bdd.util.webloc.read` keeps its documented import path, ownership boundary, and observable behavior
          stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=4

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
    Write url to webloc file.

    Responsibility:
        Write url to webloc file. It directly owns the observable contract, local decisions, and maintenance boundary
        for this function. That boundary is intentionally stated in prose so maintainers can distinguish owned work from
        collaborators before editing.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.util.webloc.write` because it keeps the nearest code, data
        shape, call signature, and failure knowledge together.

    Delegates:
        - cast: collaborator call used by this boundary
        - Path: collaborator call used by this boundary
        - getattr: collaborator call used by this boundary
        - str: collaborator call used by this boundary
        - Path.parent.mkdir: collaborator call used by this boundary
        - Path.open: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/collector.py: imports or references `write`
        - src/pytest_bdd/plugin/code_generator/plugin.py: imports or references `write`
        - src/pytest_bdd/plugin/code_generator/rendering.py: imports or references `write`
        - src/pytest_bdd/plugin/debug_mcp/discovery.py: imports or references `write`
        - src/pytest_bdd/plugin/debug_mcp/sidecar.py: imports or references `write`

    State and side effects:
        mutates data, dump, write_plist.

    Invariants:
        - `pytest_bdd.util.webloc.write` keeps its documented import path, ownership boundary, and observable behavior
          stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=4
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
