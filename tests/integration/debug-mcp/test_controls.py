from __future__ import annotations

import asyncio
import json
import os
import subprocess
import sys
import time

import pytest

pytestmark = pytest.mark.integration


def _payload(result):
    assert not result.isError
    if isinstance(result.structuredContent, dict):
        return result.structuredContent
    return json.loads(next(block.text for block in result.content if hasattr(block, "text")))


async def _inspect_and_release(record):
    from mcp import ClientSession
    from mcp.client.streamable_http import streamable_http_client

    async with streamable_http_client(record["inspection_endpoint"]) as (reader, writer, _):
        async with ClientSession(reader, writer) as client:
            await client.initialize()
            snapshot = _payload(await client.call_tool("inspect_failure", {}))
            active = snapshot["active_failure"]
            assert active is not None
            assert active["sequence"] == record["active_failure"]["sequence"]
            released = _payload(
                await client.call_tool(
                    "release_failure",
                    {
                        "session_id": snapshot["session_id"],
                        "sequence": active["sequence"],
                    },
                )
            )
            assert released["released"] is True
            return active


@pytest.mark.parametrize("workers", [0, 2])
@pytest.mark.parametrize("cap", [0, 1])
def test_installed_consumer_hold_cap_and_redacted_environment(tmp_path, workers, cap):
    pytest.importorskip("mcp")
    pytest.importorskip("mcp_pdb")
    if workers:
        pytest.importorskip("xdist")
    (tmp_path / "pytest.ini").write_text("[pytest]\n", encoding="utf-8")
    (tmp_path / "test_failures.py").write_text(
        "def test_first():\n    assert False, 'first-failure'\n"
        "def test_second():\n    assert False, 'second-failure'\n",
        encoding="utf-8",
    )
    expose = cap == 0
    command = [
        sys.executable,
        "-m",
        "pytest",
        "-c",
        "pytest.ini",
        "--rootdir=.",
        "--confcutdir=.",
        "--cuke-mcp-on-fail",
        "--cuke-mcp-timeout=30s",
        "--cuke-mcp-lease=30s",
        f"--cuke-mcp-max-holds={cap}",
        "-q",
        "test_failures.py",
    ]
    if expose:
        command += ["--cuke-mcp-expose-env", "--cuke-mcp-redact-patterns=private_marker"]
    if workers:
        command += ["-n2", "--dist=each"]
    env = {
        **os.environ,
        "CUKE_PUBLIC_MARKER": "visible-value",
        "CUKE_TOKEN_MARKER": "token-value",
        "CUKE_PRIVATE_MARKER": "custom-value",
        "PYTEST_ADDOPTS": "",
    }
    seen = {}
    with (tmp_path / "consumer.log").open("w", encoding="utf-8") as output:
        process = subprocess.Popen(command, cwd=tmp_path, env=env, stdout=output, stderr=subprocess.STDOUT)
        deadline = time.monotonic() + 120
        try:
            while process.poll() is None and time.monotonic() < deadline:
                root = tmp_path / ".pytest_cache" / "cuke" / "debug-mcp"
                paths = list((root / "workers").glob("*.json")) if workers else [root / "session.json"]
                for path in paths:
                    try:
                        record = json.loads(path.read_text(encoding="utf-8"))
                    except (FileNotFoundError, json.JSONDecodeError):
                        continue
                    active = record.get("active_failure")
                    if record.get("status") != "holding_failure" or active is None:
                        continue
                    key = (record["session_id"], active["sequence"])
                    if key in seen:
                        continue
                    inspected = asyncio.run(_inspect_and_release(record))
                    if expose:
                        environment = inspected["environment"]
                        assert environment["CUKE_PUBLIC_MARKER"] == "visible-value"
                        assert environment["CUKE_TOKEN_MARKER"] == "<redacted>"
                        assert environment["CUKE_PRIVATE_MARKER"] == "<redacted>"
                        assert "token-value" not in json.dumps(record)
                        assert "custom-value" not in json.dumps(record)
                    else:
                        assert "environment" not in inspected
                        assert "visible-value" not in json.dumps(record)
                    seen[key] = record.get("worker_id", "main")
                time.sleep(0.03)
            assert process.wait(timeout=5) == 1, (tmp_path / "consumer.log").read_text()
        finally:
            if process.poll() is None:
                process.kill()
                process.wait(timeout=5)
    expected_workers = workers or 1
    assert len(seen) == expected_workers * (cap or 2)
    assert len(set(seen.values())) == expected_workers
