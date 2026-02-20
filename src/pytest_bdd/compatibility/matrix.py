"""Compatibility matrix helpers for Python/pytest version selection."""

from __future__ import annotations

import re
from dataclasses import dataclass
from itertools import product
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterable
    from pathlib import Path

PYTEST_COMPATIBILITY_BOUNDS: dict[str, tuple[tuple[int, int], tuple[int, int] | None]] = {
    # pytest 6.x
    "60": ((3, 6), (3, 10)),
    "61": ((3, 6), (3, 10)),
    "62": ((3, 6), (3, 10)),
    "625": ((3, 6), (3, 10)),
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

REASON_COMPATIBLE = "compatible"
REASON_PYTHON_NOT_SUPPORTED_BY_PYTEST = "python_not_supported_by_pytest"
REASON_PYTEST_UNAVAILABLE = "pytest_unavailable"
REASON_PYTHON_UNAVAILABLE = "python_unavailable"


@dataclass(frozen=True)
class CompatibilityMatrixEntry:
    python_version: str
    pytest_version: str
    is_compatible: bool
    reason_code: str
    execution_targets: tuple[str, ...] = ("lin", "mac", "win")
    compatibility_source: str = "pytest-metadata"
    tox_env_name: str | None = None


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


def is_pair_compatible(python_factor: str, pytest_factor: str) -> tuple[bool, str]:
    py = _parse_python_factor(python_factor)
    if py is None:
        return False, REASON_PYTHON_UNAVAILABLE

    bounds = PYTEST_COMPATIBILITY_BOUNDS.get(pytest_factor)
    if bounds is None:
        return False, REASON_PYTEST_UNAVAILABLE

    min_version, max_version = bounds
    if py < min_version:
        return False, REASON_PYTHON_NOT_SUPPORTED_BY_PYTEST
    if max_version is not None and py > max_version:
        return False, REASON_PYTHON_NOT_SUPPORTED_BY_PYTEST
    return True, REASON_COMPATIBLE


def build_matrix(
    python_factors: Iterable[str],
    pytest_factors: Iterable[str],
    execution_targets: tuple[str, ...] = ("lin", "mac", "win"),
) -> list[CompatibilityMatrixEntry]:
    entries: list[CompatibilityMatrixEntry] = []
    for python_factor, pytest_factor in product(sorted(set(python_factors)), sorted(set(pytest_factors))):
        compatible, reason = is_pair_compatible(python_factor, pytest_factor)
        tox_env = None
        if compatible:
            tox_env = f"py{python_factor}-pytest{pytest_factor}-coverage-lin"
        entries.append(
            CompatibilityMatrixEntry(
                python_version=_format_python_version(python_factor),
                pytest_version=_format_pytest_version(pytest_factor),
                is_compatible=compatible,
                reason_code=reason,
                execution_targets=execution_targets,
                tox_env_name=tox_env,
            ),
        )
    return entries


def extract_factors_from_tox_ini(tox_ini_path: Path) -> tuple[list[str], list[str]]:
    text = tox_ini_path.read_text(encoding="utf-8")
    python_factors = sorted(set(re.findall(r"py(?:py)?(\d{2,3})", text)))
    pytest_factors = sorted(set(re.findall(r"pytest(latest|\d{2,3})", text)))
    return python_factors, pytest_factors


def expand_tox_env_names(entries: Iterable[CompatibilityMatrixEntry]) -> list[str]:
    return [entry.tox_env_name for entry in entries if entry.is_compatible and entry.tox_env_name]
