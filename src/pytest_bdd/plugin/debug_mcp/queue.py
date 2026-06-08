"""
Failure queue and hold lifecycle for debug MCP.

Responsibility:
    Failure queue and hold lifecycle for debug MCP. It directly owns the observable contract, local decisions, and
    maintenance boundary for this module.

Reason for existence:
    This entity is the information expert for `pytest_bdd.plugin.debug_mcp.queue` because it keeps the nearest code,
    data shape, call signature, and failure knowledge together.

Delegates:
    - FailureQueue: owns nested behavior below this boundary
    - _require_endpoint: owns nested behavior below this boundary
    - _require_sidecar_endpoint: owns nested behavior below this boundary

Cohesion:
    The implementation stays together because its imports, calls, state writes, and return contract describe one
    maintainable decision unit.

Separation:
    - module peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
      widening caller knowledge.

Main consumers:
    - src/pytest_bdd/plugin/debug_mcp/hook.py: imports or references `queue`
    - src/pytest_bdd/plugin/debug_mcp/sidecar.py: imports or references `queue`
    - src/pytest_bdd/plugin/debug_mcp/state.py: imports or references `queue`
    - src/pytest_bdd/plugin/gherkin_message_reporter/transport_runtime.py: imports or references `queue`

State and side effects:
    mutates active, self.connected, self.last_heartbeat_at, msg, self.active_failure; depends on __future__.annotations,
    time, collections.abc.Callable, typing.TYPE_CHECKING, attrs.

Invariants:
    - `pytest_bdd.plugin.debug_mcp.queue` keeps its documented import path, ownership boundary, and observable behavior
      stable for callers.

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
    #arch-eval:locational_stability=4
"""

from __future__ import annotations

import time
from collections.abc import Callable
from typing import TYPE_CHECKING

import attrs

from .discovery import SessionDiscovery, write_discovery_file
from .failure import QueuedFailure, ReleaseReason, ReleaseRecord

if TYPE_CHECKING:
    from pathlib import Path

    from .mcp_pdb_adapter import DebugAdapter
    from .state import DebugMcpState, Endpoint

Clock = Callable[[], float]
DiscoveryWriter = Callable[["DebugMcpState", SessionDiscovery], None]


@attrs.define(slots=True)
class FailureQueue:
    """
    Single-active-failure debug MCP queue.

    Responsibility:
        Single-active-failure debug MCP queue. It directly owns the observable contract, local decisions, and
        maintenance boundary for this class. That boundary is intentionally stated in prose so maintainers can
        distinguish owned work from collaborators before editing.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.plugin.debug_mcp.queue.FailureQueue` because it keeps the
        nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - hold_failure: owns nested behavior below this boundary
        - write_holding_discovery: owns nested behavior below this boundary
        - heartbeat: owns nested behavior below this boundary
        - release: owns nested behavior below this boundary
        - mark_artifact_written: owns nested behavior below this boundary
        - expire_without_client: owns nested behavior below this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/debug_mcp/entrypoint.py: imports or references `FailureQueue`
        - src/pytest_bdd/plugin/debug_mcp/sidecar.py: imports or references `FailureQueue`
        - src/pytest_bdd/plugin/debug_mcp/state.py: imports or references `FailureQueue`

    State and side effects:
        mutates active, self.connected, self.last_heartbeat_at, self.active_failure, self.release_record.

    Invariants:
        - `pytest_bdd.plugin.debug_mcp.queue.FailureQueue` keeps its documented import path, ownership boundary, and
          observable behavior stable for callers.

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
        #arch-eval:locational_stability=4
    """

    discovery_path: Path
    adapter: DebugAdapter
    clock: Clock = time.monotonic
    discovery_writer: DiscoveryWriter | None = None
    active_failure: QueuedFailure | None = None
    release_record: ReleaseRecord | None = None
    connected: bool = False
    last_heartbeat_at: float | None = None
    artifact_written_sequences: set[int] = attrs.field(factory=set)
    _sequence: int = 0

    def hold_failure(self, failure: QueuedFailure, *, state: DebugMcpState | None = None) -> QueuedFailure:
        """
        Make a failure active and enter the adapter seam.

        Returns:
            Active queued failure.

        Responsibility:
            Make a failure active and enter the adapter seam. It directly owns the observable contract, local decisions,
            and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.plugin.debug_mcp.queue.FailureQueue.hold_failure`
            because it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - failure.with_sequence: collaborator call used by this boundary
            - self.write_holding_discovery: collaborator call used by this boundary
            - _require_sidecar_endpoint: collaborator call used by this boundary
            - self.adapter.enter_failure: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/debug_mcp/hook.py: imports or references `hold_failure`

        State and side effects:
            mutates self._sequence, active, self.active_failure, self.release_record, self.connected.

        Invariants:
            - `pytest_bdd.plugin.debug_mcp.queue.FailureQueue.hold_failure` keeps its documented import path, ownership
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
        self._sequence += 1
        active = failure.with_sequence(self._sequence)
        self.active_failure = active
        self.release_record = None
        self.connected = False
        self.last_heartbeat_at = None
        if state is not None:
            self.write_holding_discovery(state)
            # Use sidecar endpoint for raw TCP server (different from MCP server)
            endpoint = _require_sidecar_endpoint(state)
            self.adapter.enter_failure(active, endpoint=endpoint)
        return active

    def write_holding_discovery(self, state: DebugMcpState) -> None:
        """
        Write discovery with active failure metadata.

        Responsibility:
            Write discovery with active failure metadata. It directly owns the observable contract, local decisions, and
            maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.debug_mcp.queue.FailureQueue.write_holding_discovery` because it keeps the nearest code,
            data shape, call signature, and failure knowledge together.

        Delegates:
            - self.require_active: collaborator call used by this boundary
            - SessionDiscovery.holding: collaborator call used by this boundary
            - active.summary.as_dict: collaborator call used by this boundary
            - self.discovery_writer: collaborator call used by this boundary
            - write_discovery_file: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - None found by static import/name scan; verify dynamic use before refactor

        State and side effects:
            mutates active, discovery.

        Invariants:
            - `pytest_bdd.plugin.debug_mcp.queue.FailureQueue.write_holding_discovery` keeps its documented import path,
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
        active = self.require_active()
        discovery = SessionDiscovery.holding(state, active.summary.as_dict())
        if self.discovery_writer is not None:
            self.discovery_writer(state, discovery)
            return
        write_discovery_file(self.discovery_path, discovery)

    def heartbeat(self) -> None:
        """
        Refresh connected-client lease.

        Responsibility:
            Refresh connected-client lease. It directly owns the observable contract, local decisions, and maintenance
            boundary for this method. That boundary is intentionally stated in prose so maintainers can distinguish
            owned work from collaborators before editing.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.plugin.debug_mcp.queue.FailureQueue.heartbeat` because
            it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - self.clock: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/debug_mcp/sidecar.py: imports or references `heartbeat`

        State and side effects:
            mutates self.connected, self.last_heartbeat_at.

        Invariants:
            - `pytest_bdd.plugin.debug_mcp.queue.FailureQueue.heartbeat` keeps its documented import path, ownership
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
        self.connected = True
        self.last_heartbeat_at = self.clock()

    def release(self, *, reason: ReleaseReason = "explicit", artifact_written: bool = False) -> ReleaseRecord:
        """
        Release active failure.

        Returns:
            Release metadata.

        Responsibility:
            Release active failure. It directly owns the observable contract, local decisions, and maintenance boundary
            for this method. That boundary is intentionally stated in prose so maintainers can distinguish owned work
            from collaborators before editing.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.plugin.debug_mcp.queue.FailureQueue.release` because
            it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - self.require_active: collaborator call used by this boundary
            - ReleaseRecord: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/debug_mcp/sidecar.py: imports or references `release`

        State and side effects:
            mutates active, artifact_written, record, self.release_record, self.active_failure.

        Invariants:
            - `pytest_bdd.plugin.debug_mcp.queue.FailureQueue.release` keeps its documented import path, ownership
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
        active = self.require_active()
        artifact_written = artifact_written or active.summary.sequence_id in self.artifact_written_sequences
        record = ReleaseRecord(
            sequence_id=active.summary.sequence_id,
            reason=reason,
            artifact_status="written" if artifact_written else "missing",
        )
        self.release_record = record
        self.active_failure = None
        self.connected = False
        self.last_heartbeat_at = None
        return record

    def mark_artifact_written(self, sequence_id: int) -> None:
        """
        Record that an investigation artifact exists for a failure.

        Responsibility:
            Record that an investigation artifact exists for a failure. It directly owns the observable contract, local
            decisions, and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.debug_mcp.queue.FailureQueue.mark_artifact_written` because it keeps the nearest code,
            data shape, call signature, and failure knowledge together.

        Delegates:
            - self.artifact_written_sequences.add: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/debug_mcp/sidecar.py: imports or references `mark_artifact_written`

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
        self.artifact_written_sequences.add(sequence_id)

    def expire_without_client(self, *, timeout_seconds: float) -> ReleaseRecord | None:
        """
        Release active failure after no-client timeout.

        Returns:
            Release metadata when expired, else None.

        Responsibility:
            Release active failure after no-client timeout. It directly owns the observable contract, local decisions,
            and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.debug_mcp.queue.FailureQueue.expire_without_client` because it keeps the nearest code,
            data shape, call signature, and failure knowledge together.

        Delegates:
            - self.clock: collaborator call used by this boundary
            - self.release: collaborator call used by this boundary

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
            - `pytest_bdd.plugin.debug_mcp.queue.FailureQueue.expire_without_client` keeps its documented import path,
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
        active = self.active_failure
        if active is None or self.connected:
            return None
        if self.clock() >= timeout_seconds:
            return self.release(reason="timeout")
        return None

    def expire_missed_heartbeat(self, *, lease_seconds: float) -> ReleaseRecord | None:
        """
        Release active failure after missed heartbeat lease.

        Returns:
            Release metadata when expired, else None.

        Responsibility:
            Release active failure after missed heartbeat lease. It directly owns the observable contract, local
            decisions, and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.debug_mcp.queue.FailureQueue.expire_missed_heartbeat` because it keeps the nearest code,
            data shape, call signature, and failure knowledge together.

        Delegates:
            - self.clock: collaborator call used by this boundary
            - self.release: collaborator call used by this boundary

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
        if self.active_failure is None or not self.connected or self.last_heartbeat_at is None:
            return None
        if self.clock() - self.last_heartbeat_at >= lease_seconds:
            return self.release(reason="lease_expired")
        return None

    def release_if_pdb_continued(self) -> ReleaseRecord | None:
        """
        Release active failure when adapter observes raw PDB continuation.

        Returns:
            Release metadata when continued, else None.

        Responsibility:
            Release active failure when adapter observes raw PDB continuation. It directly owns the observable contract,
            local decisions, and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.debug_mcp.queue.FailureQueue.release_if_pdb_continued` because it keeps the nearest code,
            data shape, call signature, and failure knowledge together.

        Delegates:
            - self.adapter.continued: collaborator call used by this boundary
            - self.release: collaborator call used by this boundary

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
            - `pytest_bdd.plugin.debug_mcp.queue.FailureQueue.release_if_pdb_continued` keeps its documented import
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
        active = self.active_failure
        if active is not None and self.adapter.continued(active):
            return self.release(reason="pdb_continue")
        return None

    def require_active(self) -> QueuedFailure:
        """
        Return active failure or raise.

        Returns:
            Active queued failure.

        Raises:
            RuntimeError: If no active failure exists.

        Responsibility:
            Return active failure or raise. It directly owns the observable contract, local decisions, and maintenance
            boundary for this method. That boundary is intentionally stated in prose so maintainers can distinguish
            owned work from collaborators before editing.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.plugin.debug_mcp.queue.FailureQueue.require_active`
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
            - src/pytest_bdd/plugin/debug_mcp/sidecar.py: imports or references `require_active`

        State and side effects:
            mutates msg.

        Invariants:
            - `pytest_bdd.plugin.debug_mcp.queue.FailureQueue.require_active` keeps its documented import path,
              ownership boundary, and observable behavior stable for callers.

        Failure semantics:
            Raises or re-raises RuntimeError; callers must treat these as boundary failures.

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
        if self.active_failure is None:
            msg = "No active debug MCP failure."
            raise RuntimeError(msg)
        return self.active_failure


def _require_endpoint(state: DebugMcpState) -> Endpoint:
    """
    Responsibility:
        Responsibility: Responsibility: `pytest_bdd.plugin.debug_mcp.queue._require_endpoint` owns documented function
        behavior. It directly owns the observable contract, local decisions, and maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.plugin.debug_mcp.queue._require_endpoint` because it keeps
        the nearest code, data shape, call signature, and failure knowledge together.

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
        - `pytest_bdd.plugin.debug_mcp.queue._require_endpoint` keeps its documented import path, ownership boundary,
          and observable behavior stable for callers.

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
    if state.mcp_pdb_endpoint is None:
        msg = "Debug MCP mcp-pdb endpoint is unavailable."
        raise RuntimeError(msg)
    return state.mcp_pdb_endpoint


def _require_sidecar_endpoint(state: DebugMcpState) -> Endpoint:
    """
    Responsibility:
        Responsibility: Responsibility: `pytest_bdd.plugin.debug_mcp.queue._require_sidecar_endpoint` owns documented
        function behavior. It directly owns the observable contract, local decisions, and maintenance boundary for this
        function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.plugin.debug_mcp.queue._require_sidecar_endpoint` because
        it keeps the nearest code, data shape, call signature, and failure knowledge together.

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
        - `pytest_bdd.plugin.debug_mcp.queue._require_sidecar_endpoint` keeps its documented import path, ownership
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
    if state.sidecar_endpoint is None:
        msg = "Debug MCP sidecar endpoint is unavailable."
        raise RuntimeError(msg)
    return state.sidecar_endpoint
