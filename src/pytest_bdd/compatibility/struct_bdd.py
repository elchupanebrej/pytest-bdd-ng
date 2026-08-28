from __future__ import annotations

import importlib.util

STRUCT_BDD_INSTALLED: bool = False

try:
    STRUCT_BDD_INSTALLED = (
        importlib.util.find_spec("pytest_bdd.plugin.struct_bdd.parser") is not None
        or importlib.util.find_spec("pytest_bdd.struct_bdd.parser") is not None
    )
except (ImportError, AttributeError):
    STRUCT_BDD_INSTALLED = False

__all__ = ["STRUCT_BDD_INSTALLED"]
