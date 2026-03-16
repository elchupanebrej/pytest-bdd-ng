from __future__ import annotations

import shutil
import subprocess  # noqa: S404
from functools import lru_cache

import pytest


@lru_cache(maxsize=1)
def docker_daemon_available() -> bool:
    docker_bin = shutil.which("docker")
    if docker_bin is None:
        return False
    result = subprocess.run(  # noqa: S603
        [docker_bin, "info"],
        check=False,
        capture_output=True,
        text=True,
    )
    return result.returncode == 0


def require_docker_daemon() -> None:
    if not docker_daemon_available():
        pytest.skip("Docker is unavailable.")
