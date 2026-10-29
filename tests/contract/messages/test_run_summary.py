"""Installed consumer contract for terminal Messages diagnostics."""

import json
import subprocess
import sys

import pytest

pytestmark = pytest.mark.contract


@pytest.mark.parametrize("failure", [False, True])
def test_terminal_diagnostics(tmp_path, failure):
    (tmp_path / "pytest.ini").write_text("[pytest]\n")
    (tmp_path / "test_consumer.py").write_text("def test_consumer():\n    assert " + str(not failure) + "\n")
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "-c",
            "pytest.ini",
            "--confcutdir=.",
            "--cuke-messages-ndjson=messages.ndjson",
            "-q",
        ],
        check=False,
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == int(failure), result.stdout + result.stderr
    messages = [json.loads(line) for line in (tmp_path / "messages.ndjson").read_text().splitlines()]
    summaries = [event["testRunFinished"] for event in messages if "testRunFinished" in event]
    assert len(summaries) == 1
    summary = summaries[0]
    assert summary["success"] is not failure
    if failure:
        assert summary["message"] == "pytest session exit status: 1"
        assert summary["exception"]["type"] == "PytestExitCode"
        assert summary["exception"]["message"] == "1"
    else:
        assert summary.get("exception") is None
        assert summary.get("message") is None
