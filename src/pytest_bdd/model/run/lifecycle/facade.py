"""
Backward-compatible re-exports of all public lifecycle symbols.

Responsibility:
    Backward-compatible re-exports of all public lifecycle symbols. It directly owns the observable contract, local
    decisions, and maintenance boundary for this module.

Reason for existence:
    This entity is the information expert for `pytest_bdd.model.run.lifecycle.facade` because it keeps the nearest code,
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
    - None found by static import/name scan; verify dynamic use before refactor

State and side effects:
    depends on __future__.annotations, pytest_bdd.model.run.lifecycle._run.NodeKind,
    pytest_bdd.model.run.lifecycle._run.Run, pytest_bdd.model.run.lifecycle._run.ScenarioRunResult,
    pytest_bdd.model.run.lifecycle._snapshots.ExternalApiCompatibilityRecord.

Invariants:
    - `pytest_bdd.model.run.lifecycle.facade` keeps its documented import path, ownership boundary, and observable
      behavior stable for callers.

Architecture score:
    #arch-eval:reason_for_existence=4
    #arch-eval:owned_responsibility=4
    #arch-eval:delegation_boundary=2
    #arch-eval:cohesion=3
    #arch-eval:separation=3
    #arch-eval:consumer_clarity=2
    #arch-eval:state_invariants=3
    #arch-eval:entity_fullness=2
    #arch-eval:locational_stability=2
"""

from __future__ import annotations

from pytest_bdd.model.run.lifecycle._run import (  # noqa: F401
    NodeKind,
    Run,
    ScenarioRunResult,
)
from pytest_bdd.model.run.lifecycle._snapshots import (  # noqa: F401
    ExternalApiCompatibilityRecord,
    ReportingContextSnapshot,
)
from pytest_bdd.model.run.lifecycle._states import (  # noqa: F401
    ActiveObjectSet,
    ContextErrorState,
    ReferenceResolverState,
    ReportingLifecycleState,
)
