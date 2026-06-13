"""
Serves as the Runtime layer (order 6) package init for the pickle runner's inner plugin sub-package.

Responsibility:
    Serves as the Runtime layer (order 6) package init for the pickle runner's inner plugin sub-package. Re-exports all
    public symbols from the `facade` module via `from .facade import *`, providing a clean public API surface for the
    internal plugin sub-package. Acts as a namespace boundary that separates plugin implementation details from the rest
    of the pickle runner package.

Reason for existence:
    This module exists solely to establish a Python sub-package boundary and re-export the facade module's public API.
    It is the information expert for which symbols from the `plugin` sub-package are considered public. Keeping it
    separate from the main pickle_runner init prevents symbol collision between the inner plugin sub-package and the
    outer package's own exports (apply_transition, compatibility functions).

Delegates:
    - facade: Contains the actual plugin hook implementations and public symbols that are re-exported through this init
    module.

Cohesion:
    All logic is a single import statement with no extraneous functionality. The module serves the pure purpose of
    package structure and namespace management.

Separation:
    - pickle_runner/__init__.py: Top-level package init exports apply_transition and lazy-loads compatibility functions
    — distinct from the plugin sub-package.
    - facade: Contains the actual implementation; kept separate from the init to allow clean re-export and avoid
    circular imports.

Main consumers:
    - pytest_bdd.plugin.pickle_runner.plugin._plugin: The actual plugin module imports through this sub-package boundary.
    - pytest_bdd.plugin.pickle_runner.plugin._executor: Accesses facade symbols through the sub-package namespace.

State and side effects:
    None, keeps no persistent state. Purely a namespace and re-export module.

Invariants:
    - All public symbols from `facade` must be accessible via `pytest_bdd.plugin.pickle_runner.plugin`.
    - The `from .facade import *` must not introduce duplicate symbols or shadowing issues.

Architecture score:
    #arch-eval:reason_for_existence=3
    #arch-eval:owned_responsibility=3
    #arch-eval:delegation_boundary=4
    #arch-eval:cohesion=4
    #arch-eval:separation=4
    #arch-eval:consumer_clarity=3
    #arch-eval:state_invariants=4
    #arch-eval:entity_fullness=2
    #arch-eval:locational_stability=5
"""
# init: no-check

from __future__ import annotations

from .facade import *  # noqa: F403  -- intentional re-export or import for public API facade
