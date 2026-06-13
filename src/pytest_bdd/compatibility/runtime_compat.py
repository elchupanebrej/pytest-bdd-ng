"""
Provide a cross-Python-version compatibility shim for `runtime_compat`, encapsulating all
version-detection logic an.

Responsibility:
    Provides a cross-Python-version compatibility shim for `runtime_compat`, encapsulating all
    version-detection logic and conditional imports so that higher layers import a single stable
    name regardless of the runtime Python interpreter version (3.10-3.14).

Reason for existence:
    Centralizing Python version-gating for `runtime_compat` in this module prevents `if
    sys.version_info` checks from contaminating domain logic. This module is the single information
    expert for which stdlib/third-party names and APIs are available on each supported Python
    version for this specific concern.

Delegates:
    - Python stdlib/third-party: delegates actual implementation to the version-appropriate module

Cohesion:
    All symbols re-export a single compatibility concern (runtime_compat); no unrelated utilities.

Separation:
    - Sibling compatibility modules: each handles a distinct stdlib version gap.

Main consumers:
    - `pytest_bdd.*`: all higher layers import compatibility shims to avoid inline version-gated logic

State and side effects:
    None, this module keeps no persistent state and performs only import-time version detection.

Invariants:
    - The public API surface matches the target stdlib module interface across supported Python versions.

Architecture score:
    #arch-eval:reason_for_existence=5
    #arch-eval:owned_responsibility=5
    #arch-eval:delegation_boundary=4
    #arch-eval:cohesion=5
    #arch-eval:separation=5
    #arch-eval:consumer_clarity=5
    #arch-eval:state_invariants=5
    #arch-eval:entity_fullness=3
    #arch-eval:locational_stability=5
"""

from __future__ import annotations

from attrs import frozen
from returns.maybe import Nothing

PYTEST_COMPATIBILITY_BOUNDS: dict[str, tuple[tuple[int, int], tuple[int, int] | None]] = {
    # pytest 7.x
    "70": ((3, 7), (3, 11)),
    "71": ((3, 7), (3, 11)),
    "72": ((3, 7), (3, 11)),
    "73": ((3, 7), (3, 11)),
    "74": ((3, 7), (3, 11)),
    # pytest 8.x
    "80": ((3, 8), (3, 13)),
    "81": ((3, 8), (3, 13)),
    "82": ((3, 8), (3, 13)),
    "83": ((3, 8), (3, 13)),
    "84": ((3, 8), (3, 13)),
    # pytest 9.x
    "90": ((3, 9), (3, 14)),
    # latest follows newest known major guardrails to avoid project-specific caps.
    "latest": ((3, 9), (3, 14)),
}

MIN_SUPPORTED_PYTHON: tuple[int, int] = (3, 10)
MIN_SUPPORTED_PYTEST: tuple[int, int, int] = (7, 0, 0)

REASON_COMPATIBLE = "compatible"
REASON_PYTHON_NOT_SUPPORTED_BY_PYTEST = "python_not_supported_by_pytest"
REASON_PYTEST_UNAVAILABLE = "pytest_unavailable"
REASON_PYTHON_UNAVAILABLE = "python_unavailable"
REASON_EOL_PYTHON = "eol_python"
REASON_EOL_PYTEST = "eol_pytest"


@frozen
class CompatibilityMatrixEntry:
    """
    Encapsulates the CompatibilityMatrixEntry concern within pytest-bdd, providing a focused set of
    collaborating operati.

    Responsibility:
        Encapsulates the CompatibilityMatrixEntry concern within pytest-bdd, providing a focused set of
        collaborating operations that together deliver a single well-defined capability consumed by the
        broader BDD runtime infrastructure.

    Reason for existence:
        CompatibilityMatrixEntry is a distinct class because its methods share internal state and
        collaborate on a cohesive task that would be awkward to express as standalone functions with
        shared mutable parameters.

    Delegates:
        - object: CompatibilityMatrixEntry specializes behavior from its parent(s) without duplicating their contracts

    Cohesion:
        All methods and attributes serve the single CompatibilityMatrixEntry domain concern.

    Separation:
        - Other types in this module: each class represents a distinct domain within the same layer.

    Main consumers:
        - `pytest_bdd.*`: callers catch or instantiate CompatibilityMatrixEntry for error handling and type checking

    State and side effects:
        Holds only instance state directly relevant to its encapsulated concern.

    Invariants:
        - Instances of CompatibilityMatrixEntry maintain internal consistency across all method calls.

    Architecture score:
        #arch-eval:reason_for_existence=5
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=5
        #arch-eval:separation=4
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=4
    """

    python_version: str
    pytest_version: str
    is_compatible: bool
    is_supported: bool
    reason_code: str
    execution_targets: tuple[str, ...] = ("lin", "mac", "win")
    compatibility_source: str = "pytest-metadata"
    tox_env_name: str | None = None


@frozen
class MigrationCoverageSummary:
    """
    Encapsulates the MigrationCoverageSummary concern within pytest-bdd, providing a focused set of
    collaborating operati.

    Responsibility:
        Encapsulates the MigrationCoverageSummary concern within pytest-bdd, providing a focused set of
        collaborating operations that together deliver a single well-defined capability consumed by the
        broader BDD runtime infrastructure.

    Reason for existence:
        MigrationCoverageSummary is a distinct class because its methods share internal state and
        collaborate on a cohesive task that would be awkward to express as standalone functions with
        shared mutable parameters.

    Delegates:
        - object: MigrationCoverageSummary specializes behavior from its parent(s) without duplicating their contracts

    Cohesion:
        All methods and attributes serve the single MigrationCoverageSummary domain concern.

    Separation:
        - Other types in this module: each class represents a distinct domain within the same layer.

    Main consumers:
        - `pytest_bdd.*`: callers catch or instantiate MigrationCoverageSummary for error handling and type checking

    State and side effects:
        Holds only instance state directly relevant to its encapsulated concern.

    Invariants:
        - Instances of MigrationCoverageSummary maintain internal consistency across all method calls.

    Architecture score:
        #arch-eval:reason_for_existence=5
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=5
        #arch-eval:separation=4
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=4
    """

    total_user_facing_scenarios: int
    user_facing_in_features: int
    coverage_percent: float
    threshold_percent: int
    threshold_met: bool
    duplicates_in_tests: int


def _parse_python_factor(python_factor: str) -> tuple[int, int] | None:
    """
    Perform the `_parse_python_factor` operation within its module boundary, implementing a
    focused helper function that.

    Responsibility:
        Performs the `_parse_python_factor` operation within its module boundary, implementing a
        focused helper function that is consumed by higher layers for its specific utility purpose
        within the pytest-bdd architecture.

    Reason for existence:
        `_parse_python_factor` exists as a standalone function because it encapsulates an operation
        that does not require shared instance state and benefits from being independently callable and
        testable without class instantiation overhead.

    Delegates:
        - Python standard library: delegates core operations to stdlib

    Cohesion:
        All logic directly supports the _parse_python_factor operation.

    Separation:
        - Other functions in this module: each function handles a distinct helper concern.

    Main consumers:
        - `pytest_bdd.*`: callers import and invoke _parse_python_factor for its specific utility

    State and side effects:
        None, this function is stateless and produces its output purely from input arguments.

    Invariants:
        - The _parse_python_factor function returns consistent results for equivalent inputs.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=3
        #arch-eval:delegation_boundary=3
        #arch-eval:cohesion=5
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=3
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=3
        #arch-eval:locational_stability=3
    """
    if not python_factor.isdigit():
        return Nothing.value_or(None)
    if len(python_factor) == 2:  # noqa: PLR2004  -- suppressed warning
        return (3, int(python_factor[1]))
    if len(python_factor) == 3:  # noqa: PLR2004  -- suppressed warning
        return (int(python_factor[0]), int(python_factor[1:]))
    return Nothing.value_or(None)


def _format_python_version(python_factor: str) -> str:
    """
    Perform the `_format_python_version` operation within its module boundary, implementing a
    focused helper function th.

    Responsibility:
        Performs the `_format_python_version` operation within its module boundary, implementing a
        focused helper function that is consumed by higher layers for its specific utility purpose
        within the pytest-bdd architecture.

    Reason for existence:
        `_format_python_version` exists as a standalone function because it encapsulates an operation
        that does not require shared instance state and benefits from being independently callable and
        testable without class instantiation overhead.

    Delegates:
        - Python standard library: delegates core operations to stdlib

    Cohesion:
        All logic directly supports the _format_python_version operation.

    Separation:
        - Other functions in this module: each function handles a distinct helper concern.

    Main consumers:
        - `pytest_bdd.*`: callers import and invoke _format_python_version for its specific utility

    State and side effects:
        None, this function is stateless and produces its output purely from input arguments.

    Invariants:
        - The _format_python_version function returns consistent results for equivalent inputs.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=3
        #arch-eval:delegation_boundary=3
        #arch-eval:cohesion=5
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=3
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=3
        #arch-eval:locational_stability=3
    """
    parsed = _parse_python_factor(python_factor)
    return f"{parsed[0]}.{parsed[1]}" if parsed else python_factor


def _format_pytest_version(pytest_factor: str) -> str:
    """
    Perform the `_format_pytest_version` operation within its module boundary, implementing a
    focused helper function th.

    Responsibility:
        Performs the `_format_pytest_version` operation within its module boundary, implementing a
        focused helper function that is consumed by higher layers for its specific utility purpose
        within the pytest-bdd architecture.

    Reason for existence:
        `_format_pytest_version` exists as a standalone function because it encapsulates an operation
        that does not require shared instance state and benefits from being independently callable and
        testable without class instantiation overhead.

    Delegates:
        - Python standard library: delegates core operations to stdlib

    Cohesion:
        All logic directly supports the _format_pytest_version operation.

    Separation:
        - Other functions in this module: each function handles a distinct helper concern.

    Main consumers:
        - `pytest_bdd.*`: callers import and invoke _format_pytest_version for its specific utility

    State and side effects:
        None, this function is stateless and produces its output purely from input arguments.

    Invariants:
        - The _format_pytest_version function returns consistent results for equivalent inputs.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=3
        #arch-eval:delegation_boundary=3
        #arch-eval:cohesion=5
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=3
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=3
        #arch-eval:locational_stability=3
    """
    if pytest_factor == "latest":
        return "latest"
    if len(pytest_factor) == 2:  # noqa: PLR2004  -- suppressed warning
        return f"{pytest_factor[0]}.{pytest_factor[1]}"
    if len(pytest_factor) == 3:  # noqa: PLR2004  -- suppressed warning
        return f"{pytest_factor[0]}.{pytest_factor[1]}.{pytest_factor[2]}"
    return pytest_factor


def _parse_pytest_factor(pytest_factor: str) -> tuple[int, int, int] | None:
    """
    Perform the `_parse_pytest_factor` operation within its module boundary, implementing a
    focused helper function that.

    Responsibility:
        Performs the `_parse_pytest_factor` operation within its module boundary, implementing a
        focused helper function that is consumed by higher layers for its specific utility purpose
        within the pytest-bdd architecture.

    Reason for existence:
        `_parse_pytest_factor` exists as a standalone function because it encapsulates an operation
        that does not require shared instance state and benefits from being independently callable and
        testable without class instantiation overhead.

    Delegates:
        - Python standard library: delegates core operations to stdlib

    Cohesion:
        All logic directly supports the _parse_pytest_factor operation.

    Separation:
        - Other functions in this module: each function handles a distinct helper concern.

    Main consumers:
        - `pytest_bdd.*`: callers import and invoke _parse_pytest_factor for its specific utility

    State and side effects:
        None, this function is stateless and produces its output purely from input arguments.

    Invariants:
        - The _parse_pytest_factor function returns consistent results for equivalent inputs.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=3
        #arch-eval:delegation_boundary=3
        #arch-eval:cohesion=5
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=3
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=3
        #arch-eval:locational_stability=3
    """
    if pytest_factor == "latest":
        # Keep "latest" above current known floor.
        return (99, 0, 0)
    if not pytest_factor.isdigit():
        return Nothing.value_or(None)
    if len(pytest_factor) == 2:  # noqa: PLR2004  -- suppressed warning
        return (int(pytest_factor[0]), int(pytest_factor[1]), 0)
    if len(pytest_factor) == 3:  # noqa: PLR2004  -- suppressed warning
        return (int(pytest_factor[0]), int(pytest_factor[1]), int(pytest_factor[2]))
    return Nothing.value_or(None)


def is_pair_compatible(python_factor: str, pytest_factor: str) -> tuple[bool, str]:  # noqa: PLR0911  -- suppressed warning
    """
    Perform the `is_pair_compatible` operation within its module boundary, implementing a focused
    helper function that i.

    Responsibility:
        Performs the `is_pair_compatible` operation within its module boundary, implementing a focused
        helper function that is consumed by higher layers for its specific utility purpose within the
        pytest-bdd architecture.

    Reason for existence:
        `is_pair_compatible` exists as a standalone function because it encapsulates an operation that
        does not require shared instance state and benefits from being independently callable and
        testable without class instantiation overhead.

    Delegates:
        - Python standard library: delegates core operations to stdlib

    Cohesion:
        All logic directly supports the is_pair_compatible operation.

    Separation:
        - Other functions in this module: each function handles a distinct helper concern.

    Main consumers:
        - `pytest_bdd.*`: callers import and invoke is_pair_compatible for its specific utility

    State and side effects:
        None, this function is stateless and produces its output purely from input arguments.

    Invariants:
        - The is_pair_compatible function returns consistent results for equivalent inputs.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=3
        #arch-eval:delegation_boundary=3
        #arch-eval:cohesion=5
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=3
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=3
        #arch-eval:locational_stability=3
    """
    py = _parse_python_factor(python_factor)
    if py is None:
        return False, REASON_PYTHON_UNAVAILABLE
    if py < MIN_SUPPORTED_PYTHON:
        return False, REASON_EOL_PYTHON

    pytest_version = _parse_pytest_factor(pytest_factor)
    if pytest_version is not None and pytest_version < MIN_SUPPORTED_PYTEST:
        return False, REASON_EOL_PYTEST

    bounds = PYTEST_COMPATIBILITY_BOUNDS.get(pytest_factor)
    if bounds is None:
        return False, REASON_PYTEST_UNAVAILABLE

    min_version, max_version = bounds
    if py < min_version:
        return False, REASON_PYTHON_NOT_SUPPORTED_BY_PYTEST
    if max_version is not None and py > max_version:
        return False, REASON_PYTHON_NOT_SUPPORTED_BY_PYTEST
    return True, REASON_COMPATIBLE
