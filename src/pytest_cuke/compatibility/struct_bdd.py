from __future__ import annotations

import importlib.util

STRUCT_BDD_INSTALLED: bool = False

try:
    STRUCT_BDD_INSTALLED = all(
        importlib.util.find_spec(module_name) is not None
        for module_name in (
            "pydantic",
            "yaml",
            "json5",
            "hjson",
            "pyhocon",
            "pytest_cuke.struct_bdd.parser",
        )
    )
except (ImportError, AttributeError, ModuleNotFoundError, ValueError):
    STRUCT_BDD_INSTALLED = False

__all__ = ["STRUCT_BDD_INSTALLED"]
