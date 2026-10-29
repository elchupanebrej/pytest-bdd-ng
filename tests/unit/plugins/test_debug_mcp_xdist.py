from __future__ import annotations

import hashlib
import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from types import SimpleNamespace

import pytest

pytest.importorskip("pydantic")

from pytest_cuke.debug_mcp import xdist
from pytest_cuke.debug_mcp.discovery import DiscoveryPublisher
from pytest_cuke.debug_mcp.options import DebugMcpOptions
from pytest_cuke.debug_mcp.plugin import (
    DebugMcpPlugin,
    _worker_id_for_node,
    _xdist_index_path,
    _xdist_workers_dir,
)
from pytest_cuke.debug_mcp.server import DebugMcpDependencyError


def _index(tmp_path: Path, session_id: str = "root-session") -> xdist.XdistDiscoveryIndex:
    directory = tmp_path / "cuke" / "debug-mcp"
    return xdist.XdistDiscoveryIndex(
        path=directory / "workers.json",
        workers_dir=directory / "workers",
        session_id=session_id,
    )


def _worker_record(
    worker_id: str,
    *,
    status: str = "waiting",
    root_session_id: str = "root-session",
) -> dict[str, object]:
    return {
        "root_session_id": root_session_id,
        "worker_id": worker_id,
        "session_id": f"session-{worker_id}",
        "status": status,
        "debugger_endpoint": f"http://127.0.0.1/{worker_id}/debugger" if status != "closed" else None,
        "inspection_endpoint": f"http://127.0.0.1/{worker_id}/inspection" if status != "closed" else None,
        "active_failure": None,
        "last_release": None,
    }


def _read(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def test_index_initialization_discards_stale_workers_and_publishes_sorted_records(tmp_path: Path) -> None:
    previous = _index(tmp_path, "old-session")
    previous.initialize()
    previous.publish_worker(_worker_record("gw0", root_session_id="old-session"))

    current = _index(tmp_path)
    current.initialize()
    current.register_worker("gw1")
    current.register_worker("gw0")

    index = _read(current.path)
    assert index["session_id"] == "root-session"
    assert index["status"] == "waiting"
    assert [record["worker_id"] for record in index["workers"]] == ["gw0", "gw1"]
    assert all(record["status"] == "starting" for record in index["workers"])
    assert all(record["debugger_endpoint"] is None for record in index["workers"])


def test_workers_keep_independent_failures_and_root_holds_if_any_worker_holds(tmp_path: Path) -> None:
    index = _index(tmp_path)
    index.initialize()
    index.register_worker("gw0")
    index.register_worker("gw1")

    first = _worker_record("gw0", status="holding_failure")
    first["active_failure"] = {"sequence": 1, "nodeid": "first.feature::alpha"}
    second = _worker_record("gw1")
    index.publish_worker(first)
    index.publish_worker(second)

    root = _read(index.path)
    records = {record["worker_id"]: record for record in root["workers"]}
    assert root["status"] == "holding_failure"
    assert records["gw0"]["active_failure"]["nodeid"] == "first.feature::alpha"
    assert records["gw1"]["active_failure"] is None
    assert records["gw0"]["session_id"] != records["gw1"]["session_id"]


def test_parallel_worker_publications_do_not_lose_root_index_records(tmp_path: Path) -> None:
    index = _index(tmp_path)
    index.initialize()
    worker_ids = [f"gw{number}" for number in range(8)]
    for worker_id in worker_ids:
        index.register_worker(worker_id)

    def publish(worker_id: str) -> None:
        record = _worker_record(worker_id, status="holding_failure")
        record["active_failure"] = {"sequence": 1}
        index.publish_worker(record)

    with ThreadPoolExecutor(max_workers=len(worker_ids)) as executor:
        list(executor.map(publish, worker_ids))

    root = _read(index.path)
    assert root["status"] == "holding_failure"
    assert [record["worker_id"] for record in root["workers"]] == worker_ids
    assert {record["active_failure"]["sequence"] for record in root["workers"]} == {1}


def test_worker_crash_clears_live_endpoints_and_controller_close_marks_index_closed(tmp_path: Path) -> None:
    index = _index(tmp_path)
    index.initialize()
    index.register_worker("gw0")
    index.register_worker("gw1")
    index.publish_worker(_worker_record("gw0", status="holding_failure"))
    index.publish_worker(_worker_record("gw1"))

    index.mark_worker_down("gw0", "worker process exited")
    crashed = {record["worker_id"]: record for record in _read(index.path)["workers"]}["gw0"]
    assert crashed["status"] == "worker_crashed"
    assert crashed["debugger_endpoint"] is None
    assert crashed["inspection_endpoint"] is None
    assert crashed["worker_error"] == "worker process exited"

    index.close()
    closed = _read(index.path)
    assert closed["status"] == "closed"
    workers = {record["worker_id"]: record for record in closed["workers"]}
    assert workers["gw0"]["status"] == "worker_crashed"
    assert workers["gw1"]["status"] == "worker_crashed"
    assert workers["gw1"]["debugger_endpoint"] is None


@pytest.mark.parametrize(
    "worker_record_text",
    [
        "{broken",
        json.dumps({"root_session_id": "stale-session", "worker_id": "gw0"}),
        json.dumps({"root_session_id": "root-session", "worker_id": "gw1"}),
    ],
    ids=["malformed-json", "stale-session", "wrong-worker"],
)
def test_worker_crash_recovers_cached_record_when_worker_json_is_invalid(
    tmp_path: Path,
    worker_record_text: str,
) -> None:
    index = _index(tmp_path)
    index.initialize()
    index.register_worker("gw0")
    index.register_worker("gw1")
    active = _worker_record("gw0", status="holding_failure")
    active["active_failure"] = {"sequence": 7, "nodeid": "feature.feature::scenario"}
    index.publish_worker(active)
    peer = _worker_record("gw1", status="holding_failure")
    peer["active_failure"] = {"sequence": 1, "nodeid": "feature.feature::peer"}
    index.publish_worker(peer)
    index.worker_path("gw0").write_text(worker_record_text, encoding="utf-8")

    index.mark_worker_down("gw0", "worker process exited")

    root = _read(index.path)
    records = {record["worker_id"]: record for record in root["workers"]}
    crashed = records["gw0"]
    assert root["status"] == "holding_failure"
    assert crashed["status"] == "worker_crashed"
    assert crashed["active_failure"] == active["active_failure"]
    assert crashed["session_id"] == active["session_id"]
    assert crashed["debugger_endpoint"] is None
    assert crashed["inspection_endpoint"] is None
    assert "recovered cached state" in crashed["worker_error"]
    assert _read(index.worker_path("gw0")) == crashed
    assert records["gw1"] == peer


def test_normal_worker_exit_with_invalid_record_clears_cached_endpoints(tmp_path: Path) -> None:
    index = _index(tmp_path)
    index.initialize()
    index.register_worker("gw0")
    active = _worker_record("gw0", status="holding_failure")
    active["active_failure"] = {"sequence": 7, "nodeid": "feature.feature::scenario"}
    index.publish_worker(active)
    index.worker_path("gw0").write_text("{broken", encoding="utf-8")
    config = SimpleNamespace(
        pluginmanager=SimpleNamespace(get_plugin=lambda name: object()),
        option=SimpleNamespace(numprocesses=2),
    )
    plugin = DebugMcpPlugin(config=config, options=DebugMcpOptions(enabled=True))
    plugin.xdist_index = index

    plugin.pytest_testnodedown(SimpleNamespace(workerinput={"workerid": "gw0"}), error=None)

    root = _read(index.path)
    crashed = root["workers"][0]
    assert root["status"] == "closed"
    assert crashed["status"] == "worker_crashed"
    assert crashed["active_failure"] == active["active_failure"]
    assert crashed["debugger_endpoint"] is None
    assert crashed["inspection_endpoint"] is None
    assert "could not read worker discovery file" in crashed["worker_error"]


def test_normal_worker_exit_with_closed_record_from_stale_session_clears_cached_endpoints(tmp_path: Path) -> None:
    index = _index(tmp_path)
    index.initialize()
    index.register_worker("gw0")
    active = _worker_record("gw0", status="holding_failure")
    active["active_failure"] = {"sequence": 7, "nodeid": "feature.feature::scenario"}
    index.publish_worker(active)
    stale_closed = _worker_record("gw0", status="closed")
    stale_closed["session_id"] = "stale-worker-session"
    index.worker_path("gw0").write_text(json.dumps(stale_closed), encoding="utf-8")
    config = SimpleNamespace(
        pluginmanager=SimpleNamespace(get_plugin=lambda name: object()),
        option=SimpleNamespace(numprocesses=2),
    )
    plugin = DebugMcpPlugin(config=config, options=DebugMcpOptions(enabled=True))
    plugin.xdist_index = index

    plugin.pytest_testnodedown(SimpleNamespace(workerinput={"workerid": "gw0"}), error=None)

    root = _read(index.path)
    crashed = root["workers"][0]
    assert crashed["status"] == "worker_crashed"
    assert crashed["session_id"] == active["session_id"]
    assert crashed["active_failure"] == active["active_failure"]
    assert crashed["debugger_endpoint"] is None
    assert crashed["inspection_endpoint"] is None
    assert "session ID mismatch" in crashed["worker_error"]


def test_clear_previous_removes_old_xdist_discovery_before_standalone_start(tmp_path: Path) -> None:
    index = _index(tmp_path)
    index.initialize()
    index.register_worker("gw0")

    _index(tmp_path, "standalone-session").clear_previous()

    assert not index.path.exists()
    assert list(index.workers_dir.glob("*.json")) == []


def test_stale_worker_cannot_replace_or_remove_current_session_record(tmp_path: Path) -> None:
    current = _index(tmp_path, "current-session")
    current.initialize()
    current.register_worker("gw0")
    current_record = _worker_record("gw0", root_session_id="current-session", status="holding_failure")
    current_record["active_failure"] = {"sequence": 1, "nodeid": "current-run.feature::active"}
    current.publish_worker(current_record)
    stale = _index(tmp_path, "stale-session")
    stale_publisher = DiscoveryPublisher(
        path=current.worker_path("gw0"),
        session_id="stale-worker-session",
        host="127.0.0.1",
        debugger_endpoint="http://127.0.0.1:41001/mcp",
        inspection_endpoint="http://127.0.0.1:41002/mcp",
        debugger_pid=4321,
        worker_id="gw0",
        root_session_id="stale-session",
        on_publish=stale.publish_worker,
        on_remove=stale.remove_worker,
    )

    with pytest.raises(xdist.XdistDiscoveryError, match="root discovery index belongs to a different pytest session"):
        stale_publisher.write_initial()
    with pytest.raises(xdist.XdistDiscoveryError, match="root discovery index belongs to a different pytest session"):
        stale_publisher.remove()

    assert _read(current.worker_path("gw0")) == current_record
    current_index = _read(current.path)
    assert current_index["session_id"] == "current-session"
    assert current_index["workers"] == [current_record]


def test_stale_controller_cannot_close_a_newer_session_index(tmp_path: Path) -> None:
    current = _index(tmp_path, "current-session")
    current.initialize()
    current.register_worker("gw0")
    stale_controller = _index(tmp_path, "stale-session")

    with pytest.raises(xdist.XdistDiscoveryError, match="refusing to close another pytest session"):
        stale_controller.close()

    current_index = _read(current.path)
    assert current_index["session_id"] == "current-session"
    assert current_index["status"] == "waiting"
    assert current_index["workers"][0]["status"] == "starting"


def test_safe_worker_id_avoids_traversal_and_hashes_transformed_ids() -> None:
    safe = xdist.safe_worker_id("../../remote:gateway/0")

    assert "/" not in safe
    assert "\\" not in safe
    assert safe.endswith(hashlib.sha256(b"../../remote:gateway/0").hexdigest()[:16])


def test_colliding_safe_worker_ids_fail_explicitly(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(xdist, "safe_worker_id", lambda worker_id: "same-filename")
    index = _index(tmp_path)
    index.initialize()
    index.register_worker("gateway/a")

    with pytest.raises(xdist.XdistDiscoveryError, match="map to the same safe discovery filename"):
        index.register_worker("gateway?a")


def test_malformed_worker_record_returns_a_bounded_discovery_error(tmp_path: Path) -> None:
    index = _index(tmp_path)
    index.initialize()
    index.worker_path("gw0").write_text("{broken", encoding="utf-8")

    with pytest.raises(xdist.XdistDiscoveryError, match="could not read worker discovery file"):
        index.register_worker("gw1")


def test_worker_from_another_root_session_is_rejected(tmp_path: Path) -> None:
    index = _index(tmp_path)
    index.initialize()
    stale_path = index.worker_path("gw0")
    stale_path.parent.mkdir(parents=True, exist_ok=True)
    stale_path.write_text(json.dumps({"worker_id": "gw0", "root_session_id": "old-session"}), encoding="utf-8")

    with pytest.raises(xdist.XdistDiscoveryError, match="stale worker discovery record"):
        index.register_worker("gw1")


def test_unavailable_index_lock_fails_fast_with_actionable_error(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    index = _index(tmp_path)
    index.path.parent.mkdir(parents=True)

    class UnavailableLock:
        def __init__(self, path: str, timeout: float) -> None:
            self.path = path
            self.timeout = timeout

        def acquire(self, timeout: float) -> None:
            raise PermissionError("lock denied")

        def release(self) -> None:
            return None

    monkeypatch.setattr(xdist, "FileLock", UnavailableLock)
    with pytest.raises(xdist.XdistDiscoveryError, match="could not acquire worker discovery lock"):
        index.initialize()


def test_unavailable_discovery_root_fails_with_actionable_error(tmp_path: Path) -> None:
    blocked_root = tmp_path / "cache-is-a-file"
    blocked_root.write_text("not a directory", encoding="utf-8")
    index = xdist.XdistDiscoveryIndex(
        path=blocked_root / "cuke" / "debug-mcp" / "workers.json",
        workers_dir=blocked_root / "cuke" / "debug-mcp" / "workers",
        session_id="root-session",
    )

    with pytest.raises(xdist.XdistDiscoveryError, match="could not create worker discovery root directory"):
        index.initialize()


def test_filesystem_error_inside_lock_is_not_reported_as_lock_acquisition_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    index = _index(tmp_path)
    index.initialize()
    marker = index.workers_dir / "unremovable.json"
    marker.write_text("{}", encoding="utf-8")
    unlink = Path.unlink

    def fail_marker_unlink(path: Path, *, missing_ok: bool = False) -> None:
        if path == marker:
            raise PermissionError("worker discovery file is not writable")
        unlink(path, missing_ok=missing_ok)

    monkeypatch.setattr(Path, "unlink", fail_marker_unlink)

    with pytest.raises(PermissionError, match="worker discovery file is not writable"):
        index.clear_previous()


def test_xdist_detection_and_worker_ids_cover_workers_gateways_and_local_specs() -> None:
    worker_config = SimpleNamespace(workerinput={"workerid": "gw2"})
    assert xdist.xdist_worker_id(worker_config) == "gw2"
    assert xdist.xdist_root_session_id(
        SimpleNamespace(workerinput={"cuke_debug_mcp_root_session_id": "root-7"})
    ) == "root-7"
    assert xdist.is_xdist_controller(SimpleNamespace(pluginmanager=SimpleNamespace(get_plugin=lambda name: object())))
    assert xdist.is_local_xdist_spec(SimpleNamespace(popen=True))
    assert not xdist.is_local_xdist_spec(SimpleNamespace(popen=False))
    assert _worker_id_for_node(SimpleNamespace(workerinput={}, gateway=SimpleNamespace(id="gw3"))) == "gw3"


def test_plugin_xdist_paths_share_the_debug_mcp_cache_root(tmp_path: Path) -> None:
    config = SimpleNamespace(
        rootpath=tmp_path,
        option=SimpleNamespace(cache_dir=None),
        getini=lambda name: ".pytest_cache",
    )

    assert _xdist_index_path(config) == tmp_path / ".pytest_cache" / "cuke" / "debug-mcp" / "workers.json"
    assert _xdist_workers_dir(config) == tmp_path / ".pytest_cache" / "cuke" / "debug-mcp" / "workers"


def test_remote_gateway_is_rejected_before_worker_startup() -> None:
    plugin = DebugMcpPlugin(config=SimpleNamespace(), options=DebugMcpOptions(enabled=True))

    with pytest.raises(pytest.UsageError, match="remote gateways are unsupported"):
        plugin.pytest_xdist_setupnodes([SimpleNamespace(popen=False)])


def test_xdist_worker_rejects_a_fixed_debugger_port(tmp_path: Path) -> None:
    config = SimpleNamespace(
        rootpath=tmp_path,
        option=SimpleNamespace(cache_dir=None),
        getini=lambda name: ".pytest_cache",
        workerinput={"cuke_debug_mcp_root_session_id": "root-session"},
    )
    plugin = DebugMcpPlugin(
        config=config,
        options=DebugMcpOptions(enabled=True, port=43210),
    )
    plugin.worker_id = "gw0"

    with pytest.raises(DebugMcpDependencyError, match="need --cuke-mcp-port=auto"):
        plugin._start_xdist_worker()
