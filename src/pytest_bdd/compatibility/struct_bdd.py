"""
Provide struct bdd helpers.

Responsibility:
    Provide struct bdd helpers. It directly owns the observable contract, local decisions, and maintenance boundary for
    this module. That boundary is intentionally stated in prose so maintainers can distinguish owned work from
    collaborators before editing.

Reason for existence:
    This entity is the information expert for `pytest_bdd.compatibility.struct_bdd` because it keeps the nearest code,
    data shape, call signature, and failure knowledge together.

Delegates:
    - importlib.util.find_spec: collaborator call used by this boundary

Cohesion:
    The implementation stays together because its imports, calls, state writes, and return contract describe one
    maintainable decision unit.

Separation:
    - module peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
      widening caller knowledge.

Main consumers:
    - src/pytest_bdd/mimetype.py: imports or references `struct_bdd`
    - src/pytest_bdd/parser.py: imports or references `struct_bdd`
    - src/pytest_bdd/plugin/struct_bdd/entrypoint.py: imports or references `struct_bdd`

State and side effects:
    mutates STRUCT_BDD_INSTALLED; depends on importlib.util.

Invariants:
    - `pytest_bdd.compatibility.struct_bdd` keeps its documented import path, ownership boundary, and observable
      behavior stable for callers.

Architecture score:
    #arch-eval:reason_for_existence=4
    #arch-eval:owned_responsibility=4
    #arch-eval:delegation_boundary=4
    #arch-eval:cohesion=3
    #arch-eval:separation=3
    #arch-eval:consumer_clarity=4
    #arch-eval:state_invariants=4
    #arch-eval:entity_fullness=2
    #arch-eval:locational_stability=4
"""

import importlib.util

STRUCT_BDD_INSTALLED = importlib.util.find_spec("pytest_bdd.plugin.struct_bdd.parser") is not None
