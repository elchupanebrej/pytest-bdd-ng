"""Provide struct bdd helpers."""

import importlib.util

STRUCT_BDD_INSTALLED = importlib.util.find_spec("pytest_bdd.plugin.struct_bdd.parser") is not None
