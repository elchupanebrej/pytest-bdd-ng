"""
xdist-aware discovery support for debug MCP.

Responsibility:
    xdist-aware discovery support for debug MCP. It directly owns the observable contract, local decisions, and
    maintenance boundary for this module.

Reason for existence:
    This entity is the information expert for `pytest_bdd.plugin.debug_mcp.xdist` because it keeps the nearest code,
    data shape, call signature, and failure knowledge together.

Delegates:
    - is_debug_mcp_worker: owns nested behavior below this boundary
    - worker_id_for_config: owns nested behavior below this boundary
    - worker_discovery_dir: owns nested behavior below this boundary
    - worker_discovery_path: owns nested behavior below this boundary
    - debug_mcp_discovery_path: owns nested behavior below this boundary
    - write_debug_mcp_discovery: owns nested behavior below this boundary

Cohesion:
    The implementation stays together because its imports, calls, state writes, and return contract describe one
    maintainable decision unit.

Separation:
    - module peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
      widening caller knowledge.

Main consumers:
    - None found by static import/name scan; verify dynamic use before refactor

State and side effects:
    mutates worker_id, payload, gateway_mode, resolved_worker_id, worker_path; depends on __future__.annotations, json,
    pathlib.Path, tempfile.NamedTemporaryFile, typing.TYPE_CHECKING.

Invariants:
    - `pytest_bdd.plugin.debug_mcp.xdist` keeps its documented import path, ownership boundary, and observable behavior
      stable for callers.

Architecture score:
    #arch-eval:reason_for_existence=4
    #arch-eval:owned_responsibility=4
    #arch-eval:delegation_boundary=4
    #arch-eval:cohesion=3
    #arch-eval:separation=3
    #arch-eval:consumer_clarity=2
    #arch-eval:state_invariants=4
    #arch-eval:entity_fullness=4
    #arch-eval:locational_stability=2
"""

from __future__ import annotations

import json
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import TYPE_CHECKING, Any, cast

from filelock import FileLock

from pytest_bdd.util.live_reporting import (
    format_reporting_worker_id,
    is_xdist_worker_process,
    resolve_reporting_worker_identity,
)

from .discovery import ConfigWithRootpath, SessionDiscovery, discovery_dir, discovery_path, write_discovery_file

if TYPE_CHECKING:
    from pytest_bdd.compatibility.pytest import Config

    from .state import DebugMcpState


def is_debug_mcp_worker(config: ConfigWithRootpath) -> bool:
    """
    Return whether config belongs to an xdist worker.

    Returns:
        True for worker processes.

    Responsibility:
        Return whether config belongs to an xdist worker. It directly owns the observable contract, local decisions, and
        maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.plugin.debug_mcp.xdist.is_debug_mcp_worker` because it
        keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - is_xdist_worker_process: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - None found by static import/name scan; verify dynamic use before refactor

    State and side effects:
        keeps no local persistent state beyond call-local values.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=2
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=2

    """
    return is_xdist_worker_process(config)  # type: ignore[arg-type]  # runtime duck-typing with ConfigWithRootpath


def worker_id_for_config(config: ConfigWithRootpath) -> str:
    """
    Resolve a stable worker id for discovery files.

    Returns:
        Human-readable worker id.

    Responsibility:
        Resolve a stable worker id for discovery files. It directly owns the observable contract, local decisions, and
        maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.plugin.debug_mcp.xdist.worker_id_for_config` because it
        keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - resolve_reporting_worker_identity: collaborator call used by this boundary
        - cast: collaborator call used by this boundary
        - format_reporting_worker_id: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - None found by static import/name scan; verify dynamic use before refactor

    State and side effects:
        mutates worker_id, gateway_mode.

    Invariants:
        - `pytest_bdd.plugin.debug_mcp.xdist.worker_id_for_config` keeps its documented import path, ownership boundary,
          and observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=2
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=2

    """
    worker_id, gateway_mode = resolve_reporting_worker_identity(
        cast("Config", config),
        gateway_mode_resolver=lambda _: None,
    )
    return format_reporting_worker_id(worker_id, gateway_mode)


def worker_discovery_dir(config: ConfigWithRootpath) -> Path:
    """
    Return worker discovery directory.

    Returns:
        Path to `.pytest_cache/mcp-pdb/workers`.

    Responsibility:
        Return worker discovery directory. It directly owns the observable contract, local decisions, and maintenance
        boundary for this function. That boundary is intentionally stated in prose so maintainers can distinguish owned
        work from collaborators before editing.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.plugin.debug_mcp.xdist.worker_discovery_dir` because it
        keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - discovery_dir: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - None found by static import/name scan; verify dynamic use before refactor

    State and side effects:
        keeps no local persistent state beyond call-local values.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=2
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=2

    """
    return discovery_dir(config) / "workers"


def worker_discovery_path(config: ConfigWithRootpath, worker_id: str | None = None) -> Path:
    """
    Return discovery path for a worker.

    Returns:
        Worker-specific JSON path.

    Responsibility:
        Return discovery path for a worker. It directly owns the observable contract, local decisions, and maintenance
        boundary for this function. That boundary is intentionally stated in prose so maintainers can distinguish owned
        work from collaborators before editing.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.plugin.debug_mcp.xdist.worker_discovery_path` because it
        keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - worker_id_for_config: collaborator call used by this boundary
        - worker_discovery_dir: collaborator call used by this boundary
        - _safe_worker_id: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - None found by static import/name scan; verify dynamic use before refactor

    State and side effects:
        mutates resolved_worker_id.

    Invariants:
        - `pytest_bdd.plugin.debug_mcp.xdist.worker_discovery_path` keeps its documented import path, ownership
          boundary, and observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=2
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=2

    """
    resolved_worker_id = worker_id or worker_id_for_config(config)
    return worker_discovery_dir(config) / f"{_safe_worker_id(resolved_worker_id)}.json"


def debug_mcp_discovery_path(config: ConfigWithRootpath) -> Path:
    """
    Return the process-local discovery path.

    Returns:
        Worker path for xdist workers, otherwise root session path.

    Responsibility:
        Return the process-local discovery path. It directly owns the observable contract, local decisions, and
        maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.plugin.debug_mcp.xdist.debug_mcp_discovery_path` because
        it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - is_debug_mcp_worker: collaborator call used by this boundary
        - worker_discovery_path: collaborator call used by this boundary
        - discovery_path: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/debug_mcp/entrypoint.py: imports or references `debug_mcp_discovery_path`

    State and side effects:
        keeps no local persistent state beyond call-local values.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=3

    """
    if is_debug_mcp_worker(config):
        return worker_discovery_path(config)
    return discovery_path(config)


def write_debug_mcp_discovery(
    config: ConfigWithRootpath,
    state: DebugMcpState,
    discovery: SessionDiscovery,
) -> None:
    """
    Write process-local discovery and update the root worker index when needed.

    Responsibility:
        Write process-local discovery and update the root worker index when needed. It directly owns the observable
        contract, local decisions, and maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.plugin.debug_mcp.xdist.write_debug_mcp_discovery` because
        it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - write_discovery_file: collaborator call used by this boundary
        - is_debug_mcp_worker: collaborator call used by this boundary
        - discovery_path: collaborator call used by this boundary
        - worker_id_for_config: collaborator call used by this boundary
        - worker_discovery_path: collaborator call used by this boundary
        - write_worker_index: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/debug_mcp/entrypoint.py: imports or references `write_debug_mcp_discovery`

    State and side effects:
        mutates worker_id, worker_path.

    Invariants:
        - `pytest_bdd.plugin.debug_mcp.xdist.write_debug_mcp_discovery` keeps its documented import path, ownership
          boundary, and observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=3
    """
    if not is_debug_mcp_worker(config):
        write_discovery_file(discovery_path(config), discovery)
        return
    worker_id = worker_id_for_config(config)
    worker_path = worker_discovery_path(config, worker_id)
    write_discovery_file(worker_path, discovery)
    write_worker_index(config, state)


def write_worker_index(config: ConfigWithRootpath, state: DebugMcpState) -> None:
    """
    Merge worker discovery files into the root session index.

    Responsibility:
        Merge worker discovery files into the root session index. It directly owns the observable contract, local
        decisions, and maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.plugin.debug_mcp.xdist.write_worker_index` because it
        keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - discovery_path: collaborator call used by this boundary
        - FileLock: collaborator call used by this boundary
        - str: collaborator call used by this boundary
        - root_path.with_suffix: collaborator call used by this boundary
        - _read_worker_entries: collaborator call used by this boundary
        - _combined_status: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - None found by static import/name scan; verify dynamic use before refactor

    State and side effects:
        mutates root_path, lock, workers, payload.

    Invariants:
        - `pytest_bdd.plugin.debug_mcp.xdist.write_worker_index` keeps its documented import path, ownership boundary,
          and observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=2
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=2
    """
    root_path = discovery_path(config)
    lock = FileLock(str(root_path.with_suffix(".lock")))
    with lock:
        workers = _read_worker_entries(config)
        payload = {
            "session_id": state.session_id,
            "status": _combined_status(workers),
            "workers": workers,
        }
        _write_json(root_path, payload)


def _read_worker_entries(config: ConfigWithRootpath) -> list[dict[str, Any]]:
    """
    Responsibility:
        Responsibility: Responsibility: `pytest_bdd.plugin.debug_mcp.xdist._read_worker_entries` owns documented
        function behavior. It directly owns the observable contract, local decisions, and maintenance boundary for this
        function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.plugin.debug_mcp.xdist._read_worker_entries` because it
        keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - worker_discovery_dir: collaborator call used by this boundary
        - workers_dir.exists: collaborator call used by this boundary
        - sorted: collaborator call used by this boundary
        - workers_dir.glob: collaborator call used by this boundary
        - json.loads: collaborator call used by this boundary
        - path.read_text: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - None found by static import/name scan; verify dynamic use before refactor

    State and side effects:
        mutates entries, workers_dir, payload, worker_id.

    Invariants:
        - `pytest_bdd.plugin.debug_mcp.xdist._read_worker_entries` keeps its documented import path, ownership boundary,
          and observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=2
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=2
    """
    entries: list[dict[str, Any]] = []
    workers_dir = worker_discovery_dir(config)
    if not workers_dir.exists():
        return entries
    for path in sorted(workers_dir.glob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        worker_id = path.stem
        payload["worker_id"] = worker_id
        entries.append(payload)
    return entries


def _combined_status(workers: list[dict[str, Any]]) -> str:
    """
    Responsibility:
        Responsibility: Responsibility: `pytest_bdd.plugin.debug_mcp.xdist._combined_status` owns documented function
        behavior. It directly owns the observable contract, local decisions, and maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.plugin.debug_mcp.xdist._combined_status` because it keeps
        the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - any: collaborator call used by this boundary
        - worker.get: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - None found by static import/name scan; verify dynamic use before refactor

    State and side effects:
        keeps no local persistent state beyond call-local values.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=2
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=2
    """
    if any(worker.get("status") == "holding_failure" for worker in workers):
        return "holding_failure"
    if workers:
        return "waiting_for_failure"
    return "waiting_for_failure"


def _safe_worker_id(worker_id: str) -> str:
    """
    Responsibility:
        Responsibility: Responsibility: `pytest_bdd.plugin.debug_mcp.xdist._safe_worker_id` owns documented function
        behavior. It directly owns the observable contract, local decisions, and maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.plugin.debug_mcp.xdist._safe_worker_id` because it keeps
        the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - join: collaborator call used by this boundary
        - char.isalnum: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - None found by static import/name scan; verify dynamic use before refactor

    State and side effects:
        keeps no local persistent state beyond call-local values.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=2
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=2
    """
    return "".join(char if char.isalnum() or char in {"-", "_", "."} else "-" for char in worker_id)


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    """
    Responsibility:
        Responsibility: Responsibility: `pytest_bdd.plugin.debug_mcp.xdist._write_json` owns documented function
        behavior. It directly owns the observable contract, local decisions, and maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.plugin.debug_mcp.xdist._write_json` because it keeps the
        nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - tmp.write: collaborator call used by this boundary
        - path.parent.mkdir: collaborator call used by this boundary
        - json.dumps: collaborator call used by this boundary
        - NamedTemporaryFile: collaborator call used by this boundary
        - Path: collaborator call used by this boundary
        - tmp_path.replace: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - None found by static import/name scan; verify dynamic use before refactor

    State and side effects:
        mutates content, tmp_path.

    Invariants:
        - `pytest_bdd.plugin.debug_mcp.xdist._write_json` keeps its documented import path, ownership boundary, and
          observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=2
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=2
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    content = json.dumps(payload, indent=2, sort_keys=True)
    with NamedTemporaryFile("w", encoding="utf-8", delete=False, dir=path.parent, prefix=f".{path.name}.") as tmp:
        tmp.write(content)
        tmp.write("\n")
        tmp_path = Path(tmp.name)
    tmp_path.replace(path)
