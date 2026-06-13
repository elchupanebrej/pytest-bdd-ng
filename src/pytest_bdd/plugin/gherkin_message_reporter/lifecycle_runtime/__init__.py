"""
Serves as the Reporting layer (order 7) package init for the gherkin message reporter's lifecycle runtime sub-package.

Responsibility:
    Serves as the Reporting layer (order 7) package init for the gherkin message reporter's lifecycle runtime sub-
    package. Re-exports all public symbols from the `facade` module via `from .facade import *`, providing the public
    API for lifecycle event handling within the live NDJSON reporting system. Encapsulates CI detection, hook
    management, and core lifecycle orchestration behind a clean facade.

Reason for existence:
    This module exists to establish a sub-package boundary and re-export the facade module's public API. The lifecycle
    runtime has internal complexity across `_core`, `_hooks`, and `_ci` modules. The facade pattern ensures consumers
    only depend on the curated public interface without coupling to internal implementation details.

Delegates:
    - facade: Aggregates and re-exports public lifecycle symbols from `_core`, `_hooks`, and `_ci`.

Cohesion:
    All logic is a single facade re-export import statement. The module serves the pure purpose of package structure and
    controlled namespace exposure.

Separation:
    - _core: Internal implementation of lifecycle core orchestration — private implementation detail.
    - _hooks: Internal hook management logic — private implementation detail.
    - _ci: Internal CI environment detection — private implementation detail.

Main consumers:
    - pytest_bdd.plugin.gherkin_message_reporter.plugin: Consumes lifecycle runtime types through this package boundary
    for session lifecycle management.

State and side effects:
    None, keeps no persistent state. Purely a namespace and re-export module.

Invariants:
    - All public lifecycle runtime symbols must be accessible via the package namespace.
    - Internal modules must not be directly imported by external consumers.

Architecture score:
    #arch-eval:reason_for_existence=3
    #arch-eval:owned_responsibility=3
    #arch-eval:delegation_boundary=4
    #arch-eval:cohesion=2
    #arch-eval:separation=3
    #arch-eval:consumer_clarity=3
    #arch-eval:state_invariants=4
    #arch-eval:entity_fullness=2
    #arch-eval:locational_stability=5
"""
# init: no-check

from __future__ import annotations

from .facade import *  # noqa: F403  -- intentional re-export or import for public API facade
