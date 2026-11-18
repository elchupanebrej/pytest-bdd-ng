from __future__ import annotations

import json
from pathlib import Path

import pytest

pytest.importorskip("pydantic")

from pytest_cuke.debug_mcp.registry import (
    DiscoveryRegistryClient,
    DiscoveryRegistryError,
    parse_registry_address,
    start_registry,
)
from pytest_cuke.debug_mcp.xdist import XdistDiscoveryIndex


def _index(tmp_path: Path, session_id: str = "root-session") -> XdistDiscoveryIndex:
    directory = tmp_path / "cuke" / "debug-mcp"
    return XdistDiscoveryIndex(
        path=directory / "workers.json",
        workers_dir=directory / "workers",
        session_id=session_id,
    )


def _record(worker_id: str = "gw0", *, status: str = "waiting", root_session_id: str = "root-session") -> dict:
    return {
        "root_session_id": root_session_id,
        "worker_id": worker_id,
        "session_id": f"session-{worker_id}",
        "status": status,
        "host": "worker1",
        "debugger_endpoint": f"http://worker1:41001/mcp" if status != "closed" else None,
        "inspection_endpoint": f"http://worker1:41002/mcp" if status != "closed" else None,
        "active_failure": None,
        "last_release": None,
    }


def _read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _client(registry, *, root_session_id: str = "root-session", timeout: float = 2.0) -> DiscoveryRegistryClient:
    return DiscoveryRegistryClient(
        ("127.0.0.1", registry.port),
        worker_id="gw0",
        root_session_id=root_session_id,
        timeout=timeout,
    )


def test_registry_publishes_updates_and_removes_worker_records(tmp_path: Path) -> None:
    index = _index(tmp_path)
    index.initialize()
    index.register_worker("gw0")
    registry = start_registry(host="127.0.0.1", port=0, index=index, session_id="root-session")
    client = _client(registry)
    try:
        client.publish(_record(status="holding_failure") | {"active_failure": {"sequence": 1}})
        root = _read(index.path)
        assert root["status"] == "holding_failure"
        assert root["workers"][0]["debugger_endpoint"] == "http://worker1:41001/mcp"

        client.publish(_record(status="closed") | {"active_failure": None, "last_release": {"sequence": 1}})
        root = _read(index.path)
        assert root["status"] == "closed"
        assert root["workers"][0]["active_failure"] is None
        assert root["workers"][0]["debugger_endpoint"] is None

        client.remove("gw0")
        assert _read(index.path)["workers"] == []
        assert not index.worker_path("gw0").exists()
    finally:
        registry.stop()


def test_registry_scopes_records_to_the_root_session_and_worker(tmp_path: Path) -> None:
    index = _index(tmp_path)
    index.initialize()
    index.register_worker("gw0")
    registry = start_registry(host="127.0.0.1", port=0, index=index, session_id="root-session")
    stale = _client(registry, root_session_id="stale-session", timeout=0.2)
    try:
        with pytest.raises(DiscoveryRegistryError, match="different pytest session"):
            stale.publish(_record(root_session_id="stale-session", status="holding_failure"))
        with pytest.raises(DiscoveryRegistryError, match="different pytest session"):
            stale.remove("gw0")
        assert _read(index.path)["workers"][0]["status"] == "starting"
    finally:
        registry.stop()


def test_registry_marks_a_stopped_worker_and_clears_its_live_endpoints(tmp_path: Path) -> None:
    index = _index(tmp_path)
    index.initialize()
    index.register_worker("gw0")
    registry = start_registry(host="127.0.0.1", port=0, index=index, session_id="root-session")
    try:
        _client(registry).publish(_record(status="holding_failure") | {"active_failure": {"sequence": 3}})

        registry.state.mark_worker_down("gw0", "worker process exited")

        record = _read(index.worker_path("gw0"))
        assert record["status"] == "worker_crashed"
        assert record["debugger_endpoint"] is None
        assert record["inspection_endpoint"] is None
        assert record["active_failure"] == {"sequence": 3}
        assert record["worker_error"] == "worker process exited"
    finally:
        registry.stop()


def test_registry_redacts_recognized_secrets_from_transported_records(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("CUKE_TRANSPORT_SECRET", "transport-secret-value")
    index = _index(tmp_path)
    index.initialize()
    index.register_worker("gw0")
    registry = start_registry(
        host="127.0.0.1",
        port=0,
        index=index,
        session_id="root-session",
        redact_patterns=("transport",),
    )
    record = _record(status="holding_failure") | {
        "active_failure": {
            "sequence": 1,
            "error_message": "failed with transport-secret-value",
            "traceback": "transport-secret-value at line 1",
            "fixtures": {"api_key": "transport-secret-value"},
        }
    }
    try:
        _client(registry).publish(record)

        stored_text = index.worker_path("gw0").read_text(encoding="utf-8")
        stored = json.loads(stored_text)
        assert "transport-secret-value" not in stored_text
        assert stored["active_failure"]["error_message"] == "failed with <redacted>"
        assert stored["active_failure"]["traceback"] == "<redacted> at line 1"
        assert stored["active_failure"]["fixtures"] == {"api_key": "<redacted>"}
    finally:
        registry.stop()


def test_registry_client_fails_with_an_actionable_error_when_unreachable() -> None:
    client = DiscoveryRegistryClient(
        ("127.0.0.1", 1),
        worker_id="gw0",
        root_session_id="root-session",
        timeout=0.1,
    )

    with pytest.raises(DiscoveryRegistryError, match="cuke-mcp-registry"):
        client.publish(_record())


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("controller:8890", ("controller", 8890)),
        (" http://controller:8890 ", ("controller", 8890)),
        (" 127.0.0.1:1 ", ("127.0.0.1", 1)),
        ("", None),
        (None, None),
    ],
)
def test_parse_registry_address_accepts_host_port_or_empty(value: str | None, expected) -> None:
    assert parse_registry_address(value) == expected


@pytest.mark.parametrize("value", ["controller", "controller:0", "controller:70000", ":8890"])
def test_parse_registry_address_rejects_invalid_values(value: str) -> None:
    with pytest.raises(ValueError, match="cuke_mcp_registry must be HOST:PORT"):
        parse_registry_address(value)


@pytest.mark.parametrize("value", ["0.0.0.0:8890"])
def test_parse_registry_address_rejects_unadvertisable_wildcard_hosts(value: str) -> None:
    with pytest.raises(ValueError, match="wildcard address"):
        parse_registry_address(value)
