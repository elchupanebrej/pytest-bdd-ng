"""
Provide npm resource helpers.

Responsibility:
    Provide npm resource helpers. It directly owns the observable contract, local decisions, and maintenance boundary
    for this module. That boundary is intentionally stated in prose so maintainers can distinguish owned work from
    collaborators before editing.

Reason for existence:
    This entity is the information expert for `pytest_bdd.util.npm_resource` because it keeps the nearest code, data
    shape, call signature, and failure knowledge together.

Delegates:
    - _check_subprocess: owns nested behavior below this boundary
    - get_npm_root: owns nested behavior below this boundary
    - check_npm: owns nested behavior below this boundary
    - check_npm_package: owns nested behavior below this boundary
    - find_resource: owns nested behavior below this boundary

Cohesion:
    The implementation stays together because its imports, calls, state writes, and return contract describe one
    maintainable decision unit.

Separation:
    - module peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
      widening caller knowledge.

Main consumers:
    - src/pytest_bdd/plugin/gherkin_message_reporter/live_formatter_runner.py: imports or references `npm_resource`

State and side effects:
    mutates command, P, T, search_roots; depends on __future__.annotations, subprocess, contextlib.suppress,
    functools.wraps, itertools.chain.

Invariants:
    - `pytest_bdd.util.npm_resource` keeps its documented import path, ownership boundary, and observable behavior
      stable for callers.

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

import subprocess  # noqa: S404
from contextlib import suppress
from functools import wraps
from itertools import chain
from pathlib import Path
from typing import TYPE_CHECKING, ParamSpec, TypeVar

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable, Iterator
    from os import PathLike

P = ParamSpec("P")
T = TypeVar("T")


def _check_subprocess(func: Callable[P, T]) -> Callable[P, bool]:
    """
    Responsibility:
        Responsibility: Responsibility: `pytest_bdd.util.npm_resource._check_subprocess` owns documented function
        behavior. It directly owns the observable contract, local decisions, and maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.util.npm_resource._check_subprocess` because it keeps the
        nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - wrapper: owns nested behavior below this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/gherkin_message_reporter/live_formatter_runner.py: imports or references
          `_check_subprocess`

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
        #arch-eval:locational_stability=3
    """

    @wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> bool:
        """
        Responsibility:
            Responsibility: Responsibility: `pytest_bdd.util.npm_resource._check_subprocess.wrapper` owns documented
            function behavior. It directly owns the observable contract, local decisions, and maintenance boundary for
            this function.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.util.npm_resource._check_subprocess.wrapper` because
            it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - func: collaborator call used by this boundary
            - wraps: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/gherkin_message_reporter/live_formatter_runner.py: imports or references `wrapper`

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
            #arch-eval:locational_stability=3
        """
        try:
            func(*args, **kwargs)
        except subprocess.CalledProcessError:
            return False
        else:
            return True

    return wrapper


def get_npm_root(*, global_install: bool = False) -> str:
    """
    Get npm root directory path.

    Args:
        global_install: Whether to get global install root.

    Returns:
        Path to npm root directory.

    Responsibility:
        Get npm root directory path. It directly owns the observable contract, local decisions, and maintenance boundary
        for this function. That boundary is intentionally stated in prose so maintainers can distinguish owned work from
        collaborators before editing.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.util.npm_resource.get_npm_root` because it keeps the
        nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - subprocess.check_output.decode.strip: collaborator call used by this boundary
        - subprocess.check_output.decode: collaborator call used by this boundary
        - subprocess.check_output: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/gherkin_message_reporter/live_formatter_runner.py: imports or references `get_npm_root`

    State and side effects:
        mutates command.

    Invariants:
        - `pytest_bdd.util.npm_resource.get_npm_root` keeps its documented import path, ownership boundary, and
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
    command = "npm root -g" if global_install else "npm root"
    return subprocess.check_output(command, shell=True).decode("utf-8").strip()  # noqa:S602 intentional


@_check_subprocess
def check_npm() -> str:
    """
    Check if npm is available.

    Returns:
        NPM version string, or False if not available.

    Responsibility:
        Check if npm is available. It directly owns the observable contract, local decisions, and maintenance boundary
        for this function. That boundary is intentionally stated in prose so maintainers can distinguish owned work from
        collaborators before editing.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.util.npm_resource.check_npm` because it keeps the nearest
        code, data shape, call signature, and failure knowledge together.

    Delegates:
        - subprocess.check_output.decode.strip: collaborator call used by this boundary
        - subprocess.check_output.decode: collaborator call used by this boundary
        - subprocess.check_output: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/gherkin_message_reporter/live_formatter_runner.py: imports or references `check_npm`

    State and side effects:
        mutates command.

    Invariants:
        - `pytest_bdd.util.npm_resource.check_npm` keeps its documented import path, ownership boundary, and observable
          behavior stable for callers.

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
    command = "npm --version"
    return subprocess.check_output(command, shell=True).decode("utf-8").strip()  # noqa:S602 intentional


@_check_subprocess
def check_npm_package(package_name: str, *, global_install: bool = False) -> str:
    """
    Check if npm package is installed.

    Args:
        package_name: Name of the npm package.
        global_install: Whether to check global packages.

    Returns:
        Package info string, or False if not installed.

    Responsibility:
        Check if npm package is installed. It directly owns the observable contract, local decisions, and maintenance
        boundary for this function. That boundary is intentionally stated in prose so maintainers can distinguish owned
        work from collaborators before editing.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.util.npm_resource.check_npm_package` because it keeps the
        nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - subprocess.check_output.decode.strip: collaborator call used by this boundary
        - subprocess.check_output.decode: collaborator call used by this boundary
        - subprocess.check_output: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/gherkin_message_reporter/live_formatter_runner.py: imports or references
          `check_npm_package`

    State and side effects:
        mutates command.

    Invariants:
        - `pytest_bdd.util.npm_resource.check_npm_package` keeps its documented import path, ownership boundary, and
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
    command = f'npm list -g "{package_name}"' if global_install else f"npm list {package_name}"
    return subprocess.check_output(command, shell=True).decode("utf-8").strip()  # noqa:S602 intentional


def find_resource(
    package_name: str,
    resource_path: str,
    *,
    additional_roots: Iterable[str | PathLike[str]] = (),
) -> Iterator[Path]:
    """
    Find a resource in npm package directories.

    Args:
        package_name: NPM package name.
        resource_path: Resource path to search for.
        additional_roots: Additional search roots.

    Returns:
        Iterator of found paths.

    Responsibility:
        Find a resource in npm package directories. It directly owns the observable contract, local decisions, and
        maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.util.npm_resource.find_resource` because it keeps the
        nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - Path: collaborator call used by this boundary
        - suppress: collaborator call used by this boundary
        - search_roots.append: collaborator call used by this boundary
        - get_npm_root: collaborator call used by this boundary
        - chain.from_iterable: collaborator call used by this boundary
        - glob: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/gherkin_message_reporter/live_formatter_runner.py: imports or references `find_resource`

    State and side effects:
        mutates search_roots.

    Invariants:
        - `pytest_bdd.util.npm_resource.find_resource` keeps its documented import path, ownership boundary, and
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
    search_roots = [Path(root) for root in additional_roots]

    with suppress(subprocess.CalledProcessError):
        search_roots.append(Path(get_npm_root(global_install=False)))
    with suppress(subprocess.CalledProcessError):
        search_roots.append(Path(get_npm_root(global_install=True)))

    return chain.from_iterable((root / package_name).glob(str(resource_path)) for root in search_roots)
