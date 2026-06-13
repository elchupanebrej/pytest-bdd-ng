# init: public-api  # init: no-check
"""
Top-level public API entry point for the pytest-bdd-ng library.

Responsibility:
    Top-level public API entry point for the pytest-bdd-ng library. Directly re-exports the three primary user-facing
    symbols (scenario, scenarios, FeaturePathType) and provides PEP 562 lazy-loading for seven additional symbols
    (given, when, then, step, tolerant, not_implemented, PytestBDDStepDefinitionWarning) plus a computed __version__
    attribute. This module is the only import path end users should use: `from pytest_bdd import scenario, given, when,
    then`. All internal layout changes are hidden behind this stable facade.

Reason for existence:
    This module exists as the library's public contract boundary. It is the information expert for "what does pytest-
    bdd-ng expose to users." Every other module in the codebase is an internal implementation detail that may be
    refactored, renamed, or re-layered; only the names re-exported from here form the semantic versioning contract. The
    lazy-loading via __getattr__ (PEP 562) means step decorators and warning types are not imported until actually
    accessed, keeping the import footprint minimal for users who only need scenario() or scenarios(). The __version__
    attribute is computed dynamically from the installed distribution metadata rather than being hardcoded, ensuring
    accuracy even when multiple versions coexist.

Delegates:
    - pytest_bdd.scenario: Owns the scenario() and scenarios() functions and the FeaturePathType enum. This module
    simply re-exports them.
    - pytest_bdd.steps: Owns the step decorator functions (given, when, then, step, tolerant, not_implemented). Lazily
    loaded in __getattr__.
    - pytest_bdd.types.warning: Owns PytestBDDStepDefinitionWarning. Lazily loaded in __getattr__.
    - pytest_bdd.util.packaging: Owns get_distribution_version(). Lazily loaded in __getattr__ for __version__.

Cohesion:
    All logic in this module serves the single purpose of defining and enforcing the public API surface. The direct re-
    exports (scenario, scenarios, FeaturePathType) are always available; the lazy-loaded symbols reduce import overhead
    while maintaining discoverability. There are no unrelated concerns — no parsing, no collection, no runtime logic.

Separation:
    - pytest_bdd.scenario: Kept separate because it owns the full implementation of scenario() and scenarios() with all
    their parameter handling, overloads, and marker composition. Merging that logic here would couple the facade to
    implementation details.
    - pytest_bdd.steps: Kept separate because step decorators involve the full Definition/Registry/Matcher subsystem.
    The lazy-load ensures users who never write step definitions (e.g., they only run features) never pay the import
    cost.
    - pytest_bdd.types.warning: Kept separate because warning type definitions belong in the types module alongside
    other custom exception and warning types.

Main consumers:
    - End-user test suites: Import from pytest_bdd to decorate test functions with @scenario, or use @given/@when/@then
    for step definitions. This is the primary documented import path.
    - pytest_bdd.plugin.scenario_test_collector: Imports from pytest_bdd to access scenario() for automatic test
    generation during pytest collection.
    - Downstream libraries/packages: Depend on the stable re-export surface defined by this module.

State and side effects:
    Module-level state consists of lazy-loaded attribute cache (Python's module attribute dict populated on first access
    via __getattr__). The __version__ attribute is computed once per process via get_distribution_version() and cached
    internally by the packaging utility. No pytest stash access, no file I/O, no configuration reads.

Invariants:
    - Every public symbol re-exported here must have a semantically versioned stability contract; internal-only symbols
    must not be added to __getattr__.
    - The lazy-load mapping in __getattr__ must stay in sync with the actual exports from pytest_bdd.steps; if a
    decorator is added or removed there, __getattr__ must be updated.
    - __getattr__ must raise AttributeError with a descriptive message for unrecognized names to conform to PEP 562.

Failure semantics:
    __getattr__ raises AttributeError for any name not in the known set of lazy-loaded symbols (given, when, then, step,
    tolerant, not_implemented, PytestBDDStepDefinitionWarning, __version__). Callers should catch AttributeError if
    probing for optional attributes, though in practice this is handled by Python's normal attribute access protocol.

Architecture score:
    #arch-eval:reason_for_existence=5
    #arch-eval:owned_responsibility=5
    #arch-eval:delegation_boundary=5
    #arch-eval:cohesion=5
    #arch-eval:separation=5
    #arch-eval:consumer_clarity=5
    #arch-eval:state_invariants=5
    #arch-eval:entity_fullness=2
    #arch-eval:locational_stability=5
"""

from __future__ import annotations

from typing import TYPE_CHECKING

__all__: list[str] = [
    "FeaturePathType",
    "PytestBDDStepDefinitionWarning",
    "given",
    "not_implemented",
    "scenario",
    "scenarios",
    "step",
    "then",
    "tolerant",
    "when",
]

from pytest_bdd.scenario import FeaturePathType as FeaturePathType
from pytest_bdd.scenario import scenario as scenario
from pytest_bdd.scenario import scenarios as scenarios

if TYPE_CHECKING:  # pragma: no cover
    from pytest_bdd.steps import given as given
    from pytest_bdd.steps import not_implemented as not_implemented
    from pytest_bdd.steps import step as step
    from pytest_bdd.steps import then as then
    from pytest_bdd.steps import tolerant as tolerant
    from pytest_bdd.steps import when as when
    from pytest_bdd.types.warning import PytestBDDStepDefinitionWarning as PytestBDDStepDefinitionWarning


def __getattr__(name: str) -> object:
    """
    PEP 562 module-level __getattr__ that implements lazy-loading for the step decorator functions.

    Responsibility:
        PEP 562 module-level __getattr__ that implements lazy-loading for the step decorator functions (given, when,
        then, step, tolerant, not_implemented), the PytestBDDStepDefinitionWarning exception type, and the computed
        __version__ string. When a consumer accesses `pytest_bdd.given` or `pytest_bdd.__version__`, this function
        dynamically imports the relevant sub-module, caches the result in the module's __dict__, and returns it. For any
        unrecognized name, it raises AttributeError as required by PEP 562.

    Reason for existence:
        Without lazy loading, importing pytest_bdd would eagerly pull in the entire steps subsystem (Definition,
        Registry, Matcher, all parser backends) and the packaging utility for every user, even those who only call
        scenario() and never write step definitions. This function concentrates the lazy-load decision into a single
        dispatch point, making it the information expert for "what symbols are available but not eagerly imported." The
        PEP 562 protocol is the standard Python mechanism for module-level attribute access control; this is the natural
        location for it since it sits on the public API boundary.

    Delegates:
        - pytest_bdd.steps: Provides the actual given, when, then, step, tolerant, and not_implemented decorator
        functions that are imported and returned on first access.
        - pytest_bdd.types.warning: Provides the PytestBDDStepDefinitionWarning class returned on first access.
        - pytest_bdd.util.packaging.get_distribution_version: Computes the installed package version
          string for __version__.

    Cohesion:
        All branches of this function serve the same purpose: resolve a name to its implementation via lazy import. The
        dispatch is a simple dictionary-like lookup; there is no unrelated logic, no side effects beyond the import, and
        no shared mutable state between calls.

    Separation:
        - pytest_bdd.scenario: The scenario() and scenarios() functions are eagerly imported at module level because
        they are the most commonly used entry points. They are not routed through __getattr__.
        - pytest_bdd.steps.decorators: The individual decorator functions are defined in decorators.py and re-exported
        through steps/__init__.py; __getattr__ only needs to know about the latter.

    Main consumers:
        - End-user test code: Accesses `pytest_bdd.given`, `pytest_bdd.when`, `pytest_bdd.then` etc. which triggers this
        function on first use.
        - Code introspection tools: Accessing `pytest_bdd.__version__` calls this function to compute and return the
        version string.
        - Python's attribute access machinery: The interpreter itself calls __getattr__ for any module attribute not
        found in the module's __dict__.

    State and side effects:
        On first access of each lazy symbol, this function performs a one-time import and caches the result in the
        module's __dict__ (via normal Python attribute set). Subsequent accesses for the same name bypass __getattr__
        entirely. No file I/O, no pytest stash access, no configuration reads. The __version__ cache (inside
        get_distribution_version) may persist across calls.

    Failure semantics:
        Raises AttributeError with the message `module 'pytest_bdd' has no attribute '{name}'` for any name not in the
        recognized set {given, not_implemented, step, then, tolerant, when, PytestBDDStepDefinitionWarning,
        __version__}. If the lazy import itself fails (e.g., missing dependency), the ImportError propagates to the
        caller and is not caught here.

    Architecture score:
        #arch-eval:reason_for_existence=5
        #arch-eval:owned_responsibility=5
        #arch-eval:delegation_boundary=5
        #arch-eval:cohesion=5
        #arch-eval:separation=5
        #arch-eval:consumer_clarity=5
        #arch-eval:state_invariants=5
        #arch-eval:entity_fullness=3
        #arch-eval:locational_stability=5
    """
    if name in {"given", "not_implemented", "step", "then", "tolerant", "when"}:
        from pytest_bdd.steps import (
            given,
            not_implemented,
            step,
            then,
            tolerant,
            when,
        )

        return {
            "given": given,
            "not_implemented": not_implemented,
            "step": step,
            "then": then,
            "tolerant": tolerant,
            "when": when,
        }[name]
    if name == "PytestBDDStepDefinitionWarning":
        from pytest_bdd.types.warning import PytestBDDStepDefinitionWarning

        return PytestBDDStepDefinitionWarning
    if name == "__version__":
        from pytest_bdd.util.packaging import get_distribution_version

        return str(get_distribution_version("pytest-bdd-ng"))
    msg = f"module {__name__!r} has no attribute {name!r}"
    raise AttributeError(msg)
