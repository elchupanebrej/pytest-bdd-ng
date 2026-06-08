# init: public-api  # init: no-check
"""
Provide pytest-bdd shared type helpers.

Responsibility:
    Provide pytest-bdd shared type helpers. It directly owns the observable contract, local decisions, and maintenance
    boundary for this module.

Reason for existence:
    This entity is the information expert for `pytest_bdd.types` because it keeps the nearest code, data shape, call
    signature, and failure knowledge together.

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
    depends on pytest_bdd.types.failure_reasons.CollectorFailure,
    pytest_bdd.types.failure_reasons.FeatureLocatorFailure, pytest_bdd.types.failure_reasons.GenericFailure,
    pytest_bdd.types.failure_reasons.MessageValidationFailure, pytest_bdd.types.failure_reasons.ParserFailure.

Invariants:
    - `pytest_bdd.types` keeps its documented import path, ownership boundary, and observable behavior stable for
      callers.

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

from pytest_bdd.types.failure_reasons import (
    CollectorFailure as CollectorFailure,
)
from pytest_bdd.types.failure_reasons import (
    FeatureLocatorFailure as FeatureLocatorFailure,
)
from pytest_bdd.types.failure_reasons import (
    GenericFailure as GenericFailure,
)
from pytest_bdd.types.failure_reasons import (
    MessageValidationFailure as MessageValidationFailure,
)
from pytest_bdd.types.failure_reasons import (
    ParserFailure as ParserFailure,
)
from pytest_bdd.types.failure_reasons import (
    ScenarioRunFailure as ScenarioRunFailure,
)
from pytest_bdd.types.failure_reasons import (
    StashFailure as StashFailure,
)
