"""
Runtime compatibility rules for Python/pytest version pairs.

Responsibility:
    Runtime compatibility rules for Python/pytest version pairs. It directly owns the observable contract, local
    decisions, and maintenance boundary for this module.

Reason for existence:
    This entity is the information expert for `pytest_bdd.compatibility.runtime_compat` because it keeps the nearest
    code, data shape, call signature, and failure knowledge together.

Delegates:
    - CompatibilityMatrixEntry: owns nested behavior below this boundary
    - MigrationCoverageSummary: owns nested behavior below this boundary
    - _parse_python_factor: owns nested behavior below this boundary
    - _format_python_version: owns nested behavior below this boundary
    - _format_pytest_version: owns nested behavior below this boundary
    - _parse_pytest_factor: owns nested behavior below this boundary

Cohesion:
    The implementation stays together because its imports, calls, state writes, and return contract describe one
    maintainable decision unit.

Separation:
    - module peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
      widening caller knowledge.

Main consumers:
    - src/pytest_bdd/script/compatibility_matrix.py: imports or references `runtime_compat`
    - src/pytest_bdd/util/matrix.py: imports or references `runtime_compat`

State and side effects:
    mutates pytest_version, PYTEST_COMPATIBILITY_BOUNDS, MIN_SUPPORTED_PYTHON, MIN_SUPPORTED_PYTEST, REASON_COMPATIBLE;
    depends on __future__.annotations, attrs.frozen, returns.maybe.Nothing.

Invariants:
    - `pytest_bdd.compatibility.runtime_compat` keeps its documented import path, ownership boundary, and observable
      behavior stable for callers.

Architecture score:
    #arch-eval:reason_for_existence=4
    #arch-eval:owned_responsibility=4
    #arch-eval:delegation_boundary=4
    #arch-eval:cohesion=3
    #arch-eval:separation=3
    #arch-eval:consumer_clarity=4
    #arch-eval:state_invariants=4
    #arch-eval:entity_fullness=4
    #arch-eval:locational_stability=3
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
    Represent compatibility matrix entry state.

    Responsibility:
        Represent compatibility matrix entry state. It directly owns the observable contract, local decisions, and
        maintenance boundary for this class.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.compatibility.runtime_compat.CompatibilityMatrixEntry`
        because it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - None, leaf-level implementation boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/script/compatibility_matrix.py: imports or references `CompatibilityMatrixEntry`
        - src/pytest_bdd/util/matrix.py: imports or references `CompatibilityMatrixEntry`

    State and side effects:
        mutates python_version, pytest_version, is_compatible, is_supported, reason_code.

    Invariants:
        - `pytest_bdd.compatibility.runtime_compat.CompatibilityMatrixEntry` keeps its documented import path, ownership
          boundary, and observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=2
        #arch-eval:cohesion=3
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=2
        #arch-eval:locational_stability=3
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
    Represent migration coverage summary state.

    Responsibility:
        Represent migration coverage summary state. It directly owns the observable contract, local decisions, and
        maintenance boundary for this class.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.compatibility.runtime_compat.MigrationCoverageSummary`
        because it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - None, leaf-level implementation boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/script/compatibility_matrix.py: imports or references `MigrationCoverageSummary`
        - src/pytest_bdd/util/matrix.py: imports or references `MigrationCoverageSummary`

    State and side effects:
        mutates total_user_facing_scenarios, user_facing_in_features, coverage_percent, threshold_percent,
        threshold_met.

    Invariants:
        - `pytest_bdd.compatibility.runtime_compat.MigrationCoverageSummary` keeps its documented import path, ownership
          boundary, and observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=2
        #arch-eval:cohesion=3
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=2
        #arch-eval:locational_stability=3
    """

    total_user_facing_scenarios: int
    user_facing_in_features: int
    coverage_percent: float
    threshold_percent: int
    threshold_met: bool
    duplicates_in_tests: int


def _parse_python_factor(python_factor: str) -> tuple[int, int] | None:
    """
    Parse a Python factor string into a version tuple.

    Args:
        python_factor: Python factor string (e.g., "310", "312").

    Returns:
        Tuple of (major, minor) version or None if invalid.

    Responsibility:
        Parse a Python factor string into a version tuple. It directly owns the observable contract, local decisions,
        and maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.compatibility.runtime_compat._parse_python_factor` because
        it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - int: collaborator call used by this boundary
        - Nothing.value_or: collaborator call used by this boundary
        - len: collaborator call used by this boundary
        - python_factor.isdigit: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/script/compatibility_matrix.py: imports or references `_parse_python_factor`
        - src/pytest_bdd/util/matrix.py: imports or references `_parse_python_factor`

    State and side effects:
        keeps no local persistent state beyond call-local values.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=3

    """
    if not python_factor.isdigit():
        return Nothing.value_or(None)
    if len(python_factor) == 2:  # noqa: PLR2004
        return (3, int(python_factor[1]))
    if len(python_factor) == 3:  # noqa: PLR2004
        return (int(python_factor[0]), int(python_factor[1:]))
    return Nothing.value_or(None)


def _format_python_version(python_factor: str) -> str:
    """
    Format Python factor as version string.

    Args:
        python_factor: Python factor string.

    Returns:
        Formatted version string.

    Responsibility:
        Format Python factor as version string. It directly owns the observable contract, local decisions, and
        maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.compatibility.runtime_compat._format_python_version`
        because it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - _parse_python_factor: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/script/compatibility_matrix.py: imports or references `_format_python_version`
        - src/pytest_bdd/util/matrix.py: imports or references `_format_python_version`

    State and side effects:
        mutates parsed.

    Invariants:
        - `pytest_bdd.compatibility.runtime_compat._format_python_version` keeps its documented import path, ownership
          boundary, and observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=3

    """
    parsed = _parse_python_factor(python_factor)
    return f"{parsed[0]}.{parsed[1]}" if parsed else python_factor


def _format_pytest_version(pytest_factor: str) -> str:
    """
    Format pytest factor as version string.

    Args:
        pytest_factor: Pytest factor string.

    Returns:
        Formatted version string.

    Responsibility:
        Format pytest factor as version string. It directly owns the observable contract, local decisions, and
        maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.compatibility.runtime_compat._format_pytest_version`
        because it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - len: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/script/compatibility_matrix.py: imports or references `_format_pytest_version`
        - src/pytest_bdd/util/matrix.py: imports or references `_format_pytest_version`

    State and side effects:
        keeps no local persistent state beyond call-local values.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=3

    """
    if pytest_factor == "latest":
        return "latest"
    if len(pytest_factor) == 2:  # noqa: PLR2004
        return f"{pytest_factor[0]}.{pytest_factor[1]}"
    if len(pytest_factor) == 3:  # noqa: PLR2004
        return f"{pytest_factor[0]}.{pytest_factor[1]}.{pytest_factor[2]}"
    return pytest_factor


def _parse_pytest_factor(pytest_factor: str) -> tuple[int, int, int] | None:
    """
    Parse a pytest factor string into a version tuple.

    Args:
        pytest_factor: Pytest factor string (e.g., "80", "latest").

    Returns:
        Tuple of (major, minor, patch) version or None if invalid.

    Responsibility:
        Parse a pytest factor string into a version tuple. It directly owns the observable contract, local decisions,
        and maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.compatibility.runtime_compat._parse_pytest_factor` because
        it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - int: collaborator call used by this boundary
        - Nothing.value_or: collaborator call used by this boundary
        - len: collaborator call used by this boundary
        - pytest_factor.isdigit: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/script/compatibility_matrix.py: imports or references `_parse_pytest_factor`
        - src/pytest_bdd/util/matrix.py: imports or references `_parse_pytest_factor`

    State and side effects:
        keeps no local persistent state beyond call-local values.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=3

    """
    if pytest_factor == "latest":
        # Keep "latest" above current known floor.
        return (99, 0, 0)
    if not pytest_factor.isdigit():
        return Nothing.value_or(None)
    if len(pytest_factor) == 2:  # noqa: PLR2004
        return (int(pytest_factor[0]), int(pytest_factor[1]), 0)
    if len(pytest_factor) == 3:  # noqa: PLR2004
        return (int(pytest_factor[0]), int(pytest_factor[1]), int(pytest_factor[2]))
    return Nothing.value_or(None)


def is_pair_compatible(python_factor: str, pytest_factor: str) -> tuple[bool, str]:  # noqa: PLR0911
    """
    Check if a Python/pytest version pair is compatible.

    Args:
        python_factor: Python version factor.
        pytest_factor: Pytest version factor.

    Returns:
        Tuple of (is_compatible, reason_code).

    Responsibility:
        Check if a Python/pytest version pair is compatible. It directly owns the observable contract, local decisions,
        and maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.compatibility.runtime_compat.is_pair_compatible` because
        it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - _parse_python_factor: collaborator call used by this boundary
        - _parse_pytest_factor: collaborator call used by this boundary
        - PYTEST_COMPATIBILITY_BOUNDS.get: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/script/compatibility_matrix.py: imports or references `is_pair_compatible`
        - src/pytest_bdd/util/matrix.py: imports or references `is_pair_compatible`

    State and side effects:
        mutates py, pytest_version, bounds, min_version, max_version.

    Invariants:
        - `pytest_bdd.compatibility.runtime_compat.is_pair_compatible` keeps its documented import path, ownership
          boundary, and observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
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
