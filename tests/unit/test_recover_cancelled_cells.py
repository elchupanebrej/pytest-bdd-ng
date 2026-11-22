"""Runnable check for cancelled-cell recovery (`scripts/recover_cancelled_cells.py`).

Recovery may only re-run jobs the runner pool cancelled. Completed, failed, and
in-progress jobs must stay untouched, and the aggregate proof is re-run only
after every recovered cell passed.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from types import ModuleType
from typing import Any

from pytest import MonkeyPatch, mark

pytestmark = mark.unit

SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "recover_cancelled_cells.py"

SUCCESS = {"status": "completed", "conclusion": "success"}
CANCELLED = {"status": "completed", "conclusion": "cancelled"}
IN_PROGRESS = {"status": "in_progress", "conclusion": None}


def _load_module() -> ModuleType:
    spec = importlib.util.spec_from_file_location("recover_cancelled_cells", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class FakeGithub:
    """Serve run/job snapshots and record job re-run requests."""

    def __init__(self, run_status: str, snapshots: list[list[dict[str, Any]]]) -> None:
        self.run_status = run_status
        self.snapshots = snapshots
        self.calls = 0
        self.reruns: list[int] = []

    def __call__(self, arguments: list[str]) -> str:
        endpoint, _, _ = arguments[1].partition("?")
        if endpoint.endswith("/jobs"):
            snapshot = self.snapshots[min(self.calls, len(self.snapshots) - 1)]
            self.calls += 1
            # Two pages prove that concatenated `gh api --paginate` output is decoded.
            half = max(1, len(snapshot) // 2)
            return json.dumps(snapshot[:half]) + json.dumps(snapshot[half:])
        if endpoint.endswith("/rerun"):
            self.reruns.append(int(endpoint.split("/")[-2]))
            return "{}"
        return json.dumps({"id": 7, "status": self.run_status})


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
    fake = FakeGithub("in_progress", [[]])

    code, _logs = _recover(_load_module(), fake, monkeypatch)

    assert code == 2
    assert fake.reruns == []
    assert fake.calls == 0


def test_reruns_only_cancelled_cells_then_the_aggregate_proof(monkeypatch: MonkeyPatch) -> None:
    fake = FakeGithub(
        "completed",
        [
            [
                {"id": 1, "name": "Full runtime matrix (cpython-311-linux / all)", **SUCCESS},
                {"id": 2, "name": "Full runtime matrix (cpython-311-macos / all)", **CANCELLED},
                {"id": 3, "name": "Full runtime matrix (graalpy-253-linux / all)", **IN_PROGRESS},
                {"id": 4, "name": "aggregate-proof", **CANCELLED},
            ],
            [
                {"id": 1, "name": "Full runtime matrix (cpython-311-linux / all)", **SUCCESS},
                {"id": 2, "name": "Full runtime matrix (cpython-311-macos / all)", **IN_PROGRESS},
                {"id": 3, "name": "Full runtime matrix (graalpy-253-linux / all)", **IN_PROGRESS},
                {"id": 4, "name": "aggregate-proof", **CANCELLED},
            ],
            [
                {"id": 1, "name": "Full runtime matrix (cpython-311-linux / all)", **SUCCESS},
                {"id": 2, "name": "Full runtime matrix (cpython-311-macos / all)", **SUCCESS},
                {"id": 3, "name": "Full runtime matrix (graalpy-253-linux / all)", **SUCCESS},
                {"id": 4, "name": "aggregate-proof", **CANCELLED},
            ],
            [
                {"id": 1, "name": "Full runtime matrix (cpython-311-linux / all)", **SUCCESS},
                {"id": 2, "name": "Full runtime matrix (cpython-311-macos / all)", **SUCCESS},
                {"id": 3, "name": "Full runtime matrix (graalpy-253-linux / all)", **SUCCESS},
                {"id": 4, "name": "aggregate-proof", **IN_PROGRESS},
            ],
            [
                {"id": 1, "name": "Full runtime matrix (cpython-311-linux / all)", **SUCCESS},
                {"id": 2, "name": "Full runtime matrix (cpython-311-macos / all)", **SUCCESS},
                {"id": 3, "name": "Full runtime matrix (graalpy-253-linux / all)", **SUCCESS},
                {"id": 4, "name": "aggregate-proof", **SUCCESS},
            ],
        ],
    )

    code, logs = _recover(_load_module(), fake, monkeypatch)

    assert code == 0
    assert fake.reruns == [2, 4]
    assert any("cpython-311-macos" in line for line in logs)
    assert any("aggregate proof" in line for line in logs)


def test_stops_when_a_recovered_cell_still_fails(monkeypatch: MonkeyPatch) -> None:
    fake = FakeGithub(
        "completed",
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
    assert fake.reruns == [2]
