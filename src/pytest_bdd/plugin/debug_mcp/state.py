"""
Session state for debug MCP.

Responsibility:
    Session state for debug MCP. It directly owns the observable contract, local decisions, and maintenance boundary for
    this module. That boundary is intentionally stated in prose so maintainers can distinguish owned work from
    collaborators before editing.

Reason for existence:
    This entity is the information expert for `pytest_bdd.plugin.debug_mcp.state` because it keeps the nearest code,
    data shape, call signature, and failure knowledge together.

Delegates:
    - Endpoint: owns nested behavior below this boundary
    - DebugMcpState: owns nested behavior below this boundary

Cohesion:
    The implementation stays together because its imports, calls, state writes, and return contract describe one
    maintainable decision unit.

Separation:
    - module peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
      widening caller knowledge.

Main consumers:
    - src/pytest_bdd/plugin/debug_mcp/artifacts.py: imports or references `state`
    - src/pytest_bdd/plugin/debug_mcp/discovery.py: imports or references `state`
    - src/pytest_bdd/plugin/debug_mcp/entrypoint.py: imports or references `state`
    - src/pytest_bdd/plugin/debug_mcp/hook.py: imports or references `state`
    - src/pytest_bdd/plugin/debug_mcp/queue.py: imports or references `state`

State and side effects:
    mutates host, port, STASH_KEY, options, session_id; depends on __future__.annotations, datetime.UTC,
    datetime.datetime, typing.TYPE_CHECKING, typing.ClassVar.

Invariants:
    - `pytest_bdd.plugin.debug_mcp.state` keeps its documented import path, ownership boundary, and observable behavior
      stable for callers.

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

from datetime import UTC, datetime
from typing import TYPE_CHECKING, ClassVar
from uuid import uuid4

import attrs

from pytest_bdd.model.stash_access import StashBound

if TYPE_CHECKING:
    import subprocess

    from .options import DebugMcpOptions
    from .queue import FailureQueue


@attrs.define(frozen=True, slots=True)
class Endpoint:
    """
    Debug MCP endpoint.

    Responsibility:
        Debug MCP endpoint. It directly owns the observable contract, local decisions, and maintenance boundary for this
        class. That boundary is intentionally stated in prose so maintainers can distinguish owned work from
        collaborators before editing.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.plugin.debug_mcp.state.Endpoint` because it keeps the
        nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - attrs.define: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/debug_mcp/discovery.py: imports or references `Endpoint`
        - src/pytest_bdd/plugin/debug_mcp/mcp_pdb_adapter.py: imports or references `Endpoint`
        - src/pytest_bdd/plugin/debug_mcp/queue.py: imports or references `Endpoint`

    State and side effects:
        mutates host, port.

    Invariants:
        - `pytest_bdd.plugin.debug_mcp.state.Endpoint` keeps its documented import path, ownership boundary, and
          observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=3
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=2
        #arch-eval:locational_stability=4
    """

    host: str
    port: int


@attrs.define(slots=True)
class DebugMcpState(StashBound):
    """
    Config.stash-bound debug MCP session state.

    Responsibility:
        Config.stash-bound debug MCP session state. It directly owns the observable contract, local decisions, and
        maintenance boundary for this class.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.plugin.debug_mcp.state.DebugMcpState` because it keeps the
        nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - from_options: owns nested behavior below this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/debug_mcp/artifacts.py: imports or references `DebugMcpState`
        - src/pytest_bdd/plugin/debug_mcp/discovery.py: imports or references `DebugMcpState`
        - src/pytest_bdd/plugin/debug_mcp/entrypoint.py: imports or references `DebugMcpState`
        - src/pytest_bdd/plugin/debug_mcp/hook.py: imports or references `DebugMcpState`
        - src/pytest_bdd/plugin/debug_mcp/queue.py: imports or references `DebugMcpState`

    State and side effects:
        mutates STASH_KEY, options, session_id, created_at, mcp_pdb_endpoint.

    Invariants:
        - `pytest_bdd.plugin.debug_mcp.state.DebugMcpState` keeps its documented import path, ownership boundary, and
          observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=3
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=3
        #arch-eval:locational_stability=4
    """

    STASH_KEY: ClassVar[str] = "pytest_bdd.debug_mcp.state"

    options: DebugMcpOptions
    session_id: str = attrs.field(factory=lambda: uuid4().hex)
    created_at: str = attrs.field(factory=lambda: datetime.now(UTC).isoformat())
    mcp_pdb_endpoint: Endpoint | None = None
    sidecar_endpoint: Endpoint | None = None
    queue: FailureQueue | None = None
    mcp_server_process: subprocess.Popen[bytes] | None = None

    @classmethod
    def from_options(
        cls,
        options: DebugMcpOptions,
        *,
        mcp_port: int,
        sidecar_port: int,
        queue: FailureQueue | None = None,
    ) -> DebugMcpState:
        """
        Create initialized debug MCP state from resolved options and allocated ports.

        Returns:
            Initialized debug MCP state.

        Responsibility:
            Create initialized debug MCP state from resolved options and allocated ports. It directly owns the
            observable contract, local decisions, and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.plugin.debug_mcp.state.DebugMcpState.from_options`
            because it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - Endpoint: collaborator call used by this boundary
            - cls: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/debug_mcp/entrypoint.py: imports or references `from_options`

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
        return cls(
            options=options,
            mcp_pdb_endpoint=Endpoint(host=options.host, port=mcp_port),
            sidecar_endpoint=Endpoint(host=options.host, port=sidecar_port),
            queue=queue,
        )
