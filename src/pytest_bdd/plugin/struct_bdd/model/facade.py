"""
Backward-compatible re-exports of all public struct BDD model symbols.

Responsibility:
    Backward-compatible re-exports of all public struct BDD model symbols. It directly owns the observable contract,
    local decisions, and maintenance boundary for this module.

Reason for existence:
    This entity is the information expert for `pytest_bdd.plugin.struct_bdd.model.facade` because it keeps the nearest
    code, data shape, call signature, and failure knowledge together.

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
    depends on __future__.annotations, pytest_bdd.plugin.struct_bdd.model._base.KEYWORD_TO_TYPE,
    pytest_bdd.plugin.struct_bdd.model._base.Join, pytest_bdd.plugin.struct_bdd.model._base.Keyword,
    pytest_bdd.plugin.struct_bdd.model._base.Node.

Invariants:
    - `pytest_bdd.plugin.struct_bdd.model.facade` keeps its documented import path, ownership boundary, and observable
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

from pytest_bdd.plugin.struct_bdd.model._base import (  # noqa: F401
    KEYWORD_TO_TYPE,
    Join,
    Keyword,
    Node,
    SubKeyword,
    SubTable,
    Table,
    TableNode,
    convert_sub_tables_to_tables,
)
from pytest_bdd.plugin.struct_bdd.model._steps import (  # noqa: F401
    Alternative,
    And,
    AndStep,
    But,
    ButStep,
    Given,
    GivenStep,
    StarStep,
    Step,
    StepPrototype,
    StepStepKeywordType,
    SubStep,
    Then,
    ThenStep,
    When,
    WhenStep,
    after_convert_sub_steps_to_steps,
    before_convert_to_step,
    select_step_keyword_type,
)
