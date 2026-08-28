from __future__ import annotations

import glob
import os
import subprocess
from functools import wraps
from itertools import chain
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator


def _check_subprocess(func: Callable[..., Any]) -> Callable[..., bool]:
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> bool:
        try:
            func(*args, **kwargs)
        except (subprocess.CalledProcessError, FileNotFoundError, OSError):
            return False
        else:
            return True

    return wrapper


def get_npm_root(global_install: bool = False) -> str:
    cmd = ["npm", "root", "-g"] if global_install else ["npm", "root"]
    return subprocess.check_output(cmd).decode("utf-8").strip()  # noqa: S603


@_check_subprocess
def check_npm() -> str:
    cmd = ["npm", "--version"]
    return subprocess.check_output(cmd).decode("utf-8").strip()  # noqa: S603


@_check_subprocess
def check_npm_package(package_name: str, global_install: bool = False) -> str:
    cmd = ["npm", "list", "-g", package_name] if global_install else ["npm", "list", package_name]
    return subprocess.check_output(cmd).decode("utf-8").strip()  # noqa: S603


def find_resource(package_name: str, resource_path: str) -> Iterator[str]:
    # Check local node_modules
    local_npm_root = get_npm_root(global_install=False)
    local_resource_path = os.path.join(local_npm_root, package_name, resource_path)
    local_files = glob.iglob(local_resource_path)

    # Check global node_modules
    global_npm_root = get_npm_root(global_install=True)
    global_resource_path = os.path.join(global_npm_root, package_name, resource_path)
    global_files = glob.iglob(global_resource_path)

    return chain(local_files, global_files)
