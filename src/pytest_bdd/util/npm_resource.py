import subprocess
from functools import wraps
from itertools import chain
from pathlib import Path


def _check_subprocess(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            func(*args, **kwargs)
        except subprocess.CalledProcessError:
            return False
        else:
            return True

    return wrapper


def get_npm_root(*, global_install=False):
    command = "npm root -g" if global_install else "npm root"
    return subprocess.check_output(command, shell=True).decode("utf-8").strip()  # noqa:S602 intentional


@_check_subprocess
def check_npm():
    command = "npm --version"
    return subprocess.check_output(command, shell=True).decode("utf-8").strip()  # noqa:S602 intentional


@_check_subprocess
def check_npm_package(package_name, *, global_install=False):
    command = f'npm list -g "{package_name}"' if global_install else f"npm list {package_name}"
    return subprocess.check_output(command, shell=True).decode("utf-8").strip()  # noqa:S602 intentional


def find_resource(package_name, resource_path):
    # Check local node_modules
    local_npm_root = get_npm_root(global_install=False)
    local_files = Path(local_npm_root, package_name).glob(resource_path)

    # Check global node_modules
    global_npm_root = get_npm_root(global_install=True)
    global_files = Path(global_npm_root, package_name).glob(resource_path)

    return chain(local_files, global_files)
