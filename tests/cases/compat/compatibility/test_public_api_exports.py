"""Provide test public api exports helpers."""

from __future__ import annotations

import importlib
from types import ModuleType


def test_public_scenario_export_stays_callable_after_submodule_import() -> None:
    """Verify public scenario export stays callable after submodule import."""
    importlib.import_module("pytest_bdd.scenario")

    from pytest_bdd import scenario

    assert not isinstance(scenario, ModuleType)
    assert callable(scenario)
