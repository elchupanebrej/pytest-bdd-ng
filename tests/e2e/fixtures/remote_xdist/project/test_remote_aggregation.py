from __future__ import annotations

from pathlib import Path

from pytest_bdd import given, scenarios

test_scenarios = scenarios(Path(__file__).with_name("aggregation.feature"))


@given("a passing step")
def _pass() -> str:
    return "ok"
