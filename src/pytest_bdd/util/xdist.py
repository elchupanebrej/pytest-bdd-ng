"""Provide xdist-related utilities."""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pytest_bdd.compatibility.pytest import Config


def is_xdist_worker(config: Config) -> bool:
    """
    Return True if running in an xdist worker process.

    Args:
        config: Pytest config object.

    Returns:
        True if config has workerinput attribute (xdist worker), False otherwise (controller or no xdist).

    """
    return hasattr(config, "workerinput") or os.environ.get("PYTEST_BDD_XDIST_IS_WORKER") == "1"
