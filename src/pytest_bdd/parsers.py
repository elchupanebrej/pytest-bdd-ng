"""
Backward compatibility stub — delegates to parsers/ package.

Responsibility:
    Backward compatibility stub — delegates to parsers/ package. It directly owns the observable contract, local
    decisions, and maintenance boundary for this module.

Reason for existence:
    This entity is the information expert for `pytest_bdd.parsers` because it keeps the nearest code, data shape, call
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
    - src/pytest_bdd/plugin/gherkin_message_reporter/step_catalog_runtime/_static_helpers.py: imports or references
      `parsers`
    - src/pytest_bdd/plugin/pickle_runner/entrypoint.py: imports or references `parsers`
    - src/pytest_bdd/steps/definition.py: imports or references `parsers`
    - src/pytest_bdd/steps/manager.py: imports or references `parsers`

State and side effects:
    depends on pytest_bdd.parsers.facade.*.

Invariants:
    - `pytest_bdd.parsers` keeps its documented import path, ownership boundary, and observable behavior stable for
      callers.

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

from pytest_bdd.parsers.facade import *  # noqa: F403
