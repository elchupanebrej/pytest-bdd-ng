"""Steps and worker hooks for the isolated remote xdist project."""

from __future__ import annotations

import json
from importlib.metadata import version
import os
import platform
import socket
import time
from pathlib import Path

from pytest_cuke import given


@given("a passing remote scenario")
def passing_remote_scenario() -> None:
    worker_id = os.environ.get("PYTEST_XDIST_WORKER")
    mode_path = Path("/artifacts/remote-mode")
    mode = mode_path.read_text(encoding="utf-8").strip() if mode_path.is_file() else None
    assert worker_id, "the remote xdist BDD contract must run in an xdist worker"
    assert mode in {"socket", "via", "ssh"}, f"unexpected remote transport mode: {mode!r}"

    observation_dir = Path("/artifacts/observations")
    observation_dir.mkdir(parents=True, exist_ok=True)
    observation = {
        "worker_id": worker_id,
        "mode": mode,
        "host": socket.gethostname(),
        "runtime": platform.python_implementation(),
        "python": platform.python_version(),
        "pytest": version("pytest"),
        "pytest-xdist": version("pytest-xdist"),
    }
    temporary_path = observation_dir / f"{worker_id}.json.tmp"
    temporary_path.write_text(json.dumps(observation), encoding="utf-8")
    temporary_path.replace(observation_dir / f"{worker_id}.json")
    time.sleep(0.15)


def pytest_sessionfinish(session: object, exitstatus: int) -> None:
    del session, exitstatus
    crash_marker = Path("/artifacts/crash-worker")
    crash_worker = crash_marker.read_text(encoding="utf-8").strip() if crash_marker.is_file() else ""
    worker_id = os.environ.get("PYTEST_XDIST_WORKER", "")
    if crash_worker and worker_id == crash_worker:
        os._exit(86)
