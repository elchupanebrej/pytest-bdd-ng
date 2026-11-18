"""Act as the external Debug MCP agent for one remote xdist controller container."""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import time
from pathlib import Path
from urllib.parse import urlsplit

from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

INDEX_PATH = Path("/workspace/tests/external/remote-xdist/project/.pytest_cache/cuke/debug-mcp/workers.json")


def _read_index() -> dict:
    return json.loads(INDEX_PATH.read_text(encoding="utf-8"))


def _tool_payload(result):
    structured = getattr(result, "structuredContent", None)
    if isinstance(structured, dict):
        return structured
    for block in getattr(result, "content", []):
        text = getattr(block, "text", None)
        if isinstance(text, str):
            try:
                payload = json.loads(text)
            except json.JSONDecodeError:
                continue
            if isinstance(payload, dict):
                return payload
    raise AssertionError(f"MCP tool did not return structured JSON: {result!r}")


def _holding_workers(index: dict) -> list[dict]:
    workers = index.get("workers")
    if not isinstance(workers, list):
        return []
    return [
        worker
        for worker in workers
        if isinstance(worker, dict)
        and worker.get("status") == "holding_failure"
        and isinstance(worker.get("active_failure"), dict)
        and isinstance(worker.get("inspection_endpoint"), str)
        and worker["inspection_endpoint"]
    ]


def _wait_for_holds(expected: int, timeout: float) -> dict:
    deadline = time.monotonic() + timeout
    last: object = "worker index has not been published"
    while time.monotonic() < deadline:
        try:
            index = _read_index()
        except (OSError, json.JSONDecodeError) as error:
            last = repr(error)
        else:
            workers = _holding_workers(index)
            if len(workers) >= expected:
                return index
            last = index
        time.sleep(0.1)
    raise TimeoutError(f"expected {expected} remote Debug MCP holds before the deadline: {last!r}")


async def _inspect_release(record: dict, secret: str) -> dict:
    endpoint = record["inspection_endpoint"]
    failure = record["active_failure"]
    async with streamable_http_client(endpoint, terminate_on_close=False) as (
        read_stream,
        write_stream,
        _get_session_id,
    ):
        async with ClientSession(read_stream, write_stream) as session:
            await asyncio.wait_for(session.initialize(), timeout=20)
            inspected = _tool_payload(await asyncio.wait_for(session.call_tool("inspect_failure", {}), timeout=20))
            assert inspected["session_id"] == record["session_id"], (inspected, record)
            assert inspected["active_failure"]["sequence"] == failure["sequence"], (inspected, record)
            artifact = {
                "artifact_id": f"{record['worker_id']}-remote-investigation",
                "nodeid": failure["nodeid"],
                "pytest_phase": failure["phase"],
                "status": "investigated",
                "summary": f"remote investigation for {record['worker_id']} with {secret}",
                "inspected_commands": ["inspect_failure"],
                "evidence": [f"worker {record['worker_id']} reported {secret}"],
                "suspected_cause": f"remote failure carried {secret}",
                "next_action": "release the remote hold",
            }
            submitted = _tool_payload(
                await asyncio.wait_for(
                    session.call_tool(
                        "submit_artifact",
                        {
                            "session_id": inspected["session_id"],
                            "sequence": failure["sequence"],
                            "artifact": artifact,
                        },
                    ),
                    timeout=20,
                )
            )
            assert submitted.get("ok") is True, submitted
            await asyncio.wait_for(
                session.call_tool(
                    "heartbeat",
                    {"session_id": inspected["session_id"], "sequence": failure["sequence"]},
                ),
                timeout=20,
            )
            released = _tool_payload(
                await asyncio.wait_for(
                    session.call_tool(
                        "release_failure",
                        {"session_id": inspected["session_id"], "sequence": failure["sequence"]},
                    ),
                    timeout=20,
                )
            )
            assert released.get("released") is True, released
            return {
                "endpoint": endpoint,
                "endpoint_host": urlsplit(endpoint).hostname,
                "release": released,
                "submission": submitted,
            }


def _wait_for_cleared(worker_ids: list[str], timeout: float) -> dict:
    deadline = time.monotonic() + timeout
    cleared: dict[str, bool] = {worker_id: False for worker_id in worker_ids}
    while time.monotonic() < deadline:
        try:
            index = _read_index()
        except (OSError, json.JSONDecodeError):
            time.sleep(0.1)
            continue
        records = {worker.get("worker_id"): worker for worker in index.get("workers", []) if isinstance(worker, dict)}
        for worker_id in worker_ids:
            record = records.get(worker_id)
            if isinstance(record, dict) and record.get("active_failure") is None:
                cleared[worker_id] = True
        if all(cleared.values()):
            return cleared
        time.sleep(0.1)
    raise TimeoutError(f"remote Debug MCP snapshots were not cleared after release: {cleared!r}")


def _wait_for_crash(worker_id: str, timeout: float) -> dict:
    deadline = time.monotonic() + timeout
    last: object = "worker index has not been published"
    while time.monotonic() < deadline:
        try:
            index = _read_index()
        except (OSError, json.JSONDecodeError) as error:
            last = repr(error)
        else:
            for record in index.get("workers", []):
                if not isinstance(record, dict):
                    continue
                if worker_id and record.get("worker_id") != worker_id:
                    continue
                if (
                    record.get("status") == "worker_crashed"
                    and record.get("debugger_endpoint") is None
                    and record.get("inspection_endpoint") is None
                ):
                    return {"worker": record, "root_status": index.get("status")}
            last = index
        time.sleep(0.1)
    raise TimeoutError(f"worker {worker_id!r} was never reported stopped: {last!r}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--action", choices=("release", "wait", "observe-crash"), required=True)
    parser.add_argument("--expected-holds", type=int, default=1)
    parser.add_argument("--timeout", type=float, default=120.0)
    parser.add_argument("--worker-id", default="")
    parser.add_argument("--secret", default=os.environ.get("REMOTE_DEBUG_SECRET", ""))
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    observation: dict[str, object] = {"action": args.action}
    if args.action == "observe-crash":
        observation.update(_wait_for_crash(args.worker_id, args.timeout))
    else:
        index = _wait_for_holds(args.expected_holds, args.timeout)
        observation["initial"] = {
            "session_id": index.get("session_id"),
            "workers": [
                {
                    "worker_id": worker.get("worker_id"),
                    "host": worker.get("host"),
                    "inspection_endpoint": worker.get("inspection_endpoint"),
                    "active_failure": worker.get("active_failure"),
                }
                for worker in _holding_workers(index)
            ],
        }
        if args.action == "release":
            released = [asyncio.run(_inspect_release(worker, args.secret)) for worker in _holding_workers(index)]
            worker_ids = [worker.get("worker_id") for worker in _holding_workers(index)]
            observation["released"] = released
            observation["cleared"] = _wait_for_cleared(worker_ids, 30)

    Path(args.output).write_text(json.dumps(observation, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(observation, sort_keys=True), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
