from __future__ import annotations

from importlib.util import find_spec

# Runtime modules provided by the [struct-bdd] extra (see pyproject.toml).
STRUCT_BDD_REQUIRED_MODULES = ("hjson", "json5", "pyhocon", "yaml")

STRUCT_BDD_INSTALLED: bool = all(find_spec(module) is not None for module in STRUCT_BDD_REQUIRED_MODULES)

__all__ = ["STRUCT_BDD_INSTALLED"]
