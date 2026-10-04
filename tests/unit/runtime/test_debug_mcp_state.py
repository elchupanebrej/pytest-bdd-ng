from __future__ import annotations

import threading
import time
from typing import Any

import pytest

from pytest_cuke.debug_mcp.state import FailureHoldError, FailureQueue


def _wait_for_active(queue: FailureQueue, timeout: float = 2.0) -> dict[str, Any]:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        active = queue.inspect_failure().get("active_failure")
        if isinstance(active, dict):
            return active
        time.sleep(0.005)
    pytest.fail("the expected MCP failure hold did not become active")


def test_failure_queue_holds_until_client_releases_and_increments_sequence() -> None:
    queue = FailureQueue(session_id="session-1", timeout_seconds=2.0, lease_seconds=1.0)
    results: list[dict[str, Any]] = []

    first = threading.Thread(
        target=lambda: results.append(queue.hold_failure(nodeid="test_one", phase="call", error_type="ValueError", error_message="first", bdd_context=None))
    )
    first.start()
    active = _wait_for_active(queue)
    assert active["sequence"] == 1
    queue.heartbeat(session_id="session-1", sequence=1)
    release = queue.release_failure(session_id="session-1", sequence=1)
    first.join(timeout=1.0)

    assert not first.is_alive()
    assert release["released"] is True
    assert results[0]["reason"] == "explicit"
    assert results[0]["artifact_status"] == "missing"

    second = threading.Thread(
        target=lambda: results.append(queue.hold_failure(nodeid="test_two", phase="setup", error_type="RuntimeError", error_message="second", bdd_context=None))
    )
    second.start()
    active = _wait_for_active(queue)
    assert active["sequence"] == 2
    release = queue.release_failure(session_id="session-1", sequence=2, reason="debugger_continuation")
    second.join(timeout=1.0)

    assert not second.is_alive()
    assert release["reason"] == "debugger_continuation"
    assert results[1]["sequence"] == 2


def test_failure_queue_times_out_when_no_client_connects() -> None:
    queue = FailureQueue(session_id="session-1", timeout_seconds=0.04, lease_seconds=1.0)

    result = queue.hold_failure(
        nodeid="test_timeout",
        phase="call",
        error_type="RuntimeError",
        error_message="timed out",
        bdd_context=None,
    )

    assert result["reason"] == "timeout"
    assert queue.inspect_failure()["active_failure"] is None


def test_failure_queue_lease_expires_after_a_client_heartbeat() -> None:
    queue = FailureQueue(session_id="session-1", timeout_seconds=1.0, lease_seconds=0.04)
    result: list[dict[str, Any]] = []
    hold = threading.Thread(
        target=lambda: result.append(
            queue.hold_failure(
                nodeid="test_lease",
                phase="call",
                error_type="RuntimeError",
                error_message="lease expires",
                bdd_context=None,
            )
        )
    )
    hold.start()
    active = _wait_for_active(queue)
    queue.heartbeat(session_id="session-1", sequence=active["sequence"])
    hold.join(timeout=1.0)

    assert not hold.is_alive()
    assert result[0]["reason"] == "lease_expired"


def test_failure_queue_rejects_stale_session_and_sequence() -> None:
    queue = FailureQueue(session_id="session-1", timeout_seconds=1.0, lease_seconds=0.5)
    hold = threading.Thread(
        target=lambda: queue.hold_failure(
            nodeid="test_stale",
            phase="call",
            error_type="RuntimeError",
            error_message="held",
            bdd_context=None,
        )
    )
    hold.start()
    active = _wait_for_active(queue)

    with pytest.raises(FailureHoldError, match="active failure"):
        queue.release_failure(session_id="other-session", sequence=active["sequence"])
    with pytest.raises(FailureHoldError, match="active failure"):
        queue.heartbeat(session_id="session-1", sequence=active["sequence"] + 1)
    with pytest.raises(FailureHoldError, match="active failure"):
        queue.heartbeat(session_id="session-1", sequence=True)

    queue.close()
    hold.join(timeout=1.0)
    assert not hold.is_alive()
