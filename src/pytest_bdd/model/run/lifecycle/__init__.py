"""
Run lifecycle package — backward-compatible facade.

Responsibility:
    Run lifecycle package — backward-compatible facade. It directly owns the observable contract, local decisions, and
    maintenance boundary for this module.

Reason for existence:
    This entity is the information expert for `pytest_bdd.model.run.lifecycle` because it keeps the nearest code, data
    shape, call signature, and failure knowledge together.

Delegates:
    - None, leaf-level implementation boundary

Cohesion:
    The implementation stays together because its imports, calls, state writes, and return contract describe one
    maintainable decision unit.

Separation:
    - module peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
      widening caller knowledge.

Main consumers:
    - src/pytest_bdd/model/run/__init__.py: imports or references `lifecycle`
    - src/pytest_bdd/plugin/gherkin_message_reporter/entrypoint.py: imports or references `lifecycle`

State and side effects:
    depends on __future__.annotations, facade.*.

Invariants:
    - `pytest_bdd.model.run.lifecycle` keeps its documented import path, ownership boundary, and observable behavior
      stable for callers.

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
# init: no-check

from __future__ import annotations

from .facade import *  # noqa: F403
