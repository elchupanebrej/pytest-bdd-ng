"""
Hook specifications for debug MCP artifacts.

Responsibility:
    Hook specifications for debug MCP artifacts. It directly owns the observable contract, local decisions, and
    maintenance boundary for this module.

Reason for existence:
    This entity is the information expert for `pytest_bdd.plugin.debug_mcp.hookspec` because it keeps the nearest code,
    data shape, call signature, and failure knowledge together.

Delegates:
    - DebugMcpHookSpec: owns nested behavior below this boundary

Cohesion:
    The implementation stays together because its imports, calls, state writes, and return contract describe one
    maintainable decision unit.

Separation:
    - module peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
      widening caller knowledge.

Main consumers:
    - src/pytest_bdd/plugin/gherkin_message_reporter/hook.py: imports or references `hookspec`
    - src/pytest_bdd/plugin/pickle_runner/hook.py: imports or references `hookspec`
    - src/pytest_bdd/plugin/scenario_test_collector/hook.py: imports or references `hookspec`

State and side effects:
    depends on __future__.annotations, typing.TYPE_CHECKING, typing.Literal, pytest, pathlib.Path.

Invariants:
    - `pytest_bdd.plugin.debug_mcp.hookspec` keeps its documented import path, ownership boundary, and observable
      behavior stable for callers.

Architecture score:
    #arch-eval:reason_for_existence=4
    #arch-eval:owned_responsibility=4
    #arch-eval:delegation_boundary=4
    #arch-eval:cohesion=3
    #arch-eval:separation=3
    #arch-eval:consumer_clarity=4
    #arch-eval:state_invariants=3
    #arch-eval:entity_fullness=3
    #arch-eval:locational_stability=4
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

import pytest

if TYPE_CHECKING:
    from pathlib import Path


class DebugMcpHookSpec:
    """
    Debug MCP hook specifications.

    Responsibility:
        Debug MCP hook specifications. It directly owns the observable contract, local decisions, and maintenance
        boundary for this class. That boundary is intentionally stated in prose so maintainers can distinguish owned
        work from collaborators before editing.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.plugin.debug_mcp.hookspec.DebugMcpHookSpec` because it
        keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - pytest_bdd_debug_mcp_artifact_created: owns nested behavior below this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/debug_mcp/entrypoint.py: imports or references `DebugMcpHookSpec`

    State and side effects:
        keeps no local persistent state beyond call-local values.

    Invariants:
        - `pytest_bdd.plugin.debug_mcp.hookspec.DebugMcpHookSpec` keeps its documented import path, ownership boundary,
          and observable behavior stable for callers.

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

    @pytest.hookspec
    def pytest_bdd_debug_mcp_artifact_created(  # noqa: PLR0913, PLR0917
        self,
        nodeid: str,
        pytest_phase: Literal["setup", "call", "teardown"],
        bdd_metadata: dict[str, object],
        json_path: Path,
        markdown_path: Path,
        status: str,
        summary: str,
    ) -> None:
        """
        Notify consumers that a debug MCP investigation artifact was written.

        Responsibility:
            Notify consumers that a debug MCP investigation artifact was written. It directly owns the observable
            contract, local decisions, and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.debug_mcp.hookspec.DebugMcpHookSpec.pytest_bdd_debug_mcp_artifact_created` because it
            keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - None, leaf-level implementation boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/debug_mcp/artifacts.py: imports or references
              `pytest_bdd_debug_mcp_artifact_created`

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
