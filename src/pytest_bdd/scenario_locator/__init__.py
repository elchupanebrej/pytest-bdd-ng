"""
Serves as a public API facade that explicitly re-exports the complete scenario_locator public API — including FileSce.

Responsibility:
    Serves as a public API facade that explicitly re-exports the complete scenario_locator public API — including
    FileScenarioLocator, FileScenarioLocatorDefaults, UrlScenarioLocator, PyPyUrlScenarioLocator,
    ScenarioLocatorFilterMixin, ScenarioLocatorFilterT, and ScenarioLocatorResolver — from the
    pytest_bdd.scenario_locator.facade subpackage. This module is the canonical import point for any code that needs to
    resolve and filter BDD scenarios from file systems or URLs during test collection.

Reason for existence:
    Provides a clean, stable import path (pytest_bdd.scenario_locator) for scenario location infrastructure while
    keeping implementation organized across multiple subpackage modules (base.py for protocols, file_locator.py and
    url_locator.py for concrete implementations, facade.py for re-export aggregation). This follows the facade pattern
    used throughout pytest-bdd where package __init__.py modules explicitly import and re-export the public API, giving
    consumers a single import target while allowing internal module reorganization without breaking external code.

Delegates:
    - pytest_bdd.scenario_locator.facade: All public API symbols are explicitly imported from this module, which
    aggregates re-exports from base, file_locator, and url_locator.
    - pytest_bdd.scenario_locator.base: Defines protocol classes (ScenarioLocatorFeatureResolver,
    ScenarioLocatorReadObserver, ScenarioLocatorResolver, ScenarioLocatorHookProtocol, ScenarioLocatorFilterMixin) and
    type aliases (ScenarioLocatorFilterT).
    - pytest_bdd.scenario_locator.file_locator: Implements file-system-based scenario location (FileScenarioLocator,
    FileScenarioLocatorDefaults).
    - pytest_bdd.scenario_locator.url_locator: Implements URL-based scenario location with both async/aiohttp and PyPy-
    compatible synchronous variants (UrlScenarioLocator, PyPyUrlScenarioLocator).

Cohesion:
    Perfect cohesion as a facade: the single responsibility is re-exporting the scenario_locator public API. Each import
    is explicit (not wildcard) with `as` aliasing, providing clear traceability of which symbols are exposed.

Separation:
    - pytest_bdd.scenario_locator.facade: Kept separate because facade.py aggregates re-exports with justification
    comments for each import category, while __init__.py provides the clean consumer-facing import path — facade is the
    "truth source" for the public API surface.
    - pytest_bdd.collector: Kept separate because the collector module owns the test collection lifecycle (pytest
    collection hooks and test item creation), while scenario_locator owns the feature file/pickle discovery and
    filtering — the collector consumes the locator but does not own location logic.

Main consumers:
    - pytest_bdd.collector: Imports FileScenarioLocator to discover feature files and their pickles during test
    collection, passing the results to the test item factory.
    - pytest_bdd.scenario: Uses scenario locators when the `scenarios()` function is called with directory or URL paths,
    routing to the appropriate locator based on the path type.
    - Plugin entry points and conftest.py files: May import ScenarioLocatorFilterT or ScenarioLocatorResolver for custom
    scenario filtering or resolution logic.

State and side effects:
    None, keeps no persistent state. All imports execute at module load time but have no side effects beyond namespace
    population.

Invariants:
    - Every public API type defined in the scenario_locator subpackage must be exportable through this __init__.py
    without requiring additional imports.
    - Import aliasing (`as` clauses) must preserve the original class names exactly as defined in their source modules.

Architecture score:
    #arch-eval:reason_for_existence=4
    #arch-eval:owned_responsibility=2
    #arch-eval:delegation_boundary=5
    #arch-eval:cohesion=5
    #arch-eval:separation=4
    #arch-eval:consumer_clarity=5
    #arch-eval:state_invariants=5
    #arch-eval:entity_fullness=2
    #arch-eval:locational_stability=5
"""

__all__: list[str] = [
    "FileScenarioLocator",
    "FileScenarioLocatorDefaults",
    "PyPyUrlScenarioLocator",
    "ScenarioLocatorFilterMixin",
    "ScenarioLocatorFilterT",
    "ScenarioLocatorResolver",
    "UrlScenarioLocator",
]

from pytest_bdd.scenario_locator.facade import (
    FileScenarioLocator,
    FileScenarioLocatorDefaults,
    PyPyUrlScenarioLocator,
    ScenarioLocatorFilterMixin,
    ScenarioLocatorFilterT,
    ScenarioLocatorResolver,
    UrlScenarioLocator,
)
