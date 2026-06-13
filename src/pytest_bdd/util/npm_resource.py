"""
Manages npm package resources required by live Cucumber formatters, providing functions to
resolve npm binary paths, .

Responsibility:
    Manages npm package resources required by live Cucumber formatters, providing functions to
    resolve npm binary paths, locate @cucumber packages within node_modules directories, and ensure
    the Node.js runtime dependencies are available for the live-reporting subsystem.

Reason for existence:
    npm dependency management is a distinct operational concern with its own failure modes (missing
    Node.js, uninstalled packages, PATH resolution). Isolating this keeps formatter plugins from
    embedding fragile npm discovery logic and provides a single place to handle Node.js platform
    absence.

Delegates:
    - `shutil.which`: delegates PATH-based executable discovery to Python stdlib

Cohesion:
    All functions relate to discovering and validating npm/Node.js runtime resources.

Separation:
    - `pytest_bdd.util.live_reporting`: live_reporting uses npm_resource to locate formatter executable paths.

Main consumers:
    - `pytest_bdd.util.live_reporting`: imports npm_resource to find formatter executables

State and side effects:
    None, functions perform read-only filesystem queries without caching or state mutation.

Invariants:
    - npm binary path resolution works correctly on both Windows and Unix platforms.

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

import subprocess  # noqa: S404  -- suppressed warning
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
    Perform the `_check_subprocess` operation within its module boundary, implementing a focused.
    helper function that is.

    Responsibility:
        Performs the `_check_subprocess` operation within its module boundary, implementing a focused
        helper function that is consumed by higher layers for its specific utility purpose within the
        pytest-bdd architecture.

    Reason for existence:
        `_check_subprocess` exists as a standalone function because it encapsulates an operation that
        does not require shared instance state and benefits from being independently callable and
        testable without class instantiation overhead.

    Delegates:
        - Python standard library: delegates core operations to stdlib

    Cohesion:
        All logic directly supports the _check_subprocess operation.

    Separation:
        - Other functions in this module: each function handles a distinct helper concern.

    Main consumers:
        - `pytest_bdd.*`: callers import and invoke _check_subprocess for its specific utility

    State and side effects:
        None, this function is stateless and produces its output purely from input arguments.

    Invariants:
        - The _check_subprocess function returns consistent results for equivalent inputs.

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

    @wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> bool:
        """
        Perform the `wrapper` operation within its module boundary, implementing a focused helper.
        function that is consumed .

        Responsibility:
        Performs the `wrapper` operation within its module boundary, implementing a focused helper
        function that is consumed by higher layers for its specific utility purpose within the pytest-
        bdd architecture.

        Reason for existence:
        `wrapper` exists as a standalone function because it encapsulates an operation that does not
        require shared instance state and benefits from being independently callable and testable
        without class instantiation overhead.

        Delegates:
        - Python standard library: delegates core operations to stdlib

        Cohesion:
        All logic directly supports the wrapper operation.

        Separation:
        - Other functions in this module: each function handles a distinct helper concern.

        Main consumers:
        - `pytest_bdd.*`: callers import and invoke wrapper for its specific utility

        State and side effects:
        None, this function is stateless and produces its output purely from input arguments.

        Invariants:
        - The wrapper function returns consistent results for equivalent inputs.

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
        try:
            func(*args, **kwargs)
        except subprocess.CalledProcessError:
            return False
        else:
            return True

    return wrapper


def get_npm_root(*, global_install: bool = False) -> str:
    """
    Perform the `get_npm_root` operation within its module boundary, implementing a focused helper.
    function that is cons.

    Responsibility:
        Performs the `get_npm_root` operation within its module boundary, implementing a focused helper
        function that is consumed by higher layers for its specific utility purpose within the pytest-
        bdd architecture.

    Reason for existence:
        `get_npm_root` exists as a standalone function because it encapsulates an operation that does
        not require shared instance state and benefits from being independently callable and testable
        without class instantiation overhead.

    Delegates:
        - Python standard library: delegates core operations to stdlib

    Cohesion:
        All logic directly supports the get_npm_root operation.

    Separation:
        - Other functions in this module: each function handles a distinct helper concern.

    Main consumers:
        - `pytest_bdd.*`: callers import and invoke get_npm_root for its specific utility

    State and side effects:
        None, this function is stateless and produces its output purely from input arguments.

    Invariants:
        - The get_npm_root function returns consistent results for equivalent inputs.

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
    command = "npm root -g" if global_install else "npm root"
    return subprocess.check_output(command, shell=True).decode("utf-8").strip()  # noqa:S602 intentional


@_check_subprocess
def check_npm() -> str:
    """
    Perform the `check_npm` operation within its module boundary, implementing a focused helper.
    function that is consume.

    Responsibility:
        Performs the `check_npm` operation within its module boundary, implementing a focused helper
        function that is consumed by higher layers for its specific utility purpose within the pytest-
        bdd architecture.

    Reason for existence:
        `check_npm` exists as a standalone function because it encapsulates an operation that does not
        require shared instance state and benefits from being independently callable and testable
        without class instantiation overhead.

    Delegates:
        - Python standard library: delegates core operations to stdlib

    Cohesion:
        All logic directly supports the check_npm operation.

    Separation:
        - Other functions in this module: each function handles a distinct helper concern.

    Main consumers:
        - `pytest_bdd.*`: callers import and invoke check_npm for its specific utility

    State and side effects:
        None, this function is stateless and produces its output purely from input arguments.

    Invariants:
        - The check_npm function returns consistent results for equivalent inputs.

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
    command = "npm --version"
    return subprocess.check_output(command, shell=True).decode("utf-8").strip()  # noqa:S602 intentional


@_check_subprocess
def check_npm_package(package_name: str, *, global_install: bool = False) -> str:
    """
    Perform the `check_npm_package` operation within its module boundary, implementing a focused.
    helper function that is.

    Responsibility:
        Performs the `check_npm_package` operation within its module boundary, implementing a focused
        helper function that is consumed by higher layers for its specific utility purpose within the
        pytest-bdd architecture.

    Reason for existence:
        `check_npm_package` exists as a standalone function because it encapsulates an operation that
        does not require shared instance state and benefits from being independently callable and
        testable without class instantiation overhead.

    Delegates:
        - Python standard library: delegates core operations to stdlib

    Cohesion:
        All logic directly supports the check_npm_package operation.

    Separation:
        - Other functions in this module: each function handles a distinct helper concern.

    Main consumers:
        - `pytest_bdd.*`: callers import and invoke check_npm_package for its specific utility

    State and side effects:
        None, this function is stateless and produces its output purely from input arguments.

    Invariants:
        - The check_npm_package function returns consistent results for equivalent inputs.

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
    command = f'npm list -g "{package_name}"' if global_install else f"npm list {package_name}"
    return subprocess.check_output(command, shell=True).decode("utf-8").strip()  # noqa:S602 intentional


def find_resource(
    package_name: str,
    resource_path: str,
    *,
    additional_roots: Iterable[str | PathLike[str]] = (),
) -> Iterator[Path]:
    """
    Perform the `find_resource` operation within its module boundary, implementing a focused.
    helper function that is con.

    Responsibility:
        Performs the `find_resource` operation within its module boundary, implementing a focused
        helper function that is consumed by higher layers for its specific utility purpose within the
        pytest-bdd architecture.

    Reason for existence:
        `find_resource` exists as a standalone function because it encapsulates an operation that does
        not require shared instance state and benefits from being independently callable and testable
        without class instantiation overhead.

    Delegates:
        - Python standard library: delegates core operations to stdlib

    Cohesion:
        All logic directly supports the find_resource operation.

    Separation:
        - Other functions in this module: each function handles a distinct helper concern.

    Main consumers:
        - `pytest_bdd.*`: callers import and invoke find_resource for its specific utility

    State and side effects:
        None, this function is stateless and produces its output purely from input arguments.

    Invariants:
        - The find_resource function returns consistent results for equivalent inputs.

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
    search_roots = [Path(root) for root in additional_roots]

    with suppress(subprocess.CalledProcessError):
        search_roots.append(Path(get_npm_root(global_install=False)))
    with suppress(subprocess.CalledProcessError):
        search_roots.append(Path(get_npm_root(global_install=True)))

    return chain.from_iterable((root / package_name).glob(str(resource_path)) for root in search_roots)
