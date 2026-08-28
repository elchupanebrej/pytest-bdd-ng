from __future__ import annotations

from functools import lru_cache
from importlib.metadata import version
from operator import eq
from typing import TYPE_CHECKING, Any

from packaging.version import Version

if TYPE_CHECKING:
    from collections.abc import Callable


def get_distribution_version(distribution_name: str) -> Version:
    return Version(version(distribution_name))


def parse_version(version_str: str) -> Version:
    return Version(version_str)


@lru_cache
def compare_distribution_version(
    distribution_name: str,
    version_str: str,
    operator: Callable[[Any, Any], bool] = eq,
) -> bool:
    return operator(get_distribution_version(distribution_name), parse_version(version_str))
