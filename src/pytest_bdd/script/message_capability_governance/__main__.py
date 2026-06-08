"""
Allow running the package as a module: python -m pytest_bdd.script.message_capability_governance.

Responsibility:
    Allow running the package as a module: python -m pytest_bdd.script.message_capability_governance. It directly owns
    the observable contract, local decisions, and maintenance boundary for this module.

Reason for existence:
    This entity is the information expert for `pytest_bdd.script.message_capability_governance.__main__` because it
    keeps the nearest code, data shape, call signature, and failure knowledge together.

Delegates:
    - SystemExit: collaborator call used by this boundary
    - main: collaborator call used by this boundary

Cohesion:
    The implementation stays together because its imports, calls, state writes, and return contract describe one
    maintainable decision unit.

Separation:
    - module peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
      widening caller knowledge.

Main consumers:
    - None found by static import/name scan; verify dynamic use before refactor

State and side effects:
    depends on __future__.annotations, pytest_bdd.script.message_capability_governance.cli.main.

Invariants:
    - `pytest_bdd.script.message_capability_governance.__main__` keeps its documented import path, ownership boundary,
      and observable behavior stable for callers.

Failure semantics:
    Raises or re-raises SystemExit; callers must treat these as boundary failures.

Architecture score:
    #arch-eval:reason_for_existence=4
    #arch-eval:owned_responsibility=4
    #arch-eval:delegation_boundary=4
    #arch-eval:cohesion=3
    #arch-eval:separation=3
    #arch-eval:consumer_clarity=2
    #arch-eval:state_invariants=4
    #arch-eval:entity_fullness=2
    #arch-eval:locational_stability=2
"""

from __future__ import annotations

from pytest_bdd.script.message_capability_governance.cli import main

raise SystemExit(main())
