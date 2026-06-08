"""
Register pytest-bdd test group ordering config options.

Responsibility:
    Register pytest-bdd test group ordering config options. It directly owns the observable contract, local decisions,
    and maintenance boundary for this module.

Reason for existence:
    This entity is the information expert for `pytest_bdd.plugin.test_group_ordering.entrypoint` because it keeps the
    nearest code, data shape, call signature, and failure knowledge together.

Delegates:
    - pytest_addoption: owns nested behavior below this boundary

Cohesion:
    The implementation stays together because its imports, calls, state writes, and return contract describe one
    maintainable decision unit.

Separation:
    - module peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
      widening caller knowledge.

Main consumers:
    - src/pytest_bdd/util/cucumber_formatter_support/registry.py: imports or references `entrypoint`

State and side effects:
    depends on __future__.annotations, typing.Any, pytest_bdd.util.tests_group_ordering.register_group_config_options.

Invariants:
    - `pytest_bdd.plugin.test_group_ordering.entrypoint` keeps its documented import path, ownership boundary, and
      observable behavior stable for callers.

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

from __future__ import annotations

from typing import Any

from pytest_bdd.util.tests_group_ordering import register_group_config_options


def pytest_addoption(parser: Any) -> None:
    """
    Register test group ordering ini options.

    Responsibility:
        Register test group ordering ini options. It directly owns the observable contract, local decisions, and
        maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.plugin.test_group_ordering.entrypoint.pytest_addoption`
        because it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - register_group_config_options: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/debug_mcp/entrypoint.py: imports or references `pytest_addoption`

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
    register_group_config_options(parser)
