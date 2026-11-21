from __future__ import annotations

import http.client
import json
import os
import socket
import time
from pathlib import Path
from types import SimpleNamespace

import pytest

from pytest_cuke.test_groups.assignment import TestGroupAssignment, TestGroupAssignmentSource
from pytest_cuke.test_groups.barrier import (
    FilesystemBarrierState,
    TestGroupBarrier,
    TestGroupBarrierShutdown,
    TestGroupBarrierTimeout,
    TestGroupBarrierWorkerDeath,
    _write_json_atomically,
)
from pytest_cuke.test_groups.plugin import TestGroupPlugin
from pytest_cuke.test_groups.relay import BarrierRelayError, RelayBarrierClient, start_relay
from pytest_cuke.test_groups.transport import BarrierSnapshot

RELAY_CREDENTIAL = "test-run-credential"


def _assignment(nodeid: str, group: str, ordinal: int) -> TestGroupAssignment:
    return TestGroupAssignment(
        nodeid=nodeid,
        group=group,
        ordinal=ordinal,
        source=TestGroupAssignmentSource.DEFAULT,
    )


def test_barrier_waits_for_receipt_and_deduplicates_terminal_reports(tmp_path: Path) -> None:
    barrier = TestGroupBarrier.for_state_directory(tmp_path / "run-a", timeout=0.1, groups=("unit", "integration"))
    unit = _assignment("tests/test_unit.py::test_unit", "unit", 0)
    integration = _assignment("tests/test_integration.py::test_integration", "integration", 1)
    barrier.initialize((unit, integration))

    with pytest.raises(TestGroupBarrierTimeout, match=r"unit.*integration"):
        barrier.wait_for_earlier_groups(integration)

    barrier.record_terminal(unit.nodeid)
    barrier.record_terminal(unit.nodeid)
    barrier.wait_for_earlier_groups(integration)

    receipt_files = tuple((tmp_path / "run-a" / "receipts").glob("*.json"))
    assert len(receipt_files) == 1
    assert json.loads(receipt_files[0].read_text(encoding="utf-8"))["nodeid"] == unit.nodeid


def test_barrier_state_isolated_by_run_directory(tmp_path: Path) -> None:
    unit = _assignment("tests/test_unit.py::test_unit", "unit", 0)
    integration = _assignment("tests/test_integration.py::test_integration", "integration", 1)
    first = TestGroupBarrier.for_state_directory(tmp_path / "run-a", timeout=0.02, groups=("unit", "integration"))
    second = TestGroupBarrier.for_state_directory(tmp_path / "run-b", timeout=0.02, groups=("unit", "integration"))
    first.initialize((unit, integration))
    second.initialize((unit, integration))
    first.record_terminal(unit.nodeid)

    first.wait_for_earlier_groups(integration)
    with pytest.raises(TestGroupBarrierTimeout, match="unit"):
        second.wait_for_earlier_groups(integration)


def test_empty_selection_does_not_create_barrier_state(tmp_path: Path) -> None:
    state_dir = tmp_path / "empty-run"
    barrier = TestGroupBarrier.for_state_directory(state_dir, timeout=1, groups=("unit", "integration"))

    barrier.initialize(())

    assert not state_dir.exists()


def test_atomic_state_replace_retries_transient_permission_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import pytest_cuke.test_groups.barrier as barrier_module

    target = tmp_path / "state.json"
    replace = barrier_module.os.replace
    calls = 0

    def transient_replace(source: str | bytes | Path, destination: str | bytes | Path) -> None:
        nonlocal calls
        calls += 1
        if calls == 1:
            raise PermissionError(13, "file is temporarily in use")
        replace(source, destination)

    monkeypatch.setattr(barrier_module.os, "replace", transient_replace)
    _write_json_atomically(target, {"published": True})

    assert calls == 2
    assert json.loads(target.read_text(encoding="utf-8")) == {"published": True}


def test_barrier_retries_a_transient_replace_error_after_a_slow_initial_write(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import pytest_cuke.test_groups.barrier as barrier_module

    clock = [0.0]
    attempts = 0

    def slow_first_fsync(fd: int) -> None:
        os.fsync(fd)
        if clock[0] == 0:
            clock[0] = 3.0

    def transient_replace(source: str | bytes | Path, destination: str | bytes | Path) -> None:
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            raise PermissionError(13, "file is temporarily in use")
        os.replace(source, destination)

    def advance(seconds: float) -> None:
        clock[0] += seconds

    monkeypatch.setattr(barrier_module, "time", SimpleNamespace(monotonic=lambda: clock[0], sleep=advance))
    monkeypatch.setattr(barrier_module, "os", SimpleNamespace(fsync=slow_first_fsync, replace=transient_replace))
    barrier = TestGroupBarrier.for_state_directory(tmp_path / "run", timeout=1, groups=("unit",))

    barrier.initialize((_assignment("tests/test_unit.py::test_unit", "unit", 0),))

    assert attempts == 2
    assert json.loads((tmp_path / "run" / "manifest.json").read_text(encoding="utf-8"))["items"][0]["group"] == "unit"


def test_barrier_stops_retrying_a_persistent_replace_error(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import pytest_cuke.test_groups.barrier as barrier_module

    clock = [0.0]
    attempts = 0

    def failing_replace(source: str | bytes | Path, destination: str | bytes | Path) -> None:
        nonlocal attempts
        attempts += 1
        raise PermissionError(13, "file is temporarily in use")

    def advance(seconds: float) -> None:
        clock[0] += seconds

    monkeypatch.setattr(barrier_module, "time", SimpleNamespace(monotonic=lambda: clock[0], sleep=advance))
    monkeypatch.setattr(barrier_module, "os", SimpleNamespace(fsync=os.fsync, replace=failing_replace))
    barrier = TestGroupBarrier.for_state_directory(tmp_path / "run", timeout=1, groups=("unit",))

    with pytest.raises(PermissionError, match="temporarily in use"):
        barrier.initialize((_assignment("tests/test_unit.py::test_unit", "unit", 0),))

    assert attempts > 1
    assert 2.0 <= clock[0] < 2.1
    assert not list((tmp_path / "run").glob("*.tmp"))


@pytest.mark.parametrize(
    ("when", "outcome", "should_record"),
    [
        ("setup", "passed", False),
        ("setup", "failed", False),
        ("setup", "skipped", False),
        ("call", "passed", False),
        ("call", "failed", False),
        ("call", "skipped", False),
        ("teardown", "passed", True),
        ("teardown", "failed", False),
        ("teardown", "skipped", False),
    ],
)
def test_plugin_records_only_a_successful_teardown(when: str, outcome: str, should_record: bool) -> None:
    plugin = object.__new__(TestGroupPlugin)
    recorded: list[str] = []
    plugin._worker = True
    plugin._retry_teardowns = set()
    plugin.barrier = SimpleNamespace(record_terminal=recorded.append)

    plugin.pytest_runtest_logreport(SimpleNamespace(when=when, outcome=outcome, nodeid="test-id"))

    assert recorded == (["test-id"] if should_record else [])


def test_plugin_records_a_rerun_item_only_after_its_final_teardown() -> None:
    plugin = object.__new__(TestGroupPlugin)
    recorded: list[str] = []
    plugin._worker = True
    plugin._retry_teardowns = set()
    plugin.barrier = SimpleNamespace(record_terminal=recorded.append)
    reports = [
        SimpleNamespace(when="setup", outcome="passed", nodeid="test-id"),
        SimpleNamespace(when="call", outcome="rerun", nodeid="test-id"),
        SimpleNamespace(when="teardown", outcome="passed", nodeid="test-id"),
        SimpleNamespace(when="setup", outcome="passed", nodeid="test-id"),
        SimpleNamespace(when="call", outcome="passed", nodeid="test-id"),
        SimpleNamespace(when="teardown", outcome="passed", nodeid="test-id"),
    ]

    for report in reports:
        plugin.pytest_runtest_logreport(report)

    assert recorded == ["test-id"]


def test_filesystem_barrier_stops_waiting_when_the_controller_signals_shutdown(tmp_path: Path) -> None:
    state_dir = tmp_path / "run"
    unit = _assignment("tests/test_unit.py::test_unit", "unit", 0)
    integration = _assignment("tests/test_integration.py::test_integration", "integration", 1)
    barrier = TestGroupBarrier.for_state_directory(state_dir, timeout=30, groups=("unit", "integration"))
    barrier.initialize((unit, integration))
    FilesystemBarrierState(state_dir, timeout=30).publish_shutdown()

    started = time.monotonic()
    with pytest.raises(TestGroupBarrierShutdown, match="stopping"):
        barrier.wait_for_earlier_groups(integration)

    assert time.monotonic() - started < 2


def test_plugin_skips_a_blocked_test_when_the_controller_signals_shutdown() -> None:
    plugin = object.__new__(TestGroupPlugin)
    assignment = _assignment("tests/test_integration.py::test_integration", "integration", 1)
    plugin.assignments = {assignment.nodeid: assignment}

    def stop_waiting(_assignment: TestGroupAssignment) -> None:
        raise TestGroupBarrierShutdown("The pytest session is stopping")

    plugin.barrier = SimpleNamespace(claim=lambda nodeid: None, wait_for_earlier_groups=stop_waiting)
    item = SimpleNamespace(nodeid=assignment.nodeid)

    with pytest.raises(pytest.skip.Exception, match="session is stopping"):
        plugin.pytest_runtest_setup(item)


def test_plugin_releases_waiters_at_session_finish() -> None:
    plugin = object.__new__(TestGroupPlugin)
    shutdowns: list[str] = []
    plugin.group_configuration = SimpleNamespace(enabled=True, barrier_timeout=60)
    plugin.relay = SimpleNamespace(state=SimpleNamespace(publish_shutdown=lambda: shutdowns.append("relay")))
    plugin._worker = False
    plugin._xdist_workers_configured = True
    plugin._shutdown_published = False
    plugin._state_dir = None

    plugin.pytest_sessionfinish(SimpleNamespace(), 1)

    assert shutdowns == ["relay"]
    assert plugin._shutdown_published is True


def test_plugin_releases_waiters_as_soon_as_the_session_stops() -> None:
    plugin = object.__new__(TestGroupPlugin)
    shutdowns: list[str] = []
    plugin.group_configuration = SimpleNamespace(enabled=True, barrier_timeout=60)
    plugin.relay = SimpleNamespace(state=SimpleNamespace(publish_shutdown=lambda: shutdowns.append("relay")))
    plugin._worker = False
    plugin._xdist_workers_configured = True
    plugin._shutdown_published = False
    plugin._state_dir = None
    plugin.barrier = None
    plugin._session = SimpleNamespace(shouldstop=False, shouldfail="stopping after 1 failures")

    plugin.pytest_runtest_logreport(SimpleNamespace(when="teardown", outcome="failed", nodeid="test-id"))

    assert shutdowns == ["relay"]
    assert plugin._shutdown_published is True


def test_plugin_does_not_release_waiters_while_the_session_continues() -> None:
    plugin = object.__new__(TestGroupPlugin)
    shutdowns: list[str] = []
    plugin.group_configuration = SimpleNamespace(enabled=True, barrier_timeout=60)
    plugin.relay = SimpleNamespace(state=SimpleNamespace(publish_shutdown=lambda: shutdowns.append("relay")))
    plugin._worker = False
    plugin._xdist_workers_configured = True
    plugin._shutdown_published = False
    plugin._state_dir = None
    plugin.barrier = None
    plugin._session = SimpleNamespace(shouldstop=False, shouldfail=False)

    plugin.pytest_runtest_logreport(SimpleNamespace(when="teardown", outcome="passed", nodeid="test-id"))

    assert shutdowns == []


def test_plugin_writes_a_filesystem_shutdown_marker_at_session_finish(tmp_path: Path) -> None:
    plugin = object.__new__(TestGroupPlugin)
    plugin.group_configuration = SimpleNamespace(enabled=True, barrier_timeout=60)
    plugin.relay = None
    plugin._worker = False
    plugin._xdist_workers_configured = True
    plugin._shutdown_published = False
    plugin._state_dir = tmp_path / "run"

    plugin.pytest_sessionfinish(SimpleNamespace(), 1)

    assert (tmp_path / "run" / "shutdown").exists()


def test_plugin_rejects_remote_xdist_specs_before_worker_setup() -> None:
    plugin = object.__new__(TestGroupPlugin)
    plugin.group_configuration = SimpleNamespace(enabled=True, relay=None)

    with pytest.raises(pytest.UsageError, match="shared filesystem"):
        plugin.pytest_xdist_setupnodes([SimpleNamespace(popen=False, ssh="invalid.invalid")])


def test_plugin_allows_remote_xdist_specs_when_the_barrier_relay_is_configured() -> None:
    plugin = object.__new__(TestGroupPlugin)
    plugin.group_configuration = SimpleNamespace(enabled=True, relay=("controller", 8889))

    plugin.pytest_xdist_setupnodes([SimpleNamespace(popen=False, ssh="worker1")])


def test_plugin_allows_local_popen_xdist_specs() -> None:
    plugin = object.__new__(TestGroupPlugin)
    plugin.group_configuration = SimpleNamespace(enabled=True, relay=None)

    plugin.pytest_xdist_setupnodes([SimpleNamespace(popen=True)])


@pytest.fixture
def relay():
    server = start_relay(0, credential=RELAY_CREDENTIAL)
    try:
        yield server
    finally:
        server.stop()


def _relay_barrier(relay, worker: str, *, timeout: float = 2.0) -> TestGroupBarrier:
    return TestGroupBarrier.for_relay(
        ("127.0.0.1", relay.port),
        timeout=timeout,
        groups=("unit", "integration"),
        worker_id=worker,
        credential=RELAY_CREDENTIAL,
    )


def _recv_all(connection: socket.socket) -> bytes:
    response = b""
    while chunk := connection.recv(4096):
        response += chunk
    return response


def _raw_relay_post(relay, request: dict, *, credential: str | None = None, timeout: float = 2.0) -> dict:
    body = dict(request)
    if credential is not None:
        body["credential"] = credential
    connection = http.client.HTTPConnection("127.0.0.1", relay.port, timeout=timeout)
    try:
        connection.request("POST", "/", body=json.dumps(body), headers={"Content-Type": "application/json"})
        response = connection.getresponse()
        return json.loads(response.read() or b"{}")
    finally:
        connection.close()


def test_relay_barrier_orders_groups_and_deduplicates_terminal_receipts(relay) -> None:
    unit = _assignment("tests/test_unit.py::test_unit", "unit", 0)
    integration = _assignment("tests/test_integration.py::test_integration", "integration", 1)
    producer = _relay_barrier(relay, "gw0")
    waiter = _relay_barrier(relay, "gw1", timeout=0.1)
    producer.initialize((unit, integration))
    waiter.initialize((unit, integration))

    with pytest.raises(TestGroupBarrierTimeout, match=r"unit.*integration"):
        waiter.wait_for_earlier_groups(integration)

    producer.record_terminal(unit.nodeid)
    producer.record_terminal(unit.nodeid)
    waiter.wait_for_earlier_groups(integration)

    receipts = relay.state.snapshot().receipts
    assert list(receipts) == [unit.nodeid]
    assert receipts[unit.nodeid] == {"nodeid": unit.nodeid, "group": "unit", "ordinal": 0}


def test_relay_barrier_ignores_receipts_for_unselected_items(relay) -> None:
    unit = _assignment("tests/test_unit.py::test_unit", "unit", 0)
    barrier = _relay_barrier(relay, "gw0")
    barrier.initialize((unit,))

    barrier.record_terminal("tests/test_other.py::test_other")

    assert relay.state.snapshot().receipts == {}


def test_relay_rejects_every_operation_without_the_run_credential(relay) -> None:
    forged_requests = [
        {"op": "publish_manifest", "manifest": {"groups": ["unit"], "items": []}},
        {"op": "claim", "nodeid": "tests/test_unit.py::test_unit", "worker": "gw9"},
        {"op": "publish_receipt", "nodeid": "tests/test_unit.py::test_unit"},
        {"op": "worker_down", "worker": "gw0", "detail": "forged"},
        {"op": "snapshot"},
    ]

    for request in forged_requests:
        response = _raw_relay_post(relay, request)

        assert response["ok"] is False, request
        assert "credential" in response["error"], request

    assert relay.state.snapshot() == BarrierSnapshot(manifest=None, receipts={}, owners={}, dead_workers=())


def test_relay_rejects_every_operation_with_a_wrong_run_credential(relay) -> None:
    response = _raw_relay_post(relay, {"op": "worker_down", "worker": "gw0"}, credential="not-the-credential")

    assert response["ok"] is False
    assert "credential" in response["error"]
    assert relay.state.snapshot().dead_workers == ()


def test_forged_receipt_without_the_run_credential_cannot_open_the_next_group(relay) -> None:
    unit = _assignment("tests/test_unit.py::test_unit", "unit", 0)
    integration = _assignment("tests/test_integration.py::test_integration", "integration", 1)
    producer = _relay_barrier(relay, "gw0")
    waiter = _relay_barrier(relay, "gw1", timeout=0.3)
    producer.initialize((unit, integration))
    waiter.initialize((unit, integration))

    forged = _raw_relay_post(relay, {"op": "publish_receipt", "nodeid": unit.nodeid})

    assert forged["ok"] is False
    with pytest.raises(TestGroupBarrierTimeout, match="test_unit"):
        waiter.wait_for_earlier_groups(integration)

    producer.record_terminal(unit.nodeid)
    waiter.wait_for_earlier_groups(integration)


def test_relay_client_with_a_wrong_credential_fails_loudly_without_changing_state(relay) -> None:
    client = RelayBarrierClient(
        ("127.0.0.1", relay.port),
        worker_id="gw0",
        credential="not-the-credential",
        timeout=0.2,
    )

    with pytest.raises(BarrierRelayError, match="credential"):
        client.publish_manifest({"groups": ["unit"], "items": []})

    assert relay.state.snapshot().manifest is None


def test_relay_rejects_a_negative_content_length_promptly(relay) -> None:
    with socket.create_connection(("127.0.0.1", relay.port), timeout=2) as connection:
        connection.sendall(b"POST / HTTP/1.1\r\nHost: relay\r\nContent-Length: -1\r\n\r\n")

        response = _recv_all(connection)

    assert b"Content-Length" in response
    assert relay.state.snapshot().manifest is None


def test_relay_rejects_an_oversized_body_without_waiting_for_it(relay) -> None:
    with socket.create_connection(("127.0.0.1", relay.port), timeout=2) as connection:
        connection.sendall(b"POST / HTTP/1.1\r\nHost: relay\r\nContent-Length: 1000001\r\n\r\n")

        response = _recv_all(connection)

    assert b"exceeds" in response
    assert relay.state.snapshot().manifest is None


def test_relay_bounds_socket_reads(relay, monkeypatch: pytest.MonkeyPatch) -> None:
    from pytest_cuke.test_groups import relay as relay_module

    default_timeout = relay_module._RelayRequestHandler.timeout
    assert 0 < default_timeout <= 60
    monkeypatch.setattr(relay_module._RelayRequestHandler, "timeout", 0.2)
    started = time.monotonic()

    with socket.create_connection(("127.0.0.1", relay.port), timeout=2) as connection:
        connection.sendall(b"POST / HTTP/1.1\r\nHost: relay\r\nContent-Length: 10\r\n\r\nshort")

        response = _recv_all(connection)

    assert time.monotonic() - started < 2
    assert b"timed out" in response


@pytest.mark.parametrize(
    "manifest",
    [
        {"items": []},
        {"groups": ["unit"]},
        {"groups": ["unit"], "items": "not-a-list"},
        {"groups": ["unit"], "items": [{"nodeid": 3, "group": "unit", "ordinal": 0}]},
        {"groups": ["unit"], "items": [{"nodeid": "test-id", "group": "unit"}]},
        {"groups": ["unit"], "items": [{"nodeid": "test-id", "group": "unit", "ordinal": "0"}]},
        {"groups": "unit", "items": []},
    ],
)
def test_relay_rejects_a_malformed_manifest(relay, manifest: dict) -> None:
    valid = {"groups": ["unit"], "items": []}
    assert _raw_relay_post(relay, {"op": "publish_manifest", "manifest": valid}, credential=RELAY_CREDENTIAL)["ok"]

    response = _raw_relay_post(relay, {"op": "publish_manifest", "manifest": manifest}, credential=RELAY_CREDENTIAL)

    assert response["ok"] is False
    assert "publish_manifest" in response["error"]
    assert relay.state.snapshot().manifest == valid


def test_a_rejected_manifest_leaves_waiters_with_the_timeout_diagnostic(relay) -> None:
    integration = _assignment("tests/test_integration.py::test_integration", "integration", 1)
    waiter = _relay_barrier(relay, "gw0", timeout=0.2)

    response = _raw_relay_post(
        relay,
        {"op": "publish_manifest", "manifest": {"groups": ["unit"], "items": [{"nodeid": 3}]}},
        credential=RELAY_CREDENTIAL,
    )

    assert response["ok"] is False
    with pytest.raises(TestGroupBarrierTimeout, match="run manifest was not published"):
        waiter.wait_for_earlier_groups(integration)


def test_relay_binds_and_serves_an_ipv6_advertised_host() -> None:
    if not socket.has_ipv6:
        pytest.skip("this host has no IPv6 support")
    try:
        server = start_relay(0, credential=RELAY_CREDENTIAL, host="::1")
    except OSError as error:
        pytest.skip(f"IPv6 loopback is unavailable: {error}")
    try:
        client = RelayBarrierClient(
            ("::1", server.port),
            worker_id="gw0",
            credential=RELAY_CREDENTIAL,
            timeout=2,
        )

        client.publish_manifest({"groups": ["unit"], "items": []})

        assert server.state.snapshot().manifest == {"groups": ["unit"], "items": []}
        assert client.label == f"[::1]:{server.port}"
    finally:
        server.stop()


def test_relay_barrier_names_the_unfinished_group_and_test_when_a_worker_dies(relay) -> None:
    unit = _assignment("tests/test_a_unit.py::test_unit_exits", "unit", 0)
    integration = _assignment("tests/test_z_integration.py::test_integration", "integration", 1)
    doomed = _relay_barrier(relay, "gw1", timeout=30)
    waiter = _relay_barrier(relay, "gw0", timeout=30)
    doomed.initialize((unit, integration))
    waiter.initialize((unit, integration))
    doomed.claim(unit.nodeid)
    relay.state.mark_worker_down("gw1", "worker gw1 crashed")

    started = time.monotonic()
    with pytest.raises(TestGroupBarrierWorkerDeath, match="test_unit_exits") as error:
        waiter.wait_for_earlier_groups(integration)

    assert time.monotonic() - started < 5
    message = str(error.value)
    assert "'gw1'" in message
    assert "'unit'" in message
    assert "tests/test_a_unit.py::test_unit_exits" in message
    assert "127.0.0.1" in message


def test_relay_barrier_keeps_waiting_when_a_finished_worker_dies(relay) -> None:
    unit = _assignment("tests/test_unit.py::test_unit", "unit", 0)
    integration = _assignment("tests/test_integration.py::test_integration", "integration", 1)
    producer = _relay_barrier(relay, "gw1", timeout=0.2)
    waiter = _relay_barrier(relay, "gw0", timeout=0.2)
    producer.initialize((unit, integration))
    waiter.initialize((unit, integration))
    producer.claim(unit.nodeid)
    producer.record_terminal(unit.nodeid)
    relay.state.mark_worker_down("gw1", "normal shutdown")

    waiter.wait_for_earlier_groups(integration)


def test_relay_barrier_stops_waiting_when_the_controller_signals_shutdown(relay) -> None:
    integration = _assignment("tests/test_integration.py::test_integration", "integration", 1)
    barrier = _relay_barrier(relay, "gw0", timeout=30)
    barrier.initialize((integration,))
    relay.state.publish_shutdown()

    started = time.monotonic()
    with pytest.raises(TestGroupBarrierShutdown, match="stopping"):
        barrier.wait_for_earlier_groups(integration)

    assert time.monotonic() - started < 2


def test_relay_barrier_timeout_names_the_relay_and_pending_test(relay) -> None:
    unit = _assignment("tests/test_unit.py::test_unit", "unit", 0)
    integration = _assignment("tests/test_integration.py::test_integration", "integration", 1)
    barrier = _relay_barrier(relay, "gw0", timeout=0.1)
    barrier.initialize((unit, integration))

    with pytest.raises(TestGroupBarrierTimeout, match="test_unit") as error:
        barrier.wait_for_earlier_groups(integration)

    message = str(error.value)
    assert "Timed out" in message
    assert "barrier relay" in message
    assert "shared filesystem" not in message
    assert barrier.relay_label == f"127.0.0.1:{relay.port}"


def test_relay_client_retries_a_transient_connection_error(relay, monkeypatch: pytest.MonkeyPatch) -> None:
    import pytest_cuke.test_groups.relay as relay_module

    client = relay_module.RelayBarrierClient(
        ("127.0.0.1", relay.port),
        worker_id="gw0",
        credential=RELAY_CREDENTIAL,
        timeout=2,
    )
    original_post = client._post
    attempts = 0

    def flaky_post(request):
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            raise ConnectionResetError("relay connection reset")
        return original_post(request)

    monkeypatch.setattr(client, "_post", flaky_post)
    client.publish_manifest({"groups": ["unit"], "items": []})

    assert attempts == 2
    assert relay.state.snapshot().manifest == {"groups": ["unit"], "items": []}


def test_relay_client_fails_loudly_when_the_relay_is_unreachable() -> None:
    probe = start_relay(0, credential=RELAY_CREDENTIAL)
    port = probe.port
    probe.stop()
    client = RelayBarrierClient(("127.0.0.1", port), worker_id="gw0", credential=RELAY_CREDENTIAL, timeout=0.2)

    with pytest.raises(BarrierRelayError, match="cuke_test_group_relay"):
        client.publish_manifest({"groups": ["unit"], "items": []})


def test_plugin_shares_the_run_identity_and_credential_with_each_worker(tmp_path: Path) -> None:
    plugin = object.__new__(TestGroupPlugin)
    plugin.group_configuration = SimpleNamespace(enabled=True)
    plugin.relay_credential = "per-run-credential"
    plugin.run_id = "run-42"
    plugin.config = SimpleNamespace(rootpath=tmp_path)
    plugin._xdist_workers_configured = False
    plugin._state_dir = None
    node = SimpleNamespace(workerinput={})

    plugin.pytest_configure_node(node)

    assert node.workerinput["cuke_test_group_relay_credential"] == "per-run-credential"
    assert node.workerinput["cuke_test_group_run_id"] == "run-42"
    assert plugin._state_dir == tmp_path / ".pytest_cache" / "pytest-cuke-test-groups" / "run-42"
    assert plugin._xdist_workers_configured is True


def test_filesystem_transport_remains_the_default() -> None:
    barrier = TestGroupBarrier.for_state_directory(Path("/tmp/unused"), timeout=1, groups=("unit",))
    assert barrier.relay_label == ""


def test_relay_transport_carries_state_without_a_state_directory(relay, tmp_path: Path) -> None:
    unit = _assignment("tests/test_unit.py::test_unit", "unit", 0)
    barrier = TestGroupBarrier.for_relay(
        ("127.0.0.1", relay.port),
        timeout=2,
        groups=("unit",),
        worker_id="gw0",
        credential=RELAY_CREDENTIAL,
    )

    barrier.initialize((unit,))
    barrier.record_terminal(unit.nodeid)

    assert list(tmp_path.iterdir()) == []
    snapshot = relay.state.snapshot()
    assert snapshot.manifest is not None
    assert snapshot.receipts[unit.nodeid]["group"] == "unit"
