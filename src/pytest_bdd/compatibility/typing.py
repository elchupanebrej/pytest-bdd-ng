"""
Provide typing helpers.

Responsibility:
    Provide typing helpers. It directly owns the observable contract, local decisions, and maintenance boundary for this
    module. That boundary is intentionally stated in prose so maintainers can distinguish owned work from collaborators
    before editing.

Reason for existence:
    This entity is the information expert for `pytest_bdd.compatibility.typing` because it keeps the nearest code, data
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
    - src/pytest_bdd/model/run/lifecycle/_run.py: imports or references `typing`
    - src/pytest_bdd/model/run/refs.py: imports or references `typing`
    - src/pytest_bdd/plugin/struct_bdd/model/_steps.py: imports or references `typing`

State and side effects:
    depends on sys, typing.TypeAlias, typing.Self, typing_extensions.Self.

Invariants:
    - `pytest_bdd.compatibility.typing` keeps its documented import path, ownership boundary, and observable behavior
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
from typing import TypeAlias  # noqa: F401

if sys.version_info >= (3, 11):
    from typing import Self
else:
    from typing_extensions import Self  # noqa: F401
