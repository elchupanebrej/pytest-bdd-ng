"""Provide test failing step runtime helpers."""

from __future__ import annotations

from pathlib import Path

from pytest_bdd import given, scenarios, then, when

test_scenarios = scenarios(Path(__file__).parents[4] / "resource" / "features" / "failing_step.feature")


@given("a passing precondition")
def _passing_precondition() -> None:
    return None


@when("an exploding step executes")
def _exploding_step() -> None:
    msg = "probe explosion"
    raise RuntimeError(msg)


@then("this step is not reached")
def _not_reached() -> None:
    return None
