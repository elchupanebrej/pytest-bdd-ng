"""Render real pytest Messages through the pinned official Node formatters."""

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

pytestmark = pytest.mark.integration

_SELECTORS = ("summary", "progress", "progress-bar", "snippets", "pretty", "usage", "usage-json")
_PACKAGES = {"@cucumber/cucumber": "13.3.0", "@cucumber/pretty-formatter": "4.0.2"}


@pytest.fixture(scope="module")
def node_root(tmp_path_factory):
    if shutil.which("node") is None or shutil.which("npm") is None:
        pytest.skip("real built-in replay consumers require Node.js and npm")
    configured = os.environ.get("PYTEST_CUKE_REPLAY_NODE_ROOT")
    root = Path(configured) if configured else tmp_path_factory.mktemp("replay-node")
    if not configured:
        (root / "package.json").write_text(
            json.dumps({"private": True, "type": "module", "dependencies": _PACKAGES}), encoding="utf-8"
        )
        install = subprocess.run(
            [shutil.which("npm"), "install", "--no-audit", "--no-fund"],
            cwd=root,
            capture_output=True,
            text=True,
            timeout=180,
            check=False,
        )
        assert install.returncode == 0, install.stdout + install.stderr
    for name, version in _PACKAGES.items():
        metadata = json.loads((root / "node_modules" / name / "package.json").read_text(encoding="utf-8"))
        assert metadata["version"] == version
    return root


@pytest.mark.parametrize("outcome", ["passed", "failed", "undefined"])
def test_builtin_replay_reads_real_saved_stream(tmp_path, node_root, outcome):
    (tmp_path / "features").mkdir()
    (tmp_path / "pytest.ini").write_text("[pytest]\ncuke_parser = python\n", encoding="utf-8")
    final_step = {
        "passed": "",
        "failed": "    When the replay failure occurs\n",
        "undefined": "    When the replay missing step\n",
    }[outcome]
    (tmp_path / "features" / "replay.feature").write_text(
        "Feature: Saved replay consumer\n  Scenario: Replay sentinel\n    Given the replay step passes\n" + final_step,
        encoding="utf-8",
    )
    (tmp_path / "conftest.py").write_text(
        "from pytest_cuke import given, when\n"
        "@given('the replay step passes')\n"
        "def passing(): pass\n"
        "@when('the replay failure occurs')\n"
        "def failing(): raise AssertionError('REPLAY-FAILURE-SENTINEL')\n"
        "@given('unused replay definition')\n"
        "def unused(): pass\n",
        encoding="utf-8",
    )
    source = tmp_path / "messages.ndjson"
    recorded = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "-c",
            "pytest.ini",
            "--confcutdir=.",
            "-q",
            "--cuke-messages-ndjson=" + str(source),
        ],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=90,
        check=False,
    )
    assert recorded.returncode == (0 if outcome == "passed" else 1), recorded.stdout + recorded.stderr
    original = source.read_bytes()
    outputs = {name: tmp_path / (name + ".txt") for name in _SELECTORS}
    command = [sys.executable, "-m", "pytest_cuke.cli", "replay", str(source)]
    for name, output in outputs.items():
        command.extend(["--formatter", f"{name}={output}"])
    replayed = subprocess.run(command, cwd=node_root, capture_output=True, text=True, timeout=90, check=False)
    assert replayed.returncode == 0, replayed.stdout + replayed.stderr
    assert source.read_bytes() == original
    reports = {name: path.read_text(encoding="utf-8") for name, path in outputs.items()}
    status = "undefined" if outcome == "undefined" else outcome
    assert f"1 scenario (1 {status})" in reports["summary"], reports["summary"]
    marker = {"passed": ".", "failed": "F", "undefined": "U"}[outcome]
    assert marker in reports["progress"]
    assert marker in reports["progress-bar"]
    assert "\x1b[" not in reports["progress-bar"]
    assert "Replay sentinel" in reports["pretty"]
    assert "the replay step passes" in reports["usage"]
    assert "unused replay definition" in reports["usage"]
    assert "UNUSED" in reports["usage"]
    usage = json.loads(reports["usage-json"])
    assert isinstance(usage, list)
    matched = [definition for definition in usage if definition.get("pattern") == "the replay step passes"]
    assert len(matched) == 1 and len(matched[0]["matches"]) == 1, usage
    if outcome == "undefined":
        assert "the replay missing step" in reports["snippets"]
        assert "function" in reports["snippets"]
    else:
        assert not reports["snippets"].strip()
    if outcome == "failed":
        assert "REPLAY-FAILURE-SENTINEL" in reports["summary"]

    # Dependency failure must preserve an existing destination rather than publish partial output.
    output = outputs["summary"]
    previous = output.read_bytes()
    missing_node_env = {**os.environ, "PATH": str(Path(sys.executable).parent)}
    assert shutil.which("node", path=missing_node_env["PATH"]) is None
    rejected = subprocess.run(
        [sys.executable, "-m", "pytest_cuke.cli", "replay", str(source), "--formatter", f"summary={output}"],
        cwd=node_root,
        env=missing_node_env,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    assert rejected.returncode == 2
    assert "requires executable 'node'" in rejected.stderr
    assert output.read_bytes() == previous
