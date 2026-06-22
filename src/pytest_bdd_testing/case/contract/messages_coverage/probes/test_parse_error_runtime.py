"""Provide test parse error runtime helpers."""

from __future__ import annotations

from pathlib import Path

from pytest_bdd import scenarios

test_scenarios = scenarios(Path(__file__).parents[4] / "resource" / "features" / "parse_error.feature")
