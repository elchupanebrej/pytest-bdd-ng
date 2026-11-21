from __future__ import annotations

import http.client
import json
import os
import time
from pathlib import Path
from types import SimpleNamespace

import pytest

from pytest_cuke.test_groups.assignment import TestGroupAssignment, TestGroupAssignmentSource
from pytest_cuke.test_groups.barrier import (
    TestGroupBarrier,
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
        ("call", "passed", True),
        ("call", "failed", True),
        ("call", "skipped", True),
        ("call", "rerun", False),
        ("setup", "failed", True),
        ("setup", "skipped", True),
        ("setup", "passed", False),
    ],
)
def test_plugin_records_only_terminal_reports(when: str, outcome: str, should_record: bool) -> None:
    plugin = object.__new__(TestGroupPlugin)
    recorded: list[str] = []
    plugin.barrier = SimpleNamespace(record_terminal=recorded.append)

    plugin.pytest_runtest_logreport(SimpleNamespace(when=when, outcome=outcome, nodeid="test-id"))

    assert recorded == (["test-id"] if should_record else [])


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


def test_plugin_shares_the_relay_credential_with_each_worker() -> None:
    plugin = object.__new__(TestGroupPlugin)
    plugin.relay_credential = "per-run-credential"
    node = SimpleNamespace(workerinput={})

    plugin.pytest_configure_node(node)

    assert node.workerinput["cuke_test_group_relay_credential"] == "per-run-credential"


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
