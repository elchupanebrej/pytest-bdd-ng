from __future__ import annotations

import json

from pytest_cuke.debug_mcp.discovery import DiscoveryPublisher
from pytest_cuke.debug_mcp.plugin import _outline_context
from pytest_cuke.debug_mcp.xdist import XdistDiscoveryIndex
from pytest_cuke.model import Feature, Scenario
from pytest_cuke.model.examples import Examples
from pytest_cuke.model.table import TableCell, TableRow


def test_discovery_publishes_active_state_and_clears_endpoints_on_close(tmp_path) -> None:
    path = tmp_path / "cuke" / "debug-mcp" / "session.json"
    publisher = DiscoveryPublisher(
        path=path,
        session_id="session-1",
        host="127.0.0.1",
        debugger_endpoint="http://127.0.0.1:40001/mcp",
        inspection_endpoint="http://127.0.0.1:40002/mcp",
        debugger_pid=1234,
    )

    publisher.write_initial()
    initial = json.loads(path.read_text(encoding="utf-8"))
    assert initial["status"] == "waiting"
    assert initial["debugger_endpoint"].endswith(":40001/mcp")

    publisher.publish_queue_state(
        {
            "status": "holding_failure",
            "active_failure": {"sequence": 1, "phase": "call"},
            "last_release": None,
        }
    )
    active = json.loads(path.read_text(encoding="utf-8"))
    assert active["active_failure"]["sequence"] == 1

    publisher.close({"sequence": 1, "reason": "explicit", "artifact_status": "missing"})
    closed = json.loads(path.read_text(encoding="utf-8"))
    assert closed["status"] == "closed"
    assert closed["debugger_endpoint"] is None
    assert closed["inspection_endpoint"] is None
    assert closed["active_failure"] is None
    assert closed["last_release"]["reason"] == "explicit"


def test_worker_discovery_updates_its_record_and_the_root_index(tmp_path) -> None:
    directory = tmp_path / "cuke" / "debug-mcp"
    index = XdistDiscoveryIndex(
        path=directory / "workers.json",
        workers_dir=directory / "workers",
        session_id="root-session",
    )
    index.initialize()
    index.register_worker("gw0")
    publisher = DiscoveryPublisher(
        path=index.worker_path("gw0"),
        session_id="worker-session",
        host="127.0.0.1",
        debugger_endpoint="http://127.0.0.1:40001/mcp",
        inspection_endpoint="http://127.0.0.1:40002/mcp",
        debugger_pid=1234,
        worker_id="gw0",
        root_session_id="root-session",
        on_publish=index.publish_worker,
        on_remove=index.remove_worker,
    )

    publisher.write_initial()
    publisher.publish_queue_state(
        {
            "status": "holding_failure",
            "active_failure": {"sequence": 1, "nodeid": "features/example.feature::scenario"},
            "last_release": None,
        }
    )

    record = json.loads(index.worker_path("gw0").read_text(encoding="utf-8"))
    root = json.loads(index.path.read_text(encoding="utf-8"))
    assert record["session_id"] == "worker-session"
    assert record["worker_id"] == "gw0"
    assert record["active_failure"]["sequence"] == 1
    assert root["status"] == "holding_failure"
    assert root["workers"][0]["active_failure"]["nodeid"] == "features/example.feature::scenario"

    publisher.close()
    closed = json.loads(index.path.read_text(encoding="utf-8"))
    assert closed["status"] == "closed"
    assert closed["workers"][0]["status"] == "closed"
    assert closed["workers"][0]["debugger_endpoint"] is None

    publisher.remove()
    assert json.loads(index.path.read_text(encoding="utf-8"))["workers"] == []


def test_outline_context_retains_row_values_and_source_identity() -> None:
    row = TableRow(
        cells=(TableCell(value="outline-row-17"), TableCell(value="debug MCP failure sentinel")),
        line=24,
        id="row-id-17",
    )
    original = Scenario(
        name="The client can inspect <probe_id>",
        id="scenario-id",
        examples=(
            Examples(
                header=TableRow(cells=(TableCell(value="probe_id"), TableCell(value="message"))),
                rows=(row,),
            ),
        ),
    )
    expanded = Scenario(
        name="The client can inspect <probe_id>[table_rows:[line:24]]",
        source_ast_node_ids=("scenario-id", "row-id-17"),
    )
    feature = Feature(name="MCP failure inspection", scenarios=(original,))

    values, identity = _outline_context(feature, expanded)

    assert values == {"probe_id": "outline-row-17", "message": "debug MCP failure sentinel"}
    assert identity == {
        "section_index": 1,
        "row_index": 1,
        "source_line": 24,
        "row_id": "row-id-17",
    }
