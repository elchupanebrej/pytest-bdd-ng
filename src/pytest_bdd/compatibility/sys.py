"""
Provide sys compatibility helpers.

Responsibility:
    Provide sys compatibility helpers. It directly owns the observable contract, local decisions, and maintenance
    boundary for this module. That boundary is intentionally stated in prose so maintainers can distinguish owned work
    from collaborators before editing.

Reason for existence:
    This entity is the information expert for `pytest_bdd.compatibility.sys` because it keeps the nearest code, data
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
    - src/pytest_bdd/_gherkin_go/_bridge.py: imports or references `sys`
    - src/pytest_bdd/_gherkin_go/_build.py: imports or references `sys`
    - src/pytest_bdd/_pylint/checkers/layer_rules.py: imports or references `sys`
    - src/pytest_bdd/compatibility/enum.py: imports or references `sys`
    - src/pytest_bdd/compatibility/path.py: imports or references `sys`

State and side effects:
    mutates get_frame; depends on sys._getframe.

Invariants:
    - `pytest_bdd.compatibility.sys` keeps its documented import path, ownership boundary, and observable behavior
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
    #arch-eval:locational_stability=4
"""

from sys import _getframe

get_frame = _getframe
