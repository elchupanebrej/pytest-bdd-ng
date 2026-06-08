"""
Failure metadata models for debug MCP.

Responsibility:
    Failure metadata models for debug MCP. It directly owns the observable contract, local decisions, and maintenance
    boundary for this module. That boundary is intentionally stated in prose so maintainers can distinguish owned work
    from collaborators before editing.

Reason for existence:
    This entity is the information expert for `pytest_bdd.plugin.debug_mcp.failure` because it keeps the nearest code,
    data shape, call signature, and failure knowledge together.

Delegates:
    - FailureSummary: owns nested behavior below this boundary
    - QueuedFailure: owns nested behavior below this boundary
    - ReleaseRecord: owns nested behavior below this boundary
    - _exception_type: owns nested behavior below this boundary
    - _message: owns nested behavior below this boundary

Cohesion:
    The implementation stays together because its imports, calls, state writes, and return contract describe one
    maintainable decision unit.

Separation:
    - module peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
      widening caller knowledge.

Main consumers:
    - src/pytest_bdd/plugin/debug_mcp/bdd_adapter.py: imports or references `failure`
    - src/pytest_bdd/plugin/debug_mcp/hook.py: imports or references `failure`
    - src/pytest_bdd/plugin/debug_mcp/mcp_pdb_adapter.py: imports or references `failure`
    - src/pytest_bdd/plugin/debug_mcp/queue.py: imports or references `failure`

State and side effects:
    mutates longrepr, sequence_id, artifact_status, PytestPhase, ArtifactStatus; depends on __future__.annotations,
    typing.TYPE_CHECKING, typing.Any, typing.Literal, attrs.

Invariants:
    - `pytest_bdd.plugin.debug_mcp.failure` keeps its documented import path, ownership boundary, and observable
      behavior stable for callers.

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

from typing import TYPE_CHECKING, Any, Literal

import attrs

if TYPE_CHECKING:
    from pytest_bdd.compatibility.pytest import TestReport


PytestPhase = Literal["setup", "call", "teardown"]
ArtifactStatus = Literal["missing", "written"]
ReleaseReason = Literal["explicit", "timeout", "lease_expired", "pdb_continue"]


@attrs.define(frozen=True, slots=True)
class FailureSummary:
    """
    Serializable failure metadata.

    Responsibility:
        Serializable failure metadata. It directly owns the observable contract, local decisions, and maintenance
        boundary for this class. That boundary is intentionally stated in prose so maintainers can distinguish owned
        work from collaborators before editing.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.plugin.debug_mcp.failure.FailureSummary` because it keeps
        the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - as_dict: owns nested behavior below this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - None found by static import/name scan; verify dynamic use before refactor

    State and side effects:
        mutates sequence_id, nodeid, pytest_phase, exception_type, message.

    Invariants:
        - `pytest_bdd.plugin.debug_mcp.failure.FailureSummary` keeps its documented import path, ownership boundary, and
          observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=3
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=2
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=3
        #arch-eval:locational_stability=2
    """

    sequence_id: int
    nodeid: str
    pytest_phase: PytestPhase
    exception_type: str
    message: str
    artifact_status: ArtifactStatus = "missing"
    bdd: dict[str, Any] | None = None

    def as_dict(self) -> dict[str, Any]:
        """
        Return JSON-compatible failure metadata.

        Returns:
            Failure dictionary for discovery JSON.

        Responsibility:
            Return JSON-compatible failure metadata. It directly owns the observable contract, local decisions, and
            maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.plugin.debug_mcp.failure.FailureSummary.as_dict`
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
        return attrs.asdict(self)


@attrs.define(frozen=True, slots=True)
class QueuedFailure:
    """
    Queued pytest failure.

    Responsibility:
        Queued pytest failure. It directly owns the observable contract, local decisions, and maintenance boundary for
        this class. That boundary is intentionally stated in prose so maintainers can distinguish owned work from
        collaborators before editing.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.plugin.debug_mcp.failure.QueuedFailure` because it keeps
        the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - from_report: owns nested behavior below this boundary
        - with_sequence: owns nested behavior below this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/debug_mcp/bdd_adapter.py: imports or references `QueuedFailure`
        - src/pytest_bdd/plugin/debug_mcp/hook.py: imports or references `QueuedFailure`
        - src/pytest_bdd/plugin/debug_mcp/mcp_pdb_adapter.py: imports or references `QueuedFailure`
        - src/pytest_bdd/plugin/debug_mcp/queue.py: imports or references `QueuedFailure`

    State and side effects:
        mutates summary, longrepr.

    Invariants:
        - `pytest_bdd.plugin.debug_mcp.failure.QueuedFailure` keeps its documented import path, ownership boundary, and
          observable behavior stable for callers.

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

    summary: FailureSummary
    longrepr: str

    @classmethod
    def from_report(cls, report: TestReport, *, sequence_id: int = 0) -> QueuedFailure:
        """
        Create queued failure from pytest report.

        Returns:
            Queued failure with report metadata.

        Responsibility:
            Create queued failure from pytest report. It directly owns the observable contract, local decisions, and
            maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.plugin.debug_mcp.failure.QueuedFailure.from_report`
            because it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - cls: collaborator call used by this boundary
            - FailureSummary: collaborator call used by this boundary
            - _exception_type: collaborator call used by this boundary
            - _message: collaborator call used by this boundary
            - str: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/debug_mcp/hook.py: imports or references `from_report`

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
            summary=FailureSummary(
                sequence_id=sequence_id,
                nodeid=report.nodeid,
                pytest_phase=report.when,
                exception_type=_exception_type(report),
                message=_message(report),
            ),
            longrepr=str(report.longrepr),
        )

    def with_sequence(self, sequence_id: int) -> QueuedFailure:
        """
        Return copy with deterministic sequence id.

        Returns:
            Queued failure with updated sequence id.

        Responsibility:
            Return copy with deterministic sequence id. It directly owns the observable contract, local decisions, and
            maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.plugin.debug_mcp.failure.QueuedFailure.with_sequence`
            because it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - attrs.evolve: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/debug_mcp/queue.py: imports or references `with_sequence`

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
        return attrs.evolve(self, summary=attrs.evolve(self.summary, sequence_id=sequence_id))


@attrs.define(frozen=True, slots=True)
class ReleaseRecord:
    """
    Record of a debug MCP failure release.

    Responsibility:
        Record of a debug MCP failure release. It directly owns the observable contract, local decisions, and
        maintenance boundary for this class. That boundary is intentionally stated in prose so maintainers can
        distinguish owned work from collaborators before editing.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.plugin.debug_mcp.failure.ReleaseRecord` because it keeps
        the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - as_dict: owns nested behavior below this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/debug_mcp/queue.py: imports or references `ReleaseRecord`

    State and side effects:
        mutates sequence_id, reason, artifact_status.

    Invariants:
        - `pytest_bdd.plugin.debug_mcp.failure.ReleaseRecord` keeps its documented import path, ownership boundary, and
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
        #arch-eval:locational_stability=3
    """

    sequence_id: int
    reason: ReleaseReason
    artifact_status: ArtifactStatus

    def as_dict(self) -> dict[str, object]:
        """
        Return JSON-compatible release metadata.

        Returns:
            Release dictionary for tests and future sidecar APIs.

        Responsibility:
            Return JSON-compatible release metadata. It directly owns the observable contract, local decisions, and
            maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.plugin.debug_mcp.failure.ReleaseRecord.as_dict`
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
        return attrs.asdict(self)


def _exception_type(report: TestReport) -> str:
    """
    Responsibility:
        Responsibility: Responsibility: `pytest_bdd.plugin.debug_mcp.failure._exception_type` owns documented function
        behavior. It directly owns the observable contract, local decisions, and maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.plugin.debug_mcp.failure._exception_type` because it keeps
        the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - strip: collaborator call used by this boundary
        - str: collaborator call used by this boundary
        - longrepr.split: collaborator call used by this boundary
        - tail.split: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - None found by static import/name scan; verify dynamic use before refactor

    State and side effects:
        mutates longrepr, tail.

    Invariants:
        - `pytest_bdd.plugin.debug_mcp.failure._exception_type` keeps its documented import path, ownership boundary,
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
    longrepr = str(report.longrepr)
    if "E   " in longrepr:
        tail = longrepr.split("E   ", 1)[1].strip()
        return tail.split(":", 1)[0].strip() or "Exception"
    return "Exception"


def _message(report: TestReport) -> str:
    """
    Responsibility:
        Responsibility: Responsibility: `pytest_bdd.plugin.debug_mcp.failure._message` owns documented function
        behavior. It directly owns the observable contract, local decisions, and maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.plugin.debug_mcp.failure._message` because it keeps the
        nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - longrepr.splitlines: collaborator call used by this boundary
        - str: collaborator call used by this boundary
        - strip.splitlines: collaborator call used by this boundary
        - strip: collaborator call used by this boundary
        - longrepr.split: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - None found by static import/name scan; verify dynamic use before refactor

    State and side effects:
        mutates longrepr.

    Invariants:
        - `pytest_bdd.plugin.debug_mcp.failure._message` keeps its documented import path, ownership boundary, and
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
    longrepr = str(report.longrepr)
    if "E   " in longrepr:
        return longrepr.split("E   ", 1)[1].strip().splitlines()[0]
    return longrepr.splitlines()[-1] if longrepr.splitlines() else ""
