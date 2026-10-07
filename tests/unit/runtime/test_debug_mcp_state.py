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


def test_failure_queue_handles_large_finite_deadlines_until_explicit_release() -> None:
    queue = FailureQueue(session_id="session-1", timeout_seconds=1e308, lease_seconds=1e308)
    result: list[dict[str, Any]] = []
    errors: list[BaseException] = []

    def hold() -> None:
        try:
            result.append(
                queue.hold_failure(
                    nodeid="test_large_deadline",
                    phase="call",
                    error_type="RuntimeError",
                    error_message="large finite deadline",
                    bdd_context=None,
                )
            )
        except BaseException as error:
            errors.append(error)

    worker = threading.Thread(target=hold)
    worker.start()
    active = _wait_for_active(queue)
    release = queue.release_failure(session_id="session-1", sequence=active["sequence"])
    worker.join(timeout=1.0)

    assert not worker.is_alive()
    assert not errors, errors
    assert release["released"] is True
    assert result[0]["reason"] == "explicit"


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


def test_artifact_write_marks_only_the_matching_active_failure_after_success() -> None:
    queue = FailureQueue(session_id="session-1", timeout_seconds=1.0, lease_seconds=0.5)
    hold_result: list[dict[str, Any]] = []
    hold = threading.Thread(
        target=lambda: hold_result.append(
            queue.hold_failure(
                nodeid="features/debug.feature::Scenario: failure",
                phase="call",
                error_type="RuntimeError",
                error_message="failure sentinel",
                bdd_context={"scenario_name": "failure"},
            )
        )
    )
    hold.start()
    active = _wait_for_active(queue)
    sequence = active["sequence"]
    observed_active: list[dict[str, Any]] = []

    result = queue.write_artifact(
        session_id="session-1",
        sequence=sequence,
        writer=lambda failure: observed_active.append(failure) or {"written": True},
    )

    assert result == {"written": True}
    assert observed_active[0]["nodeid"] == "features/debug.feature::Scenario: failure"
    release = queue.release_failure(session_id="session-1", sequence=sequence)
    hold.join(timeout=1.0)

    assert not hold.is_alive()
    assert release["artifact_status"] == "written"
    assert hold_result[0]["artifact_status"] == "written"


def test_failed_artifact_writer_does_not_mark_or_advance_the_active_failure() -> None:
    queue = FailureQueue(session_id="session-1", timeout_seconds=1.0, lease_seconds=0.5)
    hold_result: list[dict[str, Any]] = []
    hold = threading.Thread(
        target=lambda: hold_result.append(
            queue.hold_failure(
                nodeid="tests/test_failure.py::test_first",
                phase="call",
                error_type="RuntimeError",
                error_message="first failure",
                bdd_context=None,
            )
        )
    )
    hold.start()
    active = _wait_for_active(queue)

    with pytest.raises(OSError, match="read-only"):
        queue.write_artifact(
            session_id="session-1",
            sequence=active["sequence"],
            writer=lambda failure: (_ for _ in ()).throw(OSError("read-only artifact root")),
        )

    still_active = queue.inspect_failure()["active_failure"]
    assert still_active == active
    release = queue.release_failure(session_id="session-1", sequence=active["sequence"])
    hold.join(timeout=1.0)

    assert not hold.is_alive()
    assert release["artifact_status"] == "missing"
    assert hold_result[0]["artifact_status"] == "missing"


def test_artifact_write_rejects_a_stale_session_or_sequence() -> None:
    queue = FailureQueue(session_id="session-1", timeout_seconds=1.0, lease_seconds=0.5)
    hold = threading.Thread(
        target=lambda: queue.hold_failure(
            nodeid="tests/test_failure.py::test_stale",
            phase="call",
            error_type="RuntimeError",
            error_message="held",
            bdd_context=None,
        )
    )
    hold.start()
    active = _wait_for_active(queue)

    with pytest.raises(FailureHoldError, match="active failure"):
        queue.write_artifact(session_id="another-session", sequence=active["sequence"], writer=lambda _: None)
    with pytest.raises(FailureHoldError, match="active failure"):
        queue.write_artifact(session_id="session-1", sequence=active["sequence"] + 1, writer=lambda _: None)

    queue.close()
    hold.join(timeout=1.0)
    assert not hold.is_alive()


def test_release_cannot_advance_to_another_failure_during_artifact_write() -> None:
    queue = FailureQueue(session_id="session-1", timeout_seconds=2.0, lease_seconds=1.0)
    hold_results: list[dict[str, Any]] = []
    hold = threading.Thread(
        target=lambda: hold_results.append(
            queue.hold_failure(
                nodeid="tests/test_failure.py::test_first",
                phase="call",
                error_type="RuntimeError",
                error_message="first failure",
                bdd_context=None,
            )
        )
    )
    hold.start()
    active = _wait_for_active(queue)
    writer_started = threading.Event()
    finish_write = threading.Event()
    write_results: list[str] = []
    release_results: list[dict[str, Any]] = []

    def write_artifact() -> None:
        def writer(_: dict[str, Any]) -> str:
            writer_started.set()
            assert finish_write.wait(timeout=1.0)
            return "paired-files-written"

        write_results.append(
            queue.write_artifact(
                session_id="session-1",
                sequence=active["sequence"],
                writer=writer,
            )
        )

    write = threading.Thread(target=write_artifact)
    write.start()
    assert writer_started.wait(timeout=1.0)
    release = threading.Thread(
        target=lambda: release_results.append(
            queue.release_failure(session_id="session-1", sequence=active["sequence"])
        )
    )
    release.start()
    time.sleep(0.02)
    assert release.is_alive()
    assert release_results == []

    finish_write.set()
    write.join(timeout=1.0)
    release.join(timeout=1.0)
    hold.join(timeout=1.0)

    assert not write.is_alive()
    assert not release.is_alive()
    assert not hold.is_alive()
    assert write_results == ["paired-files-written"]
    assert release_results[0]["artifact_status"] == "written"
    assert hold_results[0]["artifact_status"] == "written"
