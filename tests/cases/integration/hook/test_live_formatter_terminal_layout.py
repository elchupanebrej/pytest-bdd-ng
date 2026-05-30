"""Provide test live formatter terminal layout helpers."""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess  # noqa: S404
import sys
from pathlib import Path

import pytest

from pytest_bdd.testing.cucumber_formatters import materialize_live_formatter_runtime

_ANSI_ESCAPE_RE = re.compile(r"\x1b\[[0-9;?]*[ -/]*[@-~]")


def _strip_ansi(text: str) -> str:
    return _ANSI_ESCAPE_RE.sub("", text).replace("\r", "")


def _resolve_node_executable() -> str:
    node_executable = shutil.which("node")
    if node_executable is None:
        pytest.skip("node executable is required for live formatter runtime checks")
    return node_executable


def _resolve_cucumber_node_path(node_executable: str) -> str:
    completed = subprocess.run(  # noqa: S603
        [node_executable, "-p", "require('path').dirname(require.resolve('@cucumber/cucumber/package.json'))"],
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        pytest.skip("@cucumber/cucumber is required for live formatter runtime checks")
    package_dir = Path(completed.stdout.strip())
    return str(package_dir.parent.parent)


def _run_node_renderer(
    *,
    tmp_path: Path,
    payload: dict[str, object],
    formatter_names: tuple[str, ...],
    columns: int,
    rows: int = 24,
) -> subprocess.CompletedProcess[str]:
    node_executable = _resolve_node_executable()
    script_path, formatter_specs = materialize_live_formatter_runtime(tmp_path, *formatter_names)
    payload["formatters"] = formatter_specs
    payload_path = tmp_path / "formatter_payload.json"
    payload_path.write_text(json.dumps(payload), encoding="utf-8")
    env = dict(os.environ)
    env["NODE_PATH"] = _resolve_cucumber_node_path(node_executable)
    env["PYTEST_BDD_LIVE_FORMATTER_STDOUT_ISATTY"] = "1"
    env["PYTEST_BDD_LIVE_FORMATTER_STDOUT_COLUMNS"] = str(columns)
    env["PYTEST_BDD_LIVE_FORMATTER_STDOUT_ROWS"] = str(rows)
    return subprocess.run(  # noqa: S603
        [node_executable, str(script_path), str(payload_path)],
        capture_output=True,
        text=True,
        check=False,
        cwd=str(tmp_path),
        env=env,
    )


def test_progress_bar_formatter_tracks_total_pickles_in_live_stream(tmp_path: Path) -> None:
    """Verify progress bar formatter tracks total pickles in live stream."""
    messages_path = tmp_path / "messages.ndjson"
    envelopes: list[dict[str, object]] = []
    for index in range(1, 6):
        envelopes.extend(
            [
                {"pickle": {"id": f"pickle-{index}", "uri": "demo.feature", "name": f"scenario-{index}", "steps": []}},
                {"testCase": {"id": f"test-case-{index}", "pickleId": f"pickle-{index}", "testSteps": []}},
            ],
        )
    envelopes.append({"testRunStarted": {"timestamp": {"seconds": 0, "nanos": 0}, "id": "run-1"}})
    for index in range(1, 6):
        envelopes.extend(
            [
                {
                    "testCaseStarted": {
                        "id": f"attempt-{index}",
                        "testCaseId": f"test-case-{index}",
                        "timestamp": {"seconds": index, "nanos": 0},
                    },
                },
                {
                    "testStepFinished": {
                        "testCaseStartedId": f"attempt-{index}",
                        "testStepId": f"step-{index}",
                        "testStepResult": {"status": "PASSED", "duration": {"seconds": 0, "nanos": 0}},
                    },
                },
                {
                    "testCaseFinished": {
                        "testCaseStartedId": f"attempt-{index}",
                        "timestamp": {"seconds": index, "nanos": 1},
                    },
                },
            ],
        )
    envelopes.append(
        {"testRunFinished": {"success": True, "timestamp": {"seconds": 9, "nanos": 0}, "testRunStartedId": "run-1"}},
    )
    messages_path.write_text("".join(json.dumps(envelope) + "\n" for envelope in envelopes), encoding="utf-8")

    result = _run_node_renderer(
        tmp_path=tmp_path,
        formatter_names=("progress-bar",),
        columns=80,
        payload={
            "cwd": str(tmp_path),
            "messagesPath": str(messages_path),
            "formatOptions": {},
            "supportCode": {"stepDefinitions": [], "hooks": [], "parameterTypes": []},
        },
    )

    assert result.returncode == 0, result.stderr
    normalized_stdout = _strip_ansi(result.stdout)
    assert re.findall(r"(\d+)/(\d+) scenarios", normalized_stdout) == [
        ("1", "5"),
        ("2", "5"),
        ("3", "5"),
        ("4", "5"),
        ("5", "5"),
    ]


def test_usage_formatter_wraps_to_terminal_width(tmp_path: Path) -> None:
    """Verify usage formatter wraps to terminal width."""
    feature_path = tmp_path / "demo.feature"
    feature_path.write_text(
        "Feature: demo\n  Scenario: one\n    Given pass\n\n  Scenario: two\n    Given fail\n",
        encoding="utf-8",
    )
    (tmp_path / "conftest.py").write_text(
        "from pytest_bdd import given\n"
        "@given('pass')\n"
        "def _pass():\n"
        "    return None\n"
        "@given('fail')\n"
        "def _fail():\n"
        "    raise RuntimeError('boom')\n",
        encoding="utf-8",
    )
    (tmp_path / "test_demo.py").write_text(
        "from pytest_bdd import scenarios\n\ntest_demo = scenarios('demo.feature')\n",
        encoding="utf-8",
    )
    messages_path = tmp_path / "messages.ndjson"
    pytest_run = subprocess.run(  # noqa: S603
        [sys.executable, "-m", "pytest", str(tmp_path / "test_demo.py"), "--messages-ndjson", str(messages_path)],
        capture_output=True,
        text=True,
        check=False,
        cwd=str(tmp_path),
        env={**os.environ, "PYTHONPATH": str(Path(__file__).resolve().parents[4] / "src")},
    )
    assert pytest_run.returncode == pytest.ExitCode.TESTS_FAILED
    assert messages_path.exists()

    result = _run_node_renderer(
        tmp_path=tmp_path,
        formatter_names=("usage",),
        columns=72,
        payload={
            "cwd": str(tmp_path),
            "messagesPath": str(messages_path),
            "formatOptions": {},
            "supportCode": {"stepDefinitions": [], "hooks": [], "parameterTypes": []},
        },
    )

    assert result.returncode == 0, result.stderr
    normalized_stdout = _strip_ansi(result.stdout)
    assert "Pattern / Text" in normalized_stdout
    assert max(len(line) for line in normalized_stdout.splitlines()) <= 72
    assert "file:demo.feature:3" in normalized_stdout
    assert "file:demo.feature:6" in normalized_stdout
