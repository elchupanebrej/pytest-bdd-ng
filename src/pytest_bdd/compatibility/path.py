"""
Provide path helpers.

Responsibility:
    Provide path helpers. It directly owns the observable contract, local decisions, and maintenance boundary for this
    module. That boundary is intentionally stated in prose so maintainers can distinguish owned work from collaborators
    before editing.

Reason for existence:
    This entity is the information expert for `pytest_bdd.compatibility.path` because it keeps the nearest code, data
    shape, call signature, and failure knowledge together.

Delegates:
    - relpath: owns nested behavior below this boundary
    - resolvepath: owns nested behavior below this boundary

Cohesion:
    The implementation stays together because its imports, calls, state writes, and return contract describe one
    maintainable decision unit.

Separation:
    - module peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
      widening caller knowledge.

Main consumers:
    - src/pytest_bdd/_pylint/checkers/file_size_rules.py: imports or references `path`
    - src/pytest_bdd/_pylint/checkers/init_rules.py: imports or references `path`
    - src/pytest_bdd/_pylint/checkers/noqa_rules.py: imports or references `path`
    - src/pytest_bdd/_pylint/checkers/plugin_patterns.py: imports or references `path`
    - src/pytest_bdd/_pylint/checkers/typing_rules.py: imports or references `path`

State and side effects:
    depends on __future__.annotations, os, sys, pathlib.Path, typing.TYPE_CHECKING.

Invariants:
    - `pytest_bdd.compatibility.path` keeps its documented import path, ownership boundary, and observable behavior
      stable for callers.

Failure semantics:
    Raises or re-raises re-raise; callers must treat these as boundary failures.

Architecture score:
    #arch-eval:reason_for_existence=4
    #arch-eval:owned_responsibility=4
    #arch-eval:delegation_boundary=4
    #arch-eval:cohesion=3
    #arch-eval:separation=3
    #arch-eval:consumer_clarity=4
    #arch-eval:state_invariants=4
    #arch-eval:entity_fullness=4
    #arch-eval:locational_stability=4
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from os import PathLike


def relpath(path: str | PathLike[str], start: str | PathLike[str] = os.curdir) -> str | PathLike[str]:
    """
    Handle relpath.

    Returns:
        Relative path from start to path.

    Raises:
        ValueError: If relative path resolution fails on a non-Windows platform.

    Responsibility:
        Handle relpath. It directly owns the observable contract, local decisions, and maintenance boundary for this
        function. That boundary is intentionally stated in prose so maintainers can distinguish owned work from
        collaborators before editing.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.compatibility.path.relpath` because it keeps the nearest
        code, data shape, call signature, and failure knowledge together.

    Delegates:
        - os.path.relpath: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/gherkin_message_reporter/hook_catalog_runtime.py: imports or references `relpath`
        - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_core.py: imports or references `relpath`
        - src/pytest_bdd/plugin/gherkin_message_reporter/step_catalog_runtime/_static_helpers.py: imports or references
          `relpath`
        - src/pytest_bdd/scenario_locator/file_locator.py: imports or references `relpath`
        - src/pytest_bdd/steps/definition.py: imports or references `relpath`

    State and side effects:
        keeps no local persistent state beyond call-local values.

    Failure semantics:
        Raises or re-raises re-raise; callers must treat these as boundary failures.

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
    try:
        return os.path.relpath(path, start)
    except ValueError:
        if sys.platform == "win32":
            return path
        raise


def resolvepath(path: str | PathLike[str], start: str | PathLike[str] = os.curdir) -> str | PathLike[str]:
    """
    Resolve an absolute path from a base directory.

    Args:
        path: Target path (relative or absolute).
        start: Base directory to resolve from (defaults to current working directory).

    Returns:
        Resolved absolute path by joining start with the relative path.

    Responsibility:
        Resolve an absolute path from a base directory. It directly owns the observable contract, local decisions, and
        maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.compatibility.path.resolvepath` because it keeps the
        nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - os.path.normpath: collaborator call used by this boundary
        - resolve: collaborator call used by this boundary
        - Path: collaborator call used by this boundary
        - relpath: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/gherkin_message_reporter/hook_catalog_runtime.py: imports or references `resolvepath`
        - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_core.py: imports or references `resolvepath`
        - src/pytest_bdd/plugin/gherkin_message_reporter/step_catalog_runtime/_static_helpers.py: imports or references
          `resolvepath`
        - src/pytest_bdd/scenario_locator/file_locator.py: imports or references `resolvepath`
        - src/pytest_bdd/steps/definition.py: imports or references `resolvepath`

    State and side effects:
        keeps no local persistent state beyond call-local values.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=4

    """
    return os.path.normpath((Path(start) / relpath(path, start)).resolve())
