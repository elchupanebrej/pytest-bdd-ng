"""Provide npm resource helpers."""

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
    @wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> bool:
        try:
            func(*args, **kwargs)
        except subprocess.CalledProcessError:
            return False
        else:
            return True

    return wrapper


def get_npm_root(*, global_install: bool = False) -> str:
    """Return npm root."""
    command = "npm root -g" if global_install else "npm root"
    return subprocess.check_output(command, shell=True).decode("utf-8").strip()  # noqa:S602 intentional


@_check_subprocess
def check_npm() -> str:
    """Check npm."""
    command = "npm --version"
    return subprocess.check_output(command, shell=True).decode("utf-8").strip()  # noqa:S602 intentional


@_check_subprocess
def check_npm_package(package_name: str, *, global_install: bool = False) -> str:
    """Check npm package."""
    command = f'npm list -g "{package_name}"' if global_install else f"npm list {package_name}"
    return subprocess.check_output(command, shell=True).decode("utf-8").strip()  # noqa:S602 intentional


def find_resource(
    package_name: str,
    resource_path: str,
    *,
    additional_roots: Iterable[str | PathLike[str]] = (),
) -> Iterator[Path]:
    """Find resource."""
    search_roots = [Path(root) for root in additional_roots]

    with suppress(subprocess.CalledProcessError):
        search_roots.append(Path(get_npm_root(global_install=False)))
    with suppress(subprocess.CalledProcessError):
        search_roots.append(Path(get_npm_root(global_install=True)))

    return chain.from_iterable((root / package_name).glob(str(resource_path)) for root in search_roots)
