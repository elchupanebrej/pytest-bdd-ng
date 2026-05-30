"""Runtime compatibility rules for Python/pytest version pairs."""

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
    """Represent compatibility matrix entry state."""

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
    """Represent migration coverage summary state."""

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
