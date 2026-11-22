from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

import pytest

pytestmark = pytest.mark.integration


def _run_with_unwritable_discovery_cache(tmp_path: Path) -> tuple[int, str]:
    discovery_path = tmp_path / ".pytest_cache" / "cuke" / "debug-mcp" / "session.json"
    command = [
        sys.executable,
        "-m",
        "pytest",
        "-c",
        "pytest.ini",
        "--rootdir=.",
        "--confcutdir=.",
        "--cuke-mcp-on-fail",
        "--cuke-mcp-timeout=1s",
        "--cuke-mcp-lease=1s",
        "-q",
        "test_failures.py",
    ]
    process = subprocess.Popen(
        command,
        cwd=tmp_path,
        env={**os.environ, "PYTEST_ADDOPTS": ""},
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    made_unwritable = False
    deadline = time.monotonic() + 60
    try:
        while time.monotonic() < deadline and process.poll() is None:
            if not made_unwritable and discovery_path.exists():
                try:
                    json.loads(discovery_path.read_text(encoding="utf-8"))
                except json.JSONDecodeError:
                    pass
                else:
                    discovery_path.parent.chmod(0o500)
                    made_unwritable = True
            time.sleep(0.01)
        output, _ = process.communicate(timeout=60)
    finally:
        if made_unwritable and discovery_path.parent.exists():
            discovery_path.parent.chmod(0o700)
        if process.poll() is None:
            process.kill()
            process.communicate()
    assert made_unwritable, output
    return process.returncode, output


def test_unwritable_discovery_cache_keeps_the_failure_report_and_warns_once(tmp_path) -> None:
    pytest.importorskip("pydantic")
    pytest.importorskip("mcp")
    pytest.importorskip("mcp_pdb")
    (tmp_path / "pytest.ini").write_text("[pytest]\n", encoding="utf-8")
    (tmp_path / "test_failures.py").write_text(
        "def test_boom():\n    assert False, 'cache-publish-sentinel'\n",
        encoding="utf-8",
    )

    for _ in range(3):
        returncode, output = _run_with_unwritable_discovery_cache(tmp_path)
        if returncode != 4 or "did not become ready" not in output:
            break
    else:
        pytest.skip("the optional Debug MCP backend did not start in this environment")

    assert returncode == 1, output
    assert "1 failed" in output, output
    assert "cache-publish-sentinel" in output, output
    assert "INTERNALERROR" not in output, output
    assert output.count("Debug MCP discovery publish failed") == 1, output
