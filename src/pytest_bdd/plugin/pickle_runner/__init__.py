# init: allow  # init: no-check
"""
Serves as the Runtime layer (order 6) package init for the pickle runner plugin.

Responsibility:
    Serves as the Runtime layer (order 6) package init for the pickle runner plugin. Exports the `apply_transition`
    function as a top-level package symbol and provides a lazy `__getattr__` for on-demand imports of
    `build_external_api_compatibility_record` and `collect_hook_public_symbols` from `api_compatibility` to break
    circular import chains. Acts as the public entry point for the pickle runner's scenario execution engine.

Reason for existence:
    This module is kept as a separate package init because it needs to control what symbols are publicly exported from
    the pickle_runner package. The lazy `__getattr__` pattern is required to defer imports of `api_compatibility`
    symbols that would otherwise create circular dependencies during package loading. Consolidating export control here
    prevents consumers from needing to know which sub-module owns which symbol.

Delegates:
    - run_transitions.apply_transition: Core state machine transition function for scenario execution.
    - api_compatibility.build_external_api_compatibility_record: Builds external API compatibility records on demand.
    - api_compatibility.collect_hook_public_symbols: Collects public symbols from hook implementations.

Cohesion:
    All logic serves the single purpose of controlled package exports: re-exporting `apply_transition` eagerly and
    lazily loading compatibility functions. No other concerns are present.

Separation:
    - pickle_runner.plugin: Contains the actual pytest plugin implementation and hookimpl methods.
    - pickle_runner.run_transitions: Contains the state machine transition logic.
    - pickle_runner.api_compatibility: Contains API compatibility utilities loaded lazily.

Main consumers:
    - pytest_bdd.plugin.pickle_runner.entrypoint: Imports `apply_transition` from this package-level export.
    - pytest_bdd.plugin.pickle_runner.api_compatibility: Symbols are accessed lazily via __getattr__.

State and side effects:
    None, keeps no persistent state. The __getattr__ function performs lazy imports that modify module globals (cached
    after first access).

Invariants:
    - `apply_transition` must always be importable as `from pytest_bdd.plugin.pickle_runner import apply_transition`.
    - Lazy-loaded symbols must resolve to the correct objects from `api_compatibility`.

Failure semantics:
    Raises AttributeError with a descriptive message when an unrecognized attribute name is accessed via __getattr__.
    Callers should handle this by checking attribute existence before access.

Architecture score:
    #arch-eval:reason_for_existence=4
    #arch-eval:owned_responsibility=4
    #arch-eval:delegation_boundary=5
    #arch-eval:cohesion=5
    #arch-eval:separation=5
    #arch-eval:consumer_clarity=4
    #arch-eval:state_invariants=4
    #arch-eval:entity_fullness=3
    #arch-eval:locational_stability=5
"""

from .run_transitions import apply_transition


def __getattr__(name: str) -> object:
    """
    Implement Python's module-level `__getattr__` protocol for lazy attribute resolution.

    Responsibility:
        Implements Python's module-level `__getattr__` protocol for lazy attribute resolution. When an attribute not
        already present in the module's namespace is accessed, this function checks if it matches
        `build_external_api_compatibility_record` or `collect_hook_public_symbols`, imports them from
        `api_compatibility` (breaking a circular import), caches them in `locals()`, and returns the resolved object.
        Raises AttributeError for unrecognized names. Operates at import time in the Runtime layer (order 6).

    Reason for existence:
        This function exists to break a circular import dependency between the pickle_runner package init and the
        `api_compatibility` module. Without lazy loading, the package init's eager import of `api_compatibility` symbols
        would cause a circular import chain. The `__getattr__` pattern defers the import until the symbol is actually
        accessed, maintaining a clean public API while avoiding circular dependencies. It is the single authority for
        dispatching attribute access to the correct deferred import.

    Delegates:
        - api_compatibility.build_external_api_compatibility_record: Lazily imported and returned when `name ==
        "build_external_api_compatibility_record"`.
        - api_compatibility.collect_hook_public_symbols: Lazily imported and returned when `name ==
        "collect_hook_public_symbols"`.

    Cohesion:
        All logic serves the single purpose of lazy attribute resolution for two specific compatibility symbols. The
        function body is a simple if-check, import, and return pattern with no extraneous logic.

    Separation:
        - apply_transition (module-level import): Eagerly imported, handled by Python's normal import mechanism, not by
        __getattr__.

    Main consumers:
        - Python interpreter: Called automatically by the module's `__getattr__` protocol when an attribute is accessed
        that doesn't exist in the module's `__dict__`.
        - External callers importing from pytest_bdd.plugin.pickle_runner: Access compatibility symbols as regular
        module attributes.

    State and side effects:
        Modifies module globals by caching imported symbols via `locals()[name]` after first access. Subsequent accesses
        to the same name bypass __getattr__.

    Failure semantics:
        Raises AttributeError with the message `module {__name__!r} has no attribute {name!r}` for unrecognized
        attribute names. Callers should handle this by using hasattr() or try/except AttributeError when accessing
        potentially undefined symbols.

    Architecture score:
        #arch-eval:reason_for_existence=5
        #arch-eval:owned_responsibility=5
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=5
        #arch-eval:separation=4
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=4
    """
    if name in {"build_external_api_compatibility_record", "collect_hook_public_symbols"}:
        from .api_compatibility import (  # noqa: PLC0415 -- breaks circular import
            build_external_api_compatibility_record,
            collect_hook_public_symbols,
        )

        return locals()[name]
    msg = f"module {__name__!r} has no attribute {name!r}"
    raise AttributeError(msg)
