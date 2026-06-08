"""
Provide pathlib helpers.

Responsibility:
    Provide pathlib helpers. It directly owns the observable contract, local decisions, and maintenance boundary for
    this module. That boundary is intentionally stated in prose so maintainers can distinguish owned work from
    collaborators before editing.

Reason for existence:
    This entity is the information expert for `pytest_bdd.compatibility.pathlib` because it keeps the nearest code, data
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
    - src/pytest_bdd/scenario_locator/file_locator.py: imports or references `pathlib`

State and side effects:
    mutates GlobError; depends on sys.

Invariants:
    - `pytest_bdd.compatibility.pathlib` keeps its documented import path, ownership boundary, and observable behavior
      stable for callers.

Architecture score:
    #arch-eval:reason_for_existence=4
    #arch-eval:owned_responsibility=4
    #arch-eval:delegation_boundary=2
    #arch-eval:cohesion=3
    #arch-eval:separation=3
    #arch-eval:consumer_clarity=4
    #arch-eval:state_invariants=4
    #arch-eval:entity_fullness=2
    #arch-eval:locational_stability=3
"""

import sys

GlobError = IndexError if sys.version_info < (3, 13) else ValueError
