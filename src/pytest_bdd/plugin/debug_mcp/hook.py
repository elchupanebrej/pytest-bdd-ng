"""
Pytest hooks for debug MCP failure handling.

Responsibility:
    Pytest hooks for debug MCP failure handling. It directly owns the observable contract, local decisions, and
    maintenance boundary for this module.

Reason for existence:
    This entity is the information expert for `pytest_bdd.plugin.debug_mcp.hook` because it keeps the nearest code, data
    shape, call signature, and failure knowledge together.

Delegates:
    - pytest_runtest_makereport: owns nested behavior below this boundary
    - _should_queue: owns nested behavior below this boundary

Cohesion:
    The implementation stays together because its imports, calls, state writes, and return contract describe one
    maintainable decision unit.

Separation:
    - module peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
      widening caller knowledge.

Main consumers:
    - src/pytest_bdd/hook.py: imports or references `hook`
    - src/pytest_bdd/plugin/code_generator/collection.py: imports or references `hook`
    - src/pytest_bdd/plugin/code_generator/plugin.py: imports or references `hook`
    - src/pytest_bdd/plugin/debug_mcp/artifacts.py: imports or references `hook`
    - src/pytest_bdd/plugin/debug_mcp/entrypoint.py: imports or references `hook`

State and side effects:
    mutates outcome, report, state, failure; depends on __future__.annotations, typing.TYPE_CHECKING, typing.cast,
    pytest, bdd_adapter.enrich_failure_with_bdd_context.

Invariants:
    - `pytest_bdd.plugin.debug_mcp.hook` keeps its documented import path, ownership boundary, and observable behavior
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

from typing import TYPE_CHECKING, cast

import pytest

from .bdd_adapter import enrich_failure_with_bdd_context
from .failure import QueuedFailure
from .state import DebugMcpState

if TYPE_CHECKING:
    from collections.abc import Generator

    from pluggy import Result

    from pytest_bdd.compatibility.pytest import CallInfo, Item, TestReport


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item: Item, call: CallInfo) -> Generator[None, object, None]:
    """
    Queue failed setup/call/teardown reports for debug MCP.

    Responsibility:
        Queue failed setup/call/teardown reports for debug MCP. It directly owns the observable contract, local
        decisions, and maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.plugin.debug_mcp.hook.pytest_runtest_makereport` because
        it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - cast: collaborator call used by this boundary
        - outcome.get_result: collaborator call used by this boundary
        - _should_queue: collaborator call used by this boundary
        - DebugMcpState.find_in_stash.value_or: collaborator call used by this boundary
        - DebugMcpState.find_in_stash: collaborator call used by this boundary
        - enrich_failure_with_bdd_context: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/debug_mcp/entrypoint.py: imports or references `pytest_runtest_makereport`

    State and side effects:
        mutates outcome, report, state, failure.

    Invariants:
        - `pytest_bdd.plugin.debug_mcp.hook.pytest_runtest_makereport` keeps its documented import path, ownership
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
    del call
    outcome = cast("Result", (yield))
    report = outcome.get_result()
    if not _should_queue(report):
        return

    state = DebugMcpState.find_in_stash(item.config.stash).value_or(None)
    if state is None or state.queue is None:
        return
    failure = enrich_failure_with_bdd_context(item.config, QueuedFailure.from_report(report))
    state.queue.hold_failure(failure, state=state)


def _should_queue(report: TestReport) -> bool:
    """
    Responsibility:
        Responsibility: Responsibility: `pytest_bdd.plugin.debug_mcp.hook._should_queue` owns documented function
        behavior. It directly owns the observable contract, local decisions, and maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.plugin.debug_mcp.hook._should_queue` because it keeps the
        nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - bool: collaborator call used by this boundary

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
    return bool(report.failed and report.when in {"setup", "call", "teardown"})
