"""
Public API facade for the scenario locator subsystem.

Responsibility:
    Public API facade for the scenario locator subsystem. Re-exports all concrete locator types (FileScenarioLocator,
    UrlScenarioLocator, PyPyUrlScenarioLocator), the abstract base (ScenarioLocator), option types
    (ScenarioLocatorFilterT, ScenarioLocatorOptions), and result types (FileLocatorResult, ScenarioLocatorResults,
    ScenarioLocatorContinuation) from the scenario_locator.facade module. This module is the stable import point for all
    scenario location concerns, allowing consumers to import from pytest_bdd.scenario_locator rather than reaching into
    internal sub-packages.

Reason for existence:
    The scenario locator subsystem is split across four internal modules (base.py, file_locator.py, url_locator.py,
    facade.py) that together implement the strategy pattern for discovering Gherkin documents — whether from local
    files, remote URLs, or PyPy-optimized URL fetching. This __init__.py serves as a stable facade that shields external
    consumers from knowing the internal module layout; if the subsystem is refactored (e.g., locators moved, split, or
    merged), only this re-export module needs updating. It sits in the collection layer (order 5) because it produces
    scenario locations consumed by the collector and ScenarioLocatorBuilder.

Delegates:
    - facade.py: Owns the public API surface — imports and re-exports ScenarioLocator, FileScenarioLocator,
    UrlScenarioLocator, PyPyUrlScenarioLocator, ScenarioLocatorFilterT, ScenarioLocatorOptions, FileLocatorResult,
    ScenarioLocatorResults, and ScenarioLocatorContinuation. This module simply star-imports from it.

Cohesion:
    All re-exported names belong to the single concern of "locate Gherkin scenarios from a given source." The module is
    a trivial pass-through with zero internal logic — it exists purely to establish the public API boundary.

Separation:
    - pytest_bdd.scenario_locator.base: Houses the abstract ScenarioLocator ABC and ScenarioLocatorContinuation; kept
    separate from this facade to prevent the base contract from being coupled to re-export concerns.
    - pytest_bdd.scenario_locator.file_locator: Implements file-system-based Gherkin discovery; kept separate because it
    carries walkdir, glob, and file-I/O dependencies that URL locators do not need.
    - pytest_bdd.scenario_locator.url_locator: Implements HTTP-based Gherkin discovery and PyPy specialization; kept
    separate because it carries network I/O and PyPy-specific dependencies.
    - pytest_bdd.feature_locator: The ScenarioLocatorBuilder consumes locator types from this facade but does not own
    locator construction — it calls the locator constructors (FileScenarioLocator, UrlScenarioLocator) directly.

Main consumers:
    - pytest_bdd.feature_locator.ScenarioLocatorBuilder: Imports FileScenarioLocator, UrlScenarioLocator,
    PyPyUrlScenarioLocator, and ScenarioLocatorFilterT directly from this facade to construct locator instances in
    _create_file_locator and _create_url_locator.
    - pytest_bdd.scenario: The scenario() and scenarios() public API functions accept locators= parameter whose type
    resolves through types imported from this facade.

State and side effects:
    None, keeps no persistent state. This module is purely a re-export layer with no mutable state, no I/O, and no
    pytest stash access.

Invariants:
    - The star-import from facade.py must always cover the complete public API; no public type may be defined in a sub-
    module without being re-exported through facade.py and this __init__.py.

Architecture score:
    #arch-eval:reason_for_existence=4
    #arch-eval:owned_responsibility=3
    #arch-eval:delegation_boundary=5
    #arch-eval:cohesion=5
    #arch-eval:separation=5
    #arch-eval:consumer_clarity=5
    #arch-eval:state_invariants=4
    #arch-eval:entity_fullness=2
    #arch-eval:locational_stability=5
"""

from pytest_bdd.scenario_locator.facade import *  # noqa: F403  -- intentional re-export or import for public API facade
