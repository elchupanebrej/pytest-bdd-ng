from __future__ import annotations

from pytest_bdd.compatibility.runtime_compat import (
    MIN_SUPPORTED_PYTEST,
    MIN_SUPPORTED_PYTHON,
    PYTEST_COMPATIBILITY_BOUNDS,
    REASON_COMPATIBLE,
    REASON_EOL_PYTHON,
    REASON_PYTEST_UNAVAILABLE,
    REASON_PYTHON_UNAVAILABLE,
    CompatibilityMatrixEntry,
    MigrationCoverageSummary,
    _format_pytest_version,
    _format_python_version,
    _parse_pytest_factor,
    _parse_python_factor,
    is_pair_compatible,
)


def test_matrix_bounds_and_constants() -> None:
    assert MIN_SUPPORTED_PYTHON == (3, 10)
    assert MIN_SUPPORTED_PYTEST == (7, 0, 0)
    assert "80" in PYTEST_COMPATIBILITY_BOUNDS


def test_matrix_entry_and_migration_summary() -> None:
    entry = CompatibilityMatrixEntry(
        python_version="3.10", pytest_version="8.0", is_compatible=True, is_supported=True, reason_code="compatible"
    )
    assert entry.is_compatible is True

    summary = MigrationCoverageSummary(
        total_user_facing_scenarios=10,
        user_facing_in_features=10,
        coverage_percent=100.0,
        threshold_percent=80,
        threshold_met=True,
        duplicates_in_tests=0,
    )
    assert summary.threshold_met is True


def test_parse_and_format_versions() -> None:
    assert _parse_python_factor("310") == (3, 10)
    assert _parse_python_factor("invalid") is None
    assert _format_python_version("310") == "3.10"
    assert _parse_pytest_factor("80") == (8, 0, 0)
    assert _parse_pytest_factor("latest") == (99, 0, 0)
    assert _parse_pytest_factor("invalid") is None
    assert _format_pytest_version("latest") == "latest"


def test_is_pair_compatible() -> None:
    assert is_pair_compatible("310", "80") == (True, REASON_COMPATIBLE)
    assert is_pair_compatible("39", "80") == (False, REASON_EOL_PYTHON)
    assert is_pair_compatible("invalid", "80") == (False, REASON_PYTHON_UNAVAILABLE)
    assert is_pair_compatible("310", "unknown") == (False, REASON_PYTEST_UNAVAILABLE)
