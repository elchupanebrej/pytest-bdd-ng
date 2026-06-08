"""
Discovery file support for debug MCP sessions.

Responsibility:
    Discovery file support for debug MCP sessions. It directly owns the observable contract, local decisions, and
    maintenance boundary for this module.

Reason for existence:
    This entity is the information expert for `pytest_bdd.plugin.debug_mcp.discovery` because it keeps the nearest code,
    data shape, call signature, and failure knowledge together.

Delegates:
    - ConfigWithRootpath: owns nested behavior below this boundary
    - SessionDiscovery: owns nested behavior below this boundary
    - allocate_local_port: owns nested behavior below this boundary
    - discovery_dir: owns nested behavior below this boundary
    - discovery_path: owns nested behavior below this boundary
    - write_discovery_file: owns nested behavior below this boundary

Cohesion:
    The implementation stays together because its imports, calls, state writes, and return contract describe one
    maintainable decision unit.

Separation:
    - module peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
      widening caller knowledge.

Main consumers:
    - src/pytest_bdd/plugin/debug_mcp/entrypoint.py: imports or references `discovery`
    - src/pytest_bdd/plugin/debug_mcp/queue.py: imports or references `discovery`
    - src/pytest_bdd/plugin/debug_mcp/xdist.py: imports or references `discovery`

State and side effects:
    mutates msg, session_id, status, host, mcp_pdb; depends on __future__.annotations, json, socket, pathlib.Path,
    tempfile.NamedTemporaryFile.

Invariants:
    - `pytest_bdd.plugin.debug_mcp.discovery` keeps its documented import path, ownership boundary, and observable
      behavior stable for callers.

Failure semantics:
    Raises or re-raises ValueError; callers must treat these as boundary failures.

Architecture score:
    #arch-eval:reason_for_existence=4
    #arch-eval:owned_responsibility=4
    #arch-eval:delegation_boundary=4
    #arch-eval:cohesion=3
    #arch-eval:separation=3
    #arch-eval:consumer_clarity=4
    #arch-eval:state_invariants=4
    #arch-eval:entity_fullness=4
    #arch-eval:locational_stability=4
"""

from __future__ import annotations

import json
import socket
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import TYPE_CHECKING, Literal, Protocol

import attrs

if TYPE_CHECKING:
    from typing import Any

    from .state import DebugMcpState, Endpoint


class ConfigWithRootpath(Protocol):
    """
    Protocol for pytest config cache path needs.

    Responsibility:
        Protocol for pytest config cache path needs. It directly owns the observable contract, local decisions, and
        maintenance boundary for this class.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.plugin.debug_mcp.discovery.ConfigWithRootpath` because it
        keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - rootpath: owns nested behavior below this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/debug_mcp/xdist.py: imports or references `ConfigWithRootpath`

    State and side effects:
        keeps no local persistent state beyond call-local values.

    Invariants:
        - `pytest_bdd.plugin.debug_mcp.discovery.ConfigWithRootpath` keeps its documented import path, ownership
          boundary, and observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=3
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=3
        #arch-eval:locational_stability=3
    """

    @property
    def rootpath(self) -> Path:
        """
        Return pytest root path.

        Returns:
            Pytest root path.

        Responsibility:
            Return pytest root path. It directly owns the observable contract, local decisions, and maintenance boundary
            for this method. That boundary is intentionally stated in prose so maintainers can distinguish owned work
            from collaborators before editing.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.debug_mcp.discovery.ConfigWithRootpath.rootpath` because it keeps the nearest code, data
            shape, call signature, and failure knowledge together.

        Delegates:
            - None, leaf-level implementation boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/feature_locator.py: imports or references `rootpath`
            - src/pytest_bdd/plugin/gherkin_message_reporter/hook_catalog_runtime.py: imports or references `rootpath`
            - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_core.py: imports or references
              `rootpath`
            - src/pytest_bdd/plugin/gherkin_message_reporter/live_formatter_node.py: imports or references `rootpath`
            - src/pytest_bdd/plugin/gherkin_message_reporter/live_formatter_payload.py: imports or references `rootpath`

        State and side effects:
            keeps no local persistent state beyond call-local values.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=2
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=3
            #arch-eval:entity_fullness=3
            #arch-eval:locational_stability=4

        """
        ...


@attrs.define(frozen=True, slots=True)
class SessionDiscovery:
    """
    Serializable debug MCP session discovery.

    Responsibility:
        Serializable debug MCP session discovery. It directly owns the observable contract, local decisions, and
        maintenance boundary for this class.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.plugin.debug_mcp.discovery.SessionDiscovery` because it
        keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - waiting: owns nested behavior below this boundary
        - holding: owns nested behavior below this boundary
        - as_dict: owns nested behavior below this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/debug_mcp/entrypoint.py: imports or references `SessionDiscovery`
        - src/pytest_bdd/plugin/debug_mcp/queue.py: imports or references `SessionDiscovery`
        - src/pytest_bdd/plugin/debug_mcp/xdist.py: imports or references `SessionDiscovery`

    State and side effects:
        mutates msg, session_id, status, host, mcp_pdb.

    Invariants:
        - `pytest_bdd.plugin.debug_mcp.discovery.SessionDiscovery` keeps its documented import path, ownership boundary,
          and observable behavior stable for callers.

    Failure semantics:
        Raises or re-raises ValueError; callers must treat these as boundary failures.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=3
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=4
    """

    session_id: str
    status: Literal["waiting_for_failure", "holding_failure", "connected", "closed"]
    host: str
    mcp_pdb: Endpoint
    sidecar: Endpoint
    active_failure: dict[str, Any] | None = None

    @classmethod
    def waiting(cls, state: DebugMcpState) -> SessionDiscovery:
        """
        Build waiting-for-failure discovery for a new session.

        Returns:
            Discovery payload for a session with no active failure.

        Raises:
            ValueError: If endpoints have not been initialized.

        Responsibility:
            Build waiting-for-failure discovery for a new session. It directly owns the observable contract, local
            decisions, and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.plugin.debug_mcp.discovery.SessionDiscovery.waiting`
            because it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - ValueError: collaborator call used by this boundary
            - cls: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/debug_mcp/entrypoint.py: imports or references `waiting`

        State and side effects:
            mutates msg.

        Invariants:
            - `pytest_bdd.plugin.debug_mcp.discovery.SessionDiscovery.waiting` keeps its documented import path,
              ownership boundary, and observable behavior stable for callers.

        Failure semantics:
            Raises or re-raises ValueError; callers must treat these as boundary failures.

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
        if state.mcp_pdb_endpoint is None or state.sidecar_endpoint is None:
            msg = "Debug MCP endpoints are not initialized."
            raise ValueError(msg)
        return cls(
            session_id=state.session_id,
            status="waiting_for_failure",
            host=state.options.host,
            mcp_pdb=state.mcp_pdb_endpoint,
            sidecar=state.sidecar_endpoint,
        )

    @classmethod
    def holding(cls, state: DebugMcpState, active_failure: dict[str, Any]) -> SessionDiscovery:
        """
        Build holding-failure discovery for an active queue entry.

        Returns:
            Discovery payload with active failure metadata.

        Raises:
            ValueError: If endpoints have not been initialized.

        Responsibility:
            Build holding-failure discovery for an active queue entry. It directly owns the observable contract, local
            decisions, and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.plugin.debug_mcp.discovery.SessionDiscovery.holding`
            because it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - ValueError: collaborator call used by this boundary
            - cls: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/debug_mcp/queue.py: imports or references `holding`

        State and side effects:
            mutates msg.

        Invariants:
            - `pytest_bdd.plugin.debug_mcp.discovery.SessionDiscovery.holding` keeps its documented import path,
              ownership boundary, and observable behavior stable for callers.

        Failure semantics:
            Raises or re-raises ValueError; callers must treat these as boundary failures.

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
        if state.mcp_pdb_endpoint is None or state.sidecar_endpoint is None:
            msg = "Debug MCP endpoints are not initialized."
            raise ValueError(msg)
        return cls(
            session_id=state.session_id,
            status="holding_failure",
            host=state.options.host,
            mcp_pdb=state.mcp_pdb_endpoint,
            sidecar=state.sidecar_endpoint,
            active_failure=active_failure,
        )

    def as_dict(self) -> dict[str, Any]:
        """
        Return JSON-compatible discovery payload.

        Returns:
            Dictionary ready for JSON serialization.

        Responsibility:
            Return JSON-compatible discovery payload. It directly owns the observable contract, local decisions, and
            maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.plugin.debug_mcp.discovery.SessionDiscovery.as_dict`
            because it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - attrs.asdict: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/model/message_transport.py: imports or references `as_dict`
            - src/pytest_bdd/model/run/lifecycle/_run.py: imports or references `as_dict`
            - src/pytest_bdd/model/run/lifecycle/_snapshots.py: imports or references `as_dict`
            - src/pytest_bdd/model/run/lifecycle/_states.py: imports or references `as_dict`
            - src/pytest_bdd/model/scenario_run.py: imports or references `as_dict`

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
            #arch-eval:locational_stability=4

        """
        return {
            "session_id": self.session_id,
            "status": self.status,
            "host": self.host,
            "mcp_pdb": attrs.asdict(self.mcp_pdb),
            "sidecar": attrs.asdict(self.sidecar),
            "active_failure": self.active_failure,
        }


def allocate_local_port(host: str) -> int:
    """
    Find an available local TCP port without keeping a listener open.

    Returns:
        Available TCP port.

    Responsibility:
        Find an available local TCP port without keeping a listener open. It directly owns the observable contract,
        local decisions, and maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.plugin.debug_mcp.discovery.allocate_local_port` because it
        keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - socket.socket: collaborator call used by this boundary
        - sock.bind: collaborator call used by this boundary
        - int: collaborator call used by this boundary
        - sock.getsockname: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/debug_mcp/entrypoint.py: imports or references `allocate_local_port`

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
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind((host, 0))
        return int(sock.getsockname()[1])


def discovery_dir(config: ConfigWithRootpath) -> Path:
    """
    Return pytest cache discovery directory.

    Returns:
        Path to `.pytest_cache/mcp-pdb`.

    Responsibility:
        Return pytest cache discovery directory. It directly owns the observable contract, local decisions, and
        maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.plugin.debug_mcp.discovery.discovery_dir` because it keeps
        the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - Path: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/debug_mcp/xdist.py: imports or references `discovery_dir`

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
    return Path(config.rootpath) / ".pytest_cache" / "mcp-pdb"


def discovery_path(config: ConfigWithRootpath) -> Path:
    """
    Return session discovery path.

    Returns:
        Path to `session.json`.

    Responsibility:
        Return session discovery path. It directly owns the observable contract, local decisions, and maintenance
        boundary for this function. That boundary is intentionally stated in prose so maintainers can distinguish owned
        work from collaborators before editing.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.plugin.debug_mcp.discovery.discovery_path` because it
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
        - src/pytest_bdd/plugin/debug_mcp/entrypoint.py: imports or references `discovery_path`
        - src/pytest_bdd/plugin/debug_mcp/queue.py: imports or references `discovery_path`
        - src/pytest_bdd/plugin/debug_mcp/xdist.py: imports or references `discovery_path`

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
        #arch-eval:locational_stability=4

    """
    return discovery_dir(config) / "session.json"


def write_discovery_file(path: Path, discovery: SessionDiscovery) -> None:
    """
    Write discovery JSON atomically.

    Responsibility:
        Write discovery JSON atomically. It directly owns the observable contract, local decisions, and maintenance
        boundary for this function. That boundary is intentionally stated in prose so maintainers can distinguish owned
        work from collaborators before editing.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.plugin.debug_mcp.discovery.write_discovery_file` because
        it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - tmp.write: collaborator call used by this boundary
        - path.parent.mkdir: collaborator call used by this boundary
        - json.dumps: collaborator call used by this boundary
        - discovery.as_dict: collaborator call used by this boundary
        - NamedTemporaryFile: collaborator call used by this boundary
        - Path: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/debug_mcp/queue.py: imports or references `write_discovery_file`
        - src/pytest_bdd/plugin/debug_mcp/xdist.py: imports or references `write_discovery_file`

    State and side effects:
        mutates payload, tmp_path.

    Invariants:
        - `pytest_bdd.plugin.debug_mcp.discovery.write_discovery_file` keeps its documented import path, ownership
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
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(discovery.as_dict(), indent=2, sort_keys=True)
    with NamedTemporaryFile("w", encoding="utf-8", delete=False, dir=path.parent, prefix=f".{path.name}.") as tmp:
        tmp.write(payload)
        tmp.write("\n")
        tmp_path = Path(tmp.name)
    tmp_path.replace(path)


def format_terminal_line(discovery: SessionDiscovery, *, path: Path) -> str:
    """
    Format concise terminal discovery output.

    Returns:
        Human-readable endpoint summary.

    Responsibility:
        Format concise terminal discovery output. It directly owns the observable contract, local decisions, and
        maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.plugin.debug_mcp.discovery.format_terminal_line` because
        it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - None, leaf-level implementation boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/debug_mcp/entrypoint.py: imports or references `format_terminal_line`

    State and side effects:
        keeps no local persistent state beyond call-local values.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=2
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=3
        #arch-eval:locational_stability=3

    """
    return (
        "debug-mcp session "
        f"{discovery.session_id}: mcp-pdb={discovery.mcp_pdb.host}:{discovery.mcp_pdb.port} "
        f"sidecar={discovery.sidecar.host}:{discovery.sidecar.port} discovery={path}"
    )
