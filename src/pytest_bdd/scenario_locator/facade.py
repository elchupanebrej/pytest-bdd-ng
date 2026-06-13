"""
Serves as the public API aggregation module for the scenario_locator subpackage, explicitly re-exporting all public p.

Responsibility:
    Serves as the public API aggregation module for the scenario_locator subpackage, explicitly re-exporting all public
    protocol types (ScenarioLocatorFeatureResolver, ScenarioLocatorReadObserver, ScenarioLocatorResolver,
    ScenarioLocatorHookProtocol), the filter mixin (ScenarioLocatorFilterMixin with ScenarioLocatorFilterT type alias),
    and concrete locator implementations (FileScenarioLocator, FileScenarioLocatorDefaults, UrlScenarioLocator,
    PyPyUrlScenarioLocator). Each import is annotated with justification for F401 suppression, making the public API
    contract explicit and reviewable.

Reason for existence:
    The scenario_locator subpackage contains 4 module files (base, file_locator, url_locator, plus __init__) with
    protocol definitions, concrete implementations, and internal logic. This facade module aggregates all public symbols
    into a single import target that the __init__.py re-exports. Without this facade, consumers would need to know which
    internal module defines each class (e.g., FileScenarioLocator is in file_locator, UrlScenarioLocator is in
    url_locator). The facade also serves as documentation of what constitutes the public API boundary.

Delegates:
    - pytest_bdd.scenario_locator.base: Provides protocol classes, filter mixin, and type aliases.
    - pytest_bdd.scenario_locator.file_locator: Provides FileScenarioLocator and FileScenarioLocatorDefaults.
    - pytest_bdd.scenario_locator.url_locator: Provides UrlScenarioLocator and PyPyUrlScenarioLocator.

Cohesion:
    Every import serves the purpose of exposing the scenario_locator public API. Imports are organized by source module
    with justification comments.

Separation:
    - pytest_bdd.scenario_locator.__init__: Kept separate because __init__.py provides the consumer-facing import path
    with explicit as-aliasing, while facade.py aggregates and documents the imports — consumer API vs internal
    aggregation.

Main consumers:
    - pytest_bdd.scenario_locator.__init__: Re-exports all symbols for consumer access.
    - pytest_bdd.collector: Imports scenario locator classes for test collection.

State and side effects:
    None. All imports are read-only namespace operations.

Invariants:
    - Every public type defined in the subpackage must be re-exported through this facade.

Architecture score:
    #arch-eval:reason_for_existence=4
    #arch-eval:owned_responsibility=3
    #arch-eval:delegation_boundary=5
    #arch-eval:cohesion=5
    #arch-eval:separation=4
    #arch-eval:consumer_clarity=5
    #arch-eval:state_invariants=5
    #arch-eval:entity_fullness=2
    #arch-eval:locational_stability=4
"""

from __future__ import annotations

from pytest_bdd.scenario_locator.base import (  # noqa: F401  -- intentional re-export; facade exposes full scenario_locator public API
    ScenarioLocatorFeatureResolver,
    ScenarioLocatorFilterMixin,
    ScenarioLocatorFilterT,
    ScenarioLocatorHookProtocol,
    ScenarioLocatorReadObserver,
    ScenarioLocatorResolver,
)
from pytest_bdd.scenario_locator.file_locator import (  # noqa: F401  -- intentional re-export; facade exposes full scenario_locator public API
    FileScenarioLocator,
    FileScenarioLocatorDefaults,
)
from pytest_bdd.scenario_locator.url_locator import (  # noqa: F401  -- intentional re-export; facade exposes full scenario_locator public API
    PyPyUrlScenarioLocator,
    UrlScenarioLocator,
)
