"""
Serves as the Reporting layer (order 7) package init for the gherkin message reporter's step catalog runtime sub-pack.

Responsibility:
    Serves as the Reporting layer (order 7) package init for the gherkin message reporter's step catalog runtime sub-
    package. Re-exports all public symbols from the `facade` module via `from .facade import *`, providing a clean API
    surface for step catalog operations within the live NDJSON reporting system. Acts as the namespace boundary between
    the step catalog implementation details and the rest of the gherkin message reporter.

Reason for existence:
    This module exists solely to establish a sub-package boundary and re-export the facade module's public API. The
    facade pattern isolates implementation details in `_core` and `_static_helpers` while exposing only the curated
    public interface through the init. This prevents direct coupling to internal implementation modules.

Delegates:
    - facade: Aggregates and re-exports public step catalog symbols from `_core` and `_static_helpers`.

Cohesion:
    All logic is a single facade re-export import statement. The module serves the pure purpose of package structure and
    controlled namespace exposure.

Separation:
    - _core: Internal implementation of step catalog core logic — private implementation detail.
    - _static_helpers: Internal static helper utilities for step catalog — private implementation detail.

Main consumers:
    - pytest_bdd.plugin.gherkin_message_reporter.hook_catalog_runtime: Consumes step catalog types through this package
    boundary.
    - pytest_bdd.plugin.gherkin_message_reporter.ide_binding_runtime: Consumes step catalog types through this package
    boundary.

State and side effects:
    None, keeps no persistent state. Purely a namespace and re-export module.

Invariants:
    - All public step catalog symbols must be accessible via the package namespace.
    - Internal modules (`_core`, `_static_helpers`) must not be directly imported by external consumers.

Architecture score:
    #arch-eval:reason_for_existence=3
    #arch-eval:owned_responsibility=3
    #arch-eval:delegation_boundary=4
    #arch-eval:cohesion=3
    #arch-eval:separation=4
    #arch-eval:consumer_clarity=3
    #arch-eval:state_invariants=4
    #arch-eval:entity_fullness=2
    #arch-eval:locational_stability=5
"""
# init: no-check

from __future__ import annotations

from .facade import *  # noqa: F403  -- intentional re-export or import for public API facade
