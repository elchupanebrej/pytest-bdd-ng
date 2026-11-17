"""Steps and worker hooks for the isolated remote xdist project."""

from __future__ import annotations

import json
from importlib.metadata import version
import os
import platform
import socket
import time
from pathlib import Path

import pytest

from pytest_cuke import given, parsers


def _remote_mode() -> str:
    mode_path = Path("/artifacts/remote-mode")
    mode = mode_path.read_text(encoding="utf-8").strip() if mode_path.is_file() else ""
    assert mode in {"socket", "via", "ssh"}, f"unexpected remote transport mode: {mode!r}"
    return mode


@given("a passing remote scenario")
def passing_remote_scenario() -> None:
    worker_id = os.environ.get("PYTEST_XDIST_WORKER")
    mode = _remote_mode()
    assert worker_id, "the remote xdist BDD contract must run in an xdist worker"

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


def _record_group_event(group: str, request: pytest.FixtureRequest) -> None:
    worker_id = os.environ.get("PYTEST_XDIST_WORKER", "")
    assert worker_id, "the grouped remote contract must run in an xdist worker"
    if request.config.getini("cuke_test_group_order"):
        assigned = {marker.name for marker in request.node.iter_markers()}
        assert group in assigned, f"the group barrier assigned {sorted(assigned)} instead of {group!r}"
    event = {
        "worker": worker_id,
        "host": socket.gethostname(),
        "group": group,
        "mode": _remote_mode(),
        "nodeid": request.node.nodeid,
        # CLOCK_MONOTONIC is kernel-wide on Linux, so these timestamps order events across containers.
        "timestamp_ns": time.monotonic_ns(),
        "barrier_state_dir": Path(".pytest_cache/pytest-cuke-test-groups").exists(),
    }
    event_directory = Path("/artifacts/observations/groups")
    event_directory.mkdir(parents=True, exist_ok=True)
    event_path = event_directory / f"{worker_id}-{os.getpid()}-{event['timestamp_ns']}.json"
    event_path.write_text(json.dumps(event), encoding="utf-8")
    time.sleep(0.2)


@given(parsers.parse('a grouped remote scenario in group "{group}"'))
def grouped_remote_scenario(group: str, request: pytest.FixtureRequest) -> None:
    _record_group_event(group, request)


@given(parsers.parse('a grouped remote scenario that exits its worker in group "{group}"'))
def grouped_remote_scenario_that_exits(group: str, request: pytest.FixtureRequest) -> None:
    if Path("/artifacts/group-crash").is_file():
        os._exit(86)
    _record_group_event(group, request)


def pytest_sessionfinish(session: object, exitstatus: int) -> None:
    del session, exitstatus
    crash_marker = Path("/artifacts/crash-worker")
    crash_worker = crash_marker.read_text(encoding="utf-8").strip() if crash_marker.is_file() else ""
    worker_id = os.environ.get("PYTEST_XDIST_WORKER", "")
    if crash_worker and worker_id == crash_worker:
        os._exit(86)
