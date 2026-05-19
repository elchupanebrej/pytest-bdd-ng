"""Provide test parse error runtime helpers."""

from __future__ import annotations

from pathlib import Path

from pytest_bdd import scenarios

test_scenarios = scenarios(Path(__file__).with_name("parse_error.feature"))
