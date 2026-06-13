# init: allow  # init: no-check
"""
Provides focused utility functions for the `cucumber_formatter_support` concern within pytest-
bdd utility layer, off.

Responsibility:
    Provides focused utility functions for the `cucumber_formatter_support` concern within pytest-
    bdd utility layer, offering helper operations consumed by higher layers (collection, runtime,
    reporting) without pulling in pytest plugin machinery or creating import cycles.

Reason for existence:
    Keeping `cucumber_formatter_support` utilities in a dedicated module prevents cross-cutting
    helper code from accumulating in larger modules where it would create unclear ownership or
    hidden dependency issues. This module is the single authority for
    `cucumber_formatter_support`-related helper operations within the utility layer.

Delegates:
    - Python standard library: delegates core data structure and I/O operations to stdlib

Cohesion:
    All functions and classes serve the single `cucumber_formatter_support` utility concern.

Separation:
    - Sibling utility modules: each handles a distinct helper concern to prevent callers from coupling to unrelated
    functionality.

Main consumers:
    - `pytest_bdd.plugin.*`: imports `cucumber_formatter_support` utilities for reporting, collection, and runtime
    operations

State and side effects:
    None, this module keeps no persistent state and performs no file or network I/O.

Invariants:
    - The public API surface (exported names) remains stable across internal refactors.

Architecture score:
    #arch-eval:reason_for_existence=4
    #arch-eval:owned_responsibility=4
    #arch-eval:delegation_boundary=4
    #arch-eval:cohesion=5
    #arch-eval:separation=4
    #arch-eval:consumer_clarity=4
    #arch-eval:state_invariants=4
    #arch-eval:entity_fullness=2
    #arch-eval:locational_stability=4
"""

from pytest_bdd.util.cucumber_formatter_support.base import (
    FormatterReporterPlugin,
    load_formatter_adapter_support_template,
    load_formatter_adapter_template,
)
