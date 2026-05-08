"""Provide test remote aggregation helpers."""

from __future__ import annotations

from pathlib import Path

import pytest

from pytest_bdd import given, scenarios

pytestmark = [pytest.mark.xdist, pytest.mark.docker, pytest.mark.slow]

test_scenarios = scenarios(Path(__file__).with_name("aggregation.feature"))


@given("a passing step")
def _pass() -> str:
    return "ok"
