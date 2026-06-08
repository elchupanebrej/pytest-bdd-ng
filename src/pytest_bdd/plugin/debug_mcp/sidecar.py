"""
In-process sidecar helper surface for debug MCP.

Responsibility:
    In-process sidecar helper surface for debug MCP. It directly owns the observable contract, local decisions, and
    maintenance boundary for this module.

Reason for existence:
    This entity is the information expert for `pytest_bdd.plugin.debug_mcp.sidecar` because it keeps the nearest code,
    data shape, call signature, and failure knowledge together.

Delegates:
    - DebugMcpSidecar: owns nested behavior below this boundary
    - build_sidecar: owns nested behavior below this boundary

Cohesion:
    The implementation stays together because its imports, calls, state writes, and return contract describe one
    maintainable decision unit.

Separation:
    - module peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
      widening caller knowledge.

Main consumers:
    - src/pytest_bdd/plugin/debug_mcp/discovery.py: imports or references `sidecar`

State and side effects:
    mutates queue, active, msg, state, artifact_sink; depends on __future__.annotations, pathlib.Path,
    typing.TYPE_CHECKING, typing.Any, attrs.

Invariants:
    - `pytest_bdd.plugin.debug_mcp.sidecar` keeps its documented import path, ownership boundary, and observable
      behavior stable for callers.

Failure semantics:
    Raises or re-raises RuntimeError; callers must treat these as boundary failures.

Architecture score:
    #arch-eval:reason_for_existence=4
    #arch-eval:owned_responsibility=4
    #arch-eval:delegation_boundary=4
    #arch-eval:cohesion=3
    #arch-eval:separation=3
    #arch-eval:consumer_clarity=4
    #arch-eval:state_invariants=4
    #arch-eval:entity_fullness=4
    #arch-eval:locational_stability=3
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

import attrs
from pydantic import ValidationError

from .artifacts import ArtifactSink, artifact_root_for_state, emit_artifact_created, validation_error_payload

if TYPE_CHECKING:
    from pytest_bdd.compatibility.pytest import PytestPluginManager

    from .queue import FailureQueue
    from .state import DebugMcpState


@attrs.define(slots=True)
class DebugMcpSidecar:
    """
    Testable sidecar handler layer for debug MCP helpers.

    Responsibility:
        Testable sidecar handler layer for debug MCP helpers. It directly owns the observable contract, local decisions,
        and maintenance boundary for this class.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.plugin.debug_mcp.sidecar.DebugMcpSidecar` because it keeps
        the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - __attrs_post_init__: owns nested behavior below this boundary
        - get_active_failure: owns nested behavior below this boundary
        - heartbeat: owns nested behavior below this boundary
        - release: owns nested behavior below this boundary
        - write_investigation_artifact: owns nested behavior below this boundary
        - get_bdd_context: owns nested behavior below this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - None found by static import/name scan; verify dynamic use before refactor

    State and side effects:
        mutates queue, active, msg, state, artifact_sink.

    Invariants:
        - `pytest_bdd.plugin.debug_mcp.sidecar.DebugMcpSidecar` keeps its documented import path, ownership boundary,
          and observable behavior stable for callers.

    Failure semantics:
        Raises or re-raises RuntimeError; callers must treat these as boundary failures.

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

    state: DebugMcpState
    artifact_sink: ArtifactSink | None = None
    pluginmanager: PytestPluginManager | None = None

    def __attrs_post_init__(self) -> None:
        """
        Initialize default artifact sink.

        Responsibility:
            Initialize default artifact sink. It directly owns the observable contract, local decisions, and maintenance
            boundary for this method. That boundary is intentionally stated in prose so maintainers can distinguish
            owned work from collaborators before editing.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.debug_mcp.sidecar.DebugMcpSidecar.__attrs_post_init__` because it keeps the nearest code,
            data shape, call signature, and failure knowledge together.

        Delegates:
            - ArtifactSink: collaborator call used by this boundary
            - Path: collaborator call used by this boundary
            - artifact_root_for_state: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - None found by static import/name scan; verify dynamic use before refactor

        State and side effects:
            mutates self.artifact_sink.

        Invariants:
            - `pytest_bdd.plugin.debug_mcp.sidecar.DebugMcpSidecar.__attrs_post_init__` keeps its documented import
              path, ownership boundary, and observable behavior stable for callers.

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
        if self.artifact_sink is None:
            self.artifact_sink = ArtifactSink(Path(artifact_root_for_state(self.state)))

    def get_active_failure(self) -> dict[str, Any] | None:
        """
        Return active failure metadata.

        Returns:
            Active failure dictionary, or None.

        Responsibility:
            Return active failure metadata. It directly owns the observable contract, local decisions, and maintenance
            boundary for this method. That boundary is intentionally stated in prose so maintainers can distinguish
            owned work from collaborators before editing.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.debug_mcp.sidecar.DebugMcpSidecar.get_active_failure` because it keeps the nearest code,
            data shape, call signature, and failure knowledge together.

        Delegates:
            - self._queue: collaborator call used by this boundary
            - queue.active_failure.summary.as_dict: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - None found by static import/name scan; verify dynamic use before refactor

        State and side effects:
            mutates queue.

        Invariants:
            - `pytest_bdd.plugin.debug_mcp.sidecar.DebugMcpSidecar.get_active_failure` keeps its documented import path,
              ownership boundary, and observable behavior stable for callers.

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
        queue = self._queue()
        if queue.active_failure is None:
            return None
        return queue.active_failure.summary.as_dict()

    def heartbeat(self) -> dict[str, object]:
        """
        Refresh queue heartbeat.

        Returns:
            Sidecar result payload.

        Responsibility:
            Refresh queue heartbeat. It directly owns the observable contract, local decisions, and maintenance boundary
            for this method. That boundary is intentionally stated in prose so maintainers can distinguish owned work
            from collaborators before editing.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.plugin.debug_mcp.sidecar.DebugMcpSidecar.heartbeat`
            because it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - self._queue.heartbeat: collaborator call used by this boundary
            - self._queue: collaborator call used by this boundary

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
        self._queue().heartbeat()
        return {"ok": True, "connected": True}

    def release(self, *, artifact_written: bool = False) -> dict[str, object]:
        """
        Release active failure.

        Returns:
            Release metadata payload.

        Responsibility:
            Release active failure. It directly owns the observable contract, local decisions, and maintenance boundary
            for this method. That boundary is intentionally stated in prose so maintainers can distinguish owned work
            from collaborators before editing.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.plugin.debug_mcp.sidecar.DebugMcpSidecar.release`
            because it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - self._queue.release: collaborator call used by this boundary
            - self._queue: collaborator call used by this boundary
            - record.as_dict: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/debug_mcp/queue.py: imports or references `release`

        State and side effects:
            mutates record.

        Invariants:
            - `pytest_bdd.plugin.debug_mcp.sidecar.DebugMcpSidecar.release` keeps its documented import path, ownership
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
        record = self._queue().release(artifact_written=artifact_written)
        return {"ok": True, "release": record.as_dict()}

    def write_investigation_artifact(self, payload: object) -> dict[str, object]:
        """
        Validate and write paired JSON/Markdown investigation artifact.

        Returns:
            Write result or validation error payload.

        Responsibility:
            Validate and write paired JSON/Markdown investigation artifact. It directly owns the observable contract,
            local decisions, and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.debug_mcp.sidecar.DebugMcpSidecar.write_investigation_artifact` because it keeps the
            nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - self._queue: collaborator call used by this boundary
            - queue.require_active: collaborator call used by this boundary
            - self._artifact_sink.write: collaborator call used by this boundary
            - self._artifact_sink: collaborator call used by this boundary
            - validation_error_payload: collaborator call used by this boundary
            - queue.mark_artifact_written: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - None found by static import/name scan; verify dynamic use before refactor

        State and side effects:
            mutates queue, active, result.

        Invariants:
            - `pytest_bdd.plugin.debug_mcp.sidecar.DebugMcpSidecar.write_investigation_artifact` keeps its documented
              import path, ownership boundary, and observable behavior stable for callers.

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
        queue = self._queue()
        active = queue.require_active()
        try:
            result = self._artifact_sink().write(
                sequence_id=active.summary.sequence_id,
                nodeid=active.summary.nodeid,
                payload=payload,
            )
        except ValidationError as error:
            return validation_error_payload(error)
        queue.mark_artifact_written(active.summary.sequence_id)
        if self.pluginmanager is not None:
            emit_artifact_created(self.pluginmanager, artifact=payload, result=result)
        return {"ok": True, "artifact": result.as_dict()}

    def get_bdd_context(self) -> dict[str, Any] | None:
        """
        Return BDD metadata for active failure.

        Returns:
            Empty or null BDD metadata until BDD adapter fills it.

        Responsibility:
            Return BDD metadata for active failure. It directly owns the observable contract, local decisions, and
            maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.debug_mcp.sidecar.DebugMcpSidecar.get_bdd_context` because it keeps the nearest code,
            data shape, call signature, and failure knowledge together.

        Delegates:
            - self._queue: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - None found by static import/name scan; verify dynamic use before refactor

        State and side effects:
            mutates active.

        Invariants:
            - `pytest_bdd.plugin.debug_mcp.sidecar.DebugMcpSidecar.get_bdd_context` keeps its documented import path,
              ownership boundary, and observable behavior stable for callers.

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
        active = self._queue().active_failure
        if active is None:
            return None
        return active.summary.bdd

    def _queue(self) -> FailureQueue:
        """
        Responsibility:
            Responsibility: Responsibility: `pytest_bdd.plugin.debug_mcp.sidecar.DebugMcpSidecar._queue` owns documented
            method behavior. It directly owns the observable contract, local decisions, and maintenance boundary for
            this method.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.plugin.debug_mcp.sidecar.DebugMcpSidecar._queue`
            because it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - RuntimeError: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - None found by static import/name scan; verify dynamic use before refactor

        State and side effects:
            mutates msg.

        Invariants:
            - `pytest_bdd.plugin.debug_mcp.sidecar.DebugMcpSidecar._queue` keeps its documented import path, ownership
              boundary, and observable behavior stable for callers.

        Failure semantics:
            Raises or re-raises RuntimeError; callers must treat these as boundary failures.

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
        if self.state.queue is None:
            msg = "Debug MCP queue is unavailable."
            raise RuntimeError(msg)
        return self.state.queue

    def _artifact_sink(self) -> ArtifactSink:
        """
        Responsibility:
            Responsibility: Responsibility: `pytest_bdd.plugin.debug_mcp.sidecar.DebugMcpSidecar._artifact_sink` owns
            documented method behavior. It directly owns the observable contract, local decisions, and maintenance
            boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.debug_mcp.sidecar.DebugMcpSidecar._artifact_sink` because it keeps the nearest code, data
            shape, call signature, and failure knowledge together.

        Delegates:
            - RuntimeError: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - None found by static import/name scan; verify dynamic use before refactor

        State and side effects:
            mutates msg.

        Invariants:
            - `pytest_bdd.plugin.debug_mcp.sidecar.DebugMcpSidecar._artifact_sink` keeps its documented import path,
              ownership boundary, and observable behavior stable for callers.

        Failure semantics:
            Raises or re-raises RuntimeError; callers must treat these as boundary failures.

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
        if self.artifact_sink is None:
            msg = "Debug MCP artifact sink is unavailable."
            raise RuntimeError(msg)
        return self.artifact_sink


def build_sidecar(state: DebugMcpState) -> DebugMcpSidecar:
    """
    Build sidecar helper layer for state.

    Returns:
        Sidecar helper instance.

    Responsibility:
        Build sidecar helper layer for state. It directly owns the observable contract, local decisions, and maintenance
        boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.plugin.debug_mcp.sidecar.build_sidecar` because it keeps
        the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - DebugMcpSidecar: collaborator call used by this boundary

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
    return DebugMcpSidecar(state=state)
