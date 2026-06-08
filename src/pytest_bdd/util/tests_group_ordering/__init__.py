# init: public-api  # init: no-check
"""
Test group ordering helpers for pytest-bdd-ng.

Responsibility:
    Test group ordering helpers for pytest-bdd-ng. It directly owns the observable contract, local decisions, and
    maintenance boundary for this module.

Reason for existence:
    This entity is the information expert for `pytest_bdd.util.tests_group_ordering` because it keeps the nearest code,
    data shape, call signature, and failure knowledge together.

Delegates:
    - None, leaf-level implementation boundary

Cohesion:
    The implementation stays together because its imports, calls, state writes, and return contract describe one
    maintainable decision unit.

Separation:
    - module peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
      widening caller knowledge.

Main consumers:
    - src/pytest_bdd/plugin/test_group_ordering/entrypoint.py: imports or references `tests_group_ordering`

State and side effects:
    depends on pytest_bdd.util.tests_group_ordering.facade.*.

Invariants:
    - `pytest_bdd.util.tests_group_ordering` keeps its documented import path, ownership boundary, and observable
      behavior stable for callers.

Architecture score:
    #arch-eval:reason_for_existence=4
    #arch-eval:owned_responsibility=4
    #arch-eval:delegation_boundary=2
    #arch-eval:cohesion=3
    #arch-eval:separation=3
    #arch-eval:consumer_clarity=4
    #arch-eval:state_invariants=3
    #arch-eval:entity_fullness=2
    #arch-eval:locational_stability=3
"""

from pytest_bdd.util.tests_group_ordering.facade import *  # noqa: F403
