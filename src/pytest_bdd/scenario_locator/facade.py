"""
Backward-compatible re-exports of all public scenario locators.

Responsibility:
    Backward-compatible re-exports of all public scenario locators. It directly owns the observable contract, local
    decisions, and maintenance boundary for this module.

Reason for existence:
    This entity is the information expert for `pytest_bdd.scenario_locator.facade` because it keeps the nearest code,
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
    - src/pytest_bdd/scenario_locator.py: imports or references `facade`
    - src/pytest_bdd/scenario_locator/__init__.py: imports or references `facade`

State and side effects:
    depends on __future__.annotations, pytest_bdd.scenario_locator.base.ScenarioLocatorFeatureResolver,
    pytest_bdd.scenario_locator.base.ScenarioLocatorFilterMixin,
    pytest_bdd.scenario_locator.base.ScenarioLocatorFilterT,
    pytest_bdd.scenario_locator.base.ScenarioLocatorHookProtocol.

Invariants:
    - `pytest_bdd.scenario_locator.facade` keeps its documented import path, ownership boundary, and observable behavior
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
    #arch-eval:locational_stability=3
"""

from __future__ import annotations

from pytest_bdd.scenario_locator.base import (  # noqa: F401
    ScenarioLocatorFeatureResolver,
    ScenarioLocatorFilterMixin,
    ScenarioLocatorFilterT,
    ScenarioLocatorHookProtocol,
    ScenarioLocatorReadObserver,
    ScenarioLocatorResolver,
)
from pytest_bdd.scenario_locator.file_locator import (  # noqa: F401
    FileScenarioLocator,
    FileScenarioLocatorDefaults,
)
from pytest_bdd.scenario_locator.url_locator import (  # noqa: F401
    PyPyUrlScenarioLocator,
    UrlScenarioLocator,
)
