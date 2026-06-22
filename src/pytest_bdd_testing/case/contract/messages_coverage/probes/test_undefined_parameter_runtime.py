"""Provide test undefined parameter runtime helpers."""

from __future__ import annotations

from pathlib import Path

from pytest_bdd import given, parsers, scenarios

test_scenarios = scenarios(Path(__file__).parents[4] / "resource" / "features" / "undefined_parameter.feature")


@given(parsers.cucumber_expression("value is {unknownParameter}"))
def _value_is_unknown_parameter() -> None:
    return None
