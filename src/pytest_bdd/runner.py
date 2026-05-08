"""Runtime helpers for compatibility-oriented execution."""

from __future__ import annotations

from pytest_bdd.compatibility.matrix import is_pair_compatible


def validate_requested_pair(python_factor: str, pytest_factor: str) -> tuple[bool, str]:
    """
    Return compatibility status and a stable reason code for a requested pair.

    Args:
        python_factor: Python version factor string.
        pytest_factor: Pytest version factor string.

    Returns:
        Tuple of (is_compatible, reason_code).

    """
    return is_pair_compatible(python_factor, pytest_factor)
