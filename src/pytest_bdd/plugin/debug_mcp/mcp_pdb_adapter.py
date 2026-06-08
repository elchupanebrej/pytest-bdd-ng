"""
Adapter boundary for mcp-pdb integration.

Responsibility:
    Adapter boundary for mcp-pdb integration. It directly owns the observable contract, local decisions, and maintenance
    boundary for this module.

Reason for existence:
    This entity is the information expert for `pytest_bdd.plugin.debug_mcp.mcp_pdb_adapter` because it keeps the nearest
    code, data shape, call signature, and failure knowledge together.

Delegates:
    - DebugAdapter: owns nested behavior below this boundary
    - McpPdbAdapter: owns nested behavior below this boundary

Cohesion:
    The implementation stays together because its imports, calls, state writes, and return contract describe one
    maintainable decision unit.

Separation:
    - module peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
      widening caller knowledge.

Main consumers:
    - None found by static import/name scan; verify dynamic use before refactor

State and side effects:
    mutates set_trace; depends on __future__.annotations, importlib.import_module, typing.TYPE_CHECKING,
    typing.Protocol, failure.QueuedFailure.

Invariants:
    - `pytest_bdd.plugin.debug_mcp.mcp_pdb_adapter` keeps its documented import path, ownership boundary, and observable
      behavior stable for callers.

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

from importlib import import_module
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from .failure import QueuedFailure
    from .state import Endpoint


class DebugAdapter(Protocol):
    """
    Boundary for entering and observing debugger state.

    Responsibility:
        Boundary for entering and observing debugger state. It directly owns the observable contract, local decisions,
        and maintenance boundary for this class.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.plugin.debug_mcp.mcp_pdb_adapter.DebugAdapter` because it
        keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - enter_failure: owns nested behavior below this boundary
        - continued: owns nested behavior below this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/debug_mcp/queue.py: imports or references `DebugAdapter`

    State and side effects:
        keeps no local persistent state beyond call-local values.

    Invariants:
        - `pytest_bdd.plugin.debug_mcp.mcp_pdb_adapter.DebugAdapter` keeps its documented import path, ownership
          boundary, and observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=3
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=3
    """

    def enter_failure(self, failure: QueuedFailure, *, endpoint: Endpoint) -> None:
        """
        Enter debugger for a queued failure.

        Responsibility:
            Enter debugger for a queued failure. It directly owns the observable contract, local decisions, and
            maintenance boundary for this method. That boundary is intentionally stated in prose so maintainers can
            distinguish owned work from collaborators before editing.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.debug_mcp.mcp_pdb_adapter.DebugAdapter.enter_failure` because it keeps the nearest code,
            data shape, call signature, and failure knowledge together.

        Delegates:
            - None, leaf-level implementation boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/debug_mcp/queue.py: imports or references `enter_failure`

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

    def continued(self, failure: QueuedFailure) -> bool:
        """
        Return whether raw PDB continuation released the failure.

        Returns:
            True when debugger continuation has resumed execution.

        Responsibility:
            Return whether raw PDB continuation released the failure. It directly owns the observable contract, local
            decisions, and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.debug_mcp.mcp_pdb_adapter.DebugAdapter.continued` because it keeps the nearest code, data
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
            - src/pytest_bdd/plugin/debug_mcp/queue.py: imports or references `continued`

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


class McpPdbAdapter:
    """
    Production adapter around mcp-pdb public entry points.

    Responsibility:
        Production adapter around mcp-pdb public entry points. It directly owns the observable contract, local
        decisions, and maintenance boundary for this class.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.plugin.debug_mcp.mcp_pdb_adapter.McpPdbAdapter` because it
        keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - enter_failure: owns nested behavior below this boundary
        - continued: owns nested behavior below this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/debug_mcp/entrypoint.py: imports or references `McpPdbAdapter`

    State and side effects:
        mutates set_trace.

    Invariants:
        - `pytest_bdd.plugin.debug_mcp.mcp_pdb_adapter.McpPdbAdapter` keeps its documented import path, ownership
          boundary, and observable behavior stable for callers.

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

    @staticmethod
    def enter_failure(failure: QueuedFailure, *, endpoint: Endpoint) -> None:
        """
        Enter mcp-pdb for a queued failure.

        Responsibility:
            Enter mcp-pdb for a queued failure. It directly owns the observable contract, local decisions, and
            maintenance boundary for this method. That boundary is intentionally stated in prose so maintainers can
            distinguish owned work from collaborators before editing.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.debug_mcp.mcp_pdb_adapter.McpPdbAdapter.enter_failure` because it keeps the nearest code,
            data shape, call signature, and failure knowledge together.

        Delegates:
            - set_trace: collaborator call used by this boundary
            - import_module: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/debug_mcp/queue.py: imports or references `enter_failure`

        State and side effects:
            mutates set_trace.

        Invariants:
            - `pytest_bdd.plugin.debug_mcp.mcp_pdb_adapter.McpPdbAdapter.enter_failure` keeps its documented import
              path, ownership boundary, and observable behavior stable for callers.

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
        del failure
        set_trace = import_module("mcp_pdb.rpdb").set_trace

        try:
            set_trace(host=endpoint.host, port=endpoint.port)
        except TypeError:
            set_trace()

    @staticmethod
    def continued(failure: QueuedFailure) -> bool:
        """
        Return whether raw PDB continuation released the failure.

        Returns:
            False until later adapter plans wire observable mcp-pdb state.

        Responsibility:
            Return whether raw PDB continuation released the failure. It directly owns the observable contract, local
            decisions, and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.debug_mcp.mcp_pdb_adapter.McpPdbAdapter.continued` because it keeps the nearest code,
            data shape, call signature, and failure knowledge together.

        Delegates:
            - None, leaf-level implementation boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/debug_mcp/queue.py: imports or references `continued`

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
        del failure
        return False
