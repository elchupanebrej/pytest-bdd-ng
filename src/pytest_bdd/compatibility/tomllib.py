"""
Provide tomllib helpers.

Responsibility:
    Provide tomllib helpers. It directly owns the observable contract, local decisions, and maintenance boundary for
    this module. That boundary is intentionally stated in prose so maintainers can distinguish owned work from
    collaborators before editing.

Reason for existence:
    This entity is the information expert for `pytest_bdd.compatibility.tomllib` because it keeps the nearest code, data
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
    - src/pytest_bdd/_pylint/checkers/layer_rules.py: imports or references `tomllib`
    - src/pytest_bdd/_pylint/checkers/test_import_rules.py: imports or references `tomllib`
    - src/pytest_bdd/plugin/struct_bdd/parser.py: imports or references `tomllib`
    - src/pytest_bdd/util/tests_group_ordering/config.py: imports or references `tomllib`

State and side effects:
    depends on sys, tomllib.TOMLDecodeError, tomllib.load, tomllib.loads, tomli.TOMLDecodeError.

Invariants:
    - `pytest_bdd.compatibility.tomllib` keeps its documented import path, ownership boundary, and observable behavior
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
    #arch-eval:locational_stability=4
"""

import sys

if sys.version_info >= (3, 11):
    from tomllib import TOMLDecodeError, load, loads
else:
    from tomli import TOMLDecodeError, load, loads  # noqa: F401
