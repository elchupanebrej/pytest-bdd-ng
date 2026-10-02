from __future__ import annotations

import importlib.util

STRUCT_BDD_INSTALLED: bool = False

try:
    STRUCT_BDD_INSTALLED = importlib.util.find_spec("pytest_cuke.struct_bdd.parser") is not None
except (ImportError, AttributeError, ModuleNotFoundError):
    STRUCT_BDD_INSTALLED = False

__all__ = ["STRUCT_BDD_INSTALLED"]
