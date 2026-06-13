"""
Provides focused utility functions for the `facade` concern within pytest-bdd utility layer,
offering helper operatio.

Responsibility:
    Provides focused utility functions for the `facade` concern within pytest-bdd utility layer,
    offering helper operations consumed by higher layers (collection, runtime, reporting) without
    pulling in pytest plugin machinery or creating import cycles.

Reason for existence:
    Keeping `facade` utilities in a dedicated module prevents cross-cutting helper code from
    accumulating in larger modules where it would create unclear ownership or hidden dependency
    issues. This module is the single authority for `facade`-related helper operations within the
    utility layer.

Delegates:
    - Python standard library: delegates core data structure and I/O operations to stdlib

Cohesion:
    All functions and classes serve the single `facade` utility concern.

Separation:
    - Sibling utility modules: each handles a distinct helper concern to prevent callers from coupling to unrelated
    functionality.

Main consumers:
    - `pytest_bdd.plugin.*`: imports `facade` utilities for reporting, collection, and runtime operations

State and side effects:
    None, this module keeps no persistent state and performs no file or network I/O.

Invariants:
    - The public API surface (exported names) remains stable across internal refactors.

Architecture score:
    #arch-eval:reason_for_existence=5
    #arch-eval:owned_responsibility=4
    #arch-eval:delegation_boundary=4
    #arch-eval:cohesion=4
    #arch-eval:separation=4
    #arch-eval:consumer_clarity=4
    #arch-eval:state_invariants=4
    #arch-eval:entity_fullness=4
    #arch-eval:locational_stability=4
"""

from __future__ import annotations

from pytest_bdd.util.tests_group_ordering.barrier import (  # noqa: F401  -- intentional re-export or import for public API facade
    read_barrier_state,
    record_group_barrier_report,
    wait_for_group_barrier,
    write_barrier_state,
)
from pytest_bdd.util.tests_group_ordering.config import (  # noqa: F401  -- intentional re-export or import for public API facade
    GroupAssignment,
    GroupConfig,
    GroupPathMapping,
    ResolutionSource,
    RuntimeGroupBarrierObservation,
    read_group_config,
    register_group_config_options,
)
from pytest_bdd.util.tests_group_ordering.marker import (  # noqa: F401  -- intentional re-export or import for public API facade
    apply_group_marker,
    apply_group_ordering,
    apply_order_marker,
    resolve_group_assignment,
)
