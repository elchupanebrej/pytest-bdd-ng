"""
Serves as the Extra Plugins layer (order 8) package init for the struct_bdd model sub-package.

Responsibility:
    Serves as the Extra Plugins layer (order 8) package init for the struct_bdd model sub-package. Re-exports all public
    symbols from the `facade` module via `from .facade import *`, providing a unified public API for the
    YAML/JSON/TOML/HOCON BDD model layer. Acts as the namespace boundary between struct_bdd's internal model
    implementation and its consumers.

Reason for existence:
    This module exists to establish a sub-package boundary and re-export the facade module's public API. The struct_bdd
    feature uses a facade pattern where `_base` and `_steps` provide internal implementation and `facade` aggregates the
    public interface. This init makes all public model symbols accessible from `pytest_bdd.plugin.struct_bdd.model`
    without exposing internal implementation modules.

Delegates:
    - facade: Aggregates and re-exports public model symbols from `_base` and `_steps` internal modules.

Cohesion:
    All logic is a single facade re-export. The module serves the pure purpose of package structure and controlled
    namespace exposure.

Separation:
    - _base: Internal implementation of base BDD model classes — kept private via underscore naming.
    - _steps: Internal implementation of step-related model classes — kept private via underscore naming.
    - struct_bdd.parser: Parser implementation consumes model types through this package boundary.

Main consumers:
    - pytest_bdd.plugin.struct_bdd.model_builder: Imports model types through this package init.
    - pytest_bdd.plugin.struct_bdd.parser: Imports model types through this package init.

State and side effects:
    None, keeps no persistent state. Purely a namespace and re-export module.

Invariants:
    - All public model symbols must be accessible via `pytest_bdd.plugin.struct_bdd.model`.
    - Internal modules (`_base`, `_steps`) must not be directly imported by external consumers.

Architecture score:
    #arch-eval:reason_for_existence=4
    #arch-eval:owned_responsibility=4
    #arch-eval:delegation_boundary=4
    #arch-eval:cohesion=5
    #arch-eval:separation=4
    #arch-eval:consumer_clarity=4
    #arch-eval:state_invariants=4
    #arch-eval:entity_fullness=4
    #arch-eval:locational_stability=5
"""
# init: no-check

from __future__ import annotations

from .facade import *  # noqa: F403  -- intentional re-export or import for public API facade
