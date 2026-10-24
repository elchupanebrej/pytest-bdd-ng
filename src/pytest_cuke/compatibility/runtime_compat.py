from __future__ import annotations

from attrs import frozen

PYTEST_COMPATIBILITY_BOUNDS: dict[str, tuple[tuple[int, int], tuple[int, int] | None]] = {
    # Upper bounds record the newest Python version with explicit support in
    # that pytest minor line. The project support floor is applied separately.
    "70": ((3, 6), (3, 10)),
    "71": ((3, 7), (3, 10)),
    "72": ((3, 7), (3, 11)),
    "73": ((3, 7), (3, 12)),
    "74": ((3, 7), (3, 12)),
    "80": ((3, 8), (3, 12)),
    "81": ((3, 8), (3, 12)),
    "82": ((3, 8), (3, 13)),
    "83": ((3, 8), (3, 13)),
    "84": ((3, 9), (3, 14)),
    "90": ((3, 10), (3, 14)),
    # pytest 9.0+ supports Python 3.10+ (docs.pytest.org/en/stable/backwards-compatibility.html).
    "9": ((3, 10), None),
    "latest": ((3, 10), None),
}

MIN_SUPPORTED_PYTHON: tuple[int, int] = (3, 11)
MIN_SUPPORTED_PYTEST: tuple[int, int, int] = (7, 0, 0)

REASON_COMPATIBLE = "compatible"
REASON_PYTHON_NOT_SUPPORTED_BY_PYTEST = "python_not_supported_by_pytest"
REASON_PYTEST_UNAVAILABLE = "pytest_unavailable"
REASON_PYTHON_UNAVAILABLE = "python_unavailable"
REASON_EOL_PYTHON = "eol_python"
REASON_EOL_PYTEST = "eol_pytest"


@frozen
class CompatibilityMatrixEntry:
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
    total_user_facing_scenarios: int
    user_facing_in_features: int
    coverage_percent: float
    threshold_percent: int
    threshold_met: bool
    duplicates_in_tests: int


def _parse_python_factor(python_factor: str) -> tuple[int, int] | None:
    if not python_factor.isdigit():
        return None
    if len(python_factor) == 2:
        return (3, int(python_factor[1]))
    if len(python_factor) == 3:
        return (int(python_factor[0]), int(python_factor[1:]))
    return None


def _format_python_version(python_factor: str) -> str:
    parsed = _parse_python_factor(python_factor)
    return f"{parsed[0]}.{parsed[1]}" if parsed else python_factor


def _format_pytest_version(pytest_factor: str) -> str:
    if pytest_factor == "latest":
        return "latest"
    if len(pytest_factor) == 2:
        return f"{pytest_factor[0]}.{pytest_factor[1]}"
    if len(pytest_factor) == 3:
        return f"{pytest_factor[0]}.{pytest_factor[1]}.{pytest_factor[2]}"
    return pytest_factor


def _parse_pytest_factor(pytest_factor: str) -> tuple[int, int, int] | None:
    if pytest_factor == "latest":
        return (99, 0, 0)
    if len(pytest_factor) == 1 and pytest_factor.isdigit():
        return (int(pytest_factor), 0, 0)
    if not pytest_factor.isdigit():
        return None
    if len(pytest_factor) == 2:
        return (int(pytest_factor[0]), int(pytest_factor[1]), 0)
    if len(pytest_factor) == 3:
        return (int(pytest_factor[0]), int(pytest_factor[1]), int(pytest_factor[2]))
    return None


def is_pair_compatible(python_factor: str, pytest_factor: str) -> tuple[bool, str]:
    py = _parse_python_factor(python_factor)
    if py is None:
        return False, REASON_PYTHON_UNAVAILABLE
    pytest_version = _parse_pytest_factor(pytest_factor)
    if pytest_version is not None and pytest_version < MIN_SUPPORTED_PYTEST:
        return False, REASON_EOL_PYTEST

    compatible = _is_python_version_supported_by_pytest(py, pytest_factor)
    if compatible is None:
        return False, REASON_PYTEST_UNAVAILABLE
    if py < MIN_SUPPORTED_PYTHON:
        return False, REASON_EOL_PYTHON
    if not compatible:
        return False, REASON_PYTHON_NOT_SUPPORTED_BY_PYTEST
    return True, REASON_COMPATIBLE


def _is_python_version_supported_by_pytest(python_version: tuple[int, int], pytest_factor: str) -> bool | None:
    """Return upstream Python support for a known pytest factor, or None if unknown."""
    bounds = PYTEST_COMPATIBILITY_BOUNDS.get(pytest_factor)
    if bounds is None:
        return None
    minimum_python, maximum_python = bounds
    return python_version >= minimum_python and (maximum_python is None or python_version <= maximum_python)


__all__ = [
    "MIN_SUPPORTED_PYTEST",
    "MIN_SUPPORTED_PYTHON",
    "PYTEST_COMPATIBILITY_BOUNDS",
    "REASON_COMPATIBLE",
    "REASON_EOL_PYTEST",
    "REASON_EOL_PYTHON",
    "REASON_PYTEST_UNAVAILABLE",
    "REASON_PYTHON_NOT_SUPPORTED_BY_PYTEST",
    "REASON_PYTHON_UNAVAILABLE",
    "CompatibilityMatrixEntry",
    "MigrationCoverageSummary",
    "_format_pytest_version",
    "_format_python_version",
    "_is_python_version_supported_by_pytest",
    "_parse_pytest_factor",
    "_parse_python_factor",
    "is_pair_compatible",
]
