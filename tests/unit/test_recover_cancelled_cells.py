"""Runnable check for cancelled-cell recovery (`scripts/recover_cancelled_cells.py`).

Recovery may only re-run jobs the runner pool cancelled. Completed jobs must stay
untouched, and the aggregate proof is only accepted when it passes in the
recovery attempt.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from types import ModuleType, SimpleNamespace
from typing import Any

from pytest import MonkeyPatch, mark

pytestmark = mark.unit

SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "recover_cancelled_cells.py"

SUCCESS = {"status": "completed", "conclusion": "success"}
CANCELLED = {"status": "completed", "conclusion": "cancelled"}


def _load_module() -> ModuleType:
    spec = importlib.util.spec_from_file_location("recover_cancelled_cells", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class FakeGithub:
    """Serve run/job snapshots and record failed-jobs re-run requests."""

    def __init__(self, statuses: list[dict[str, Any]], snapshots: list[list[dict[str, Any]]]) -> None:
        self.statuses = statuses
        self.snapshots = snapshots
        self.status_calls = 0
        self.job_calls = 0
        self.reruns = 0

    def __call__(self, arguments: list[str]) -> str:
        endpoint, _, _ = arguments[1].partition("?")
        if endpoint.endswith("/jobs"):
            snapshot = self.snapshots[min(self.job_calls, len(self.snapshots) - 1)]
            self.job_calls += 1
            # Two pages prove that concatenated `gh api --paginate` output is decoded.
            half = max(1, len(snapshot) // 2)
            return json.dumps(snapshot[:half]) + json.dumps(snapshot[half:])
        if endpoint.endswith("/rerun-failed-jobs"):
            self.reruns += 1
            return "{}"
        status = self.statuses[min(self.status_calls, len(self.statuses) - 1)]
        self.status_calls += 1
        return json.dumps(status)


def _recover(module: ModuleType, fake: FakeGithub, monkeypatch: MonkeyPatch) -> tuple[int, list[str]]:
    monkeypatch.setattr(module.time, "sleep", lambda _seconds: None)
    logs: list[str] = []
    code = module.recover(
        module.GithubRun("owner/repo", 7, run_gh=fake),
        aggregate_job="aggregate-proof",
        timeout=60,
        poll_interval=0,
        log=logs.append,
    )
    return code, logs


def test_refuses_to_touch_a_run_that_is_still_running(monkeypatch: MonkeyPatch) -> None:
    fake = FakeGithub([{"status": "in_progress", "run_attempt": 1}], [[]])

    code, _logs = _recover(_load_module(), fake, monkeypatch)

    assert code == 2
    assert fake.reruns == 0
    assert fake.job_calls == 0


def test_reruns_cancelled_cells_then_requires_the_aggregate_proof(monkeypatch: MonkeyPatch) -> None:
    fake = FakeGithub(
        [
            {"status": "completed", "run_attempt": 1},
            {"status": "queued", "run_attempt": 2},
            {"status": "completed", "run_attempt": 2},
        ],
        [
            [
                {"id": 1, "name": "Full runtime matrix (cpython-311-linux / all)", **SUCCESS},
                {"id": 2, "name": "Full runtime matrix (cpython-311-macos / all)", **CANCELLED},
                {"id": 3, "name": "Full runtime matrix (graalpy-253-linux / all)", **SUCCESS},
                {"id": 4, "name": "aggregate-proof", **CANCELLED},
            ],
            [
                {"id": 11, "name": "Full runtime matrix (cpython-311-linux / all)", **SUCCESS},
                {"id": 12, "name": "Full runtime matrix (cpython-311-macos / all)", **SUCCESS},
                {"id": 13, "name": "Full runtime matrix (graalpy-253-linux / all)", **SUCCESS},
                {"id": 14, "name": "aggregate-proof", **SUCCESS},
            ],
        ],
    )

    code, logs = _recover(_load_module(), fake, monkeypatch)

    assert code == 0
    assert fake.reruns == 1
    assert any("cpython-311-macos" in line for line in logs)
    assert any("recovery complete" in line for line in logs)


def test_stops_when_a_recovered_cell_still_fails(monkeypatch: MonkeyPatch) -> None:
    fake = FakeGithub(
        [
            {"status": "completed", "run_attempt": 1},
            {"status": "completed", "run_attempt": 2},
        ],
        [
            [
                {"id": 2, "name": "Full runtime matrix (cpython-311-macos / all)", **CANCELLED},
                {"id": 4, "name": "aggregate-proof", **CANCELLED},
            ],
            [
                {
                    "id": 2,
                    "name": "Full runtime matrix (cpython-311-macos / all)",
                    "status": "completed",
                    "conclusion": "failure",
                },
                {"id": 4, "name": "aggregate-proof", **CANCELLED},
            ],
        ],
    )

    code, _logs = _recover(_load_module(), fake, monkeypatch)

    assert code == 1
    assert fake.reruns == 1


def test_retries_a_transient_api_failure(monkeypatch: MonkeyPatch) -> None:
    module = _load_module()
    outcomes = [
        SimpleNamespace(returncode=1, stderr="HTTP 502", stdout=""),
        SimpleNamespace(returncode=0, stderr="", stdout="ok"),
    ]
    monkeypatch.setattr(module.shutil, "which", lambda _name: "gh")
    monkeypatch.setattr(module.subprocess, "run", lambda *_args, **_kwargs: outcomes.pop(0))
    monkeypatch.setattr(module.time, "sleep", lambda _seconds: None)

    assert module._run_gh(["api", "repos/owner/repo"]) == "ok"


def test_does_nothing_without_cancelled_cells(monkeypatch: MonkeyPatch) -> None:
    fake = FakeGithub(
        [{"status": "completed", "run_attempt": 1}],
        [[{"id": 1, "name": "Full runtime matrix (cpython-311-linux / all)", **SUCCESS}]],
    )

    code, logs = _recover(_load_module(), fake, monkeypatch)

    assert code == 0
    assert fake.reruns == 0
    assert logs == ["recover: no cancelled cells to recover"]
