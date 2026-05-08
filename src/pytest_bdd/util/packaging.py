"""Provide packaging helpers."""

from __future__ import annotations

from functools import lru_cache
from operator import eq
from typing import TYPE_CHECKING

from packaging.utils import Version

if TYPE_CHECKING:
    from collections.abc import Callable

from pytest_bdd.compatibility.importlib.metadata import version


def get_distribution_version(distribution_name: str) -> Version:
    """Return distribution version."""
    return Version(version(distribution_name))


def parse_version(version: str) -> Version:
    """Parse version."""
    return Version(version)


@lru_cache
def compare_distribution_version(
    distribution_name: str,
    version: str,
    operator: Callable[[Version, Version], bool] = eq,
) -> bool:
    """Handle compare distribution version."""
    return operator(get_distribution_version(distribution_name), parse_version(version))
