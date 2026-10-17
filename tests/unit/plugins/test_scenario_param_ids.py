from __future__ import annotations

import pytest

from pytest_cuke.model import Feature, Scenario
from pytest_cuke.plugin import _build_scenario_param


@pytest.mark.parametrize(
    ("first_uri", "second_uri", "expected_source"),
    [
        (
            "file:../_remote-0-first/features/checkout.feature",
            "file:../_remote-1-second/features/checkout.feature",
            "file:../_remote/features/checkout.feature",
        ),
        (
            r"file:..\_remote-0-first\features\checkout.feature",
            r"file:..\_remote-1-second\features\checkout.feature",
            r"file:..\_remote\features\checkout.feature",
        ),
        (
            "file:../pytest-cuke-execnet-remote-0-first/features/checkout.feature",
            "file:../pytest-cuke-execnet-remote-1-second/features/checkout.feature",
            "file:../_remote/features/checkout.feature",
        ),
        (
            r"file:..\pytest-cuke-execnet-remote-0-first\features\pytest-cuke-execnet-remote-preserved\checkout.feature",
            r"file:..\pytest-cuke-execnet-remote-1-second\features\pytest-cuke-execnet-remote-preserved\checkout.feature",
            r"file:..\_remote\features\pytest-cuke-execnet-remote-preserved\checkout.feature",
        ),
    ],
)
def test_scenario_param_id_ignores_xdist_rsync_worker_root(
    first_uri: str,
    second_uri: str,
    expected_source: str,
) -> None:
    scenario = Scenario(name="checkout loads")
    first = _build_scenario_param(Feature(name="Checkout", uri=first_uri), scenario, config=None)
    second = _build_scenario_param(Feature(name="Checkout", uri=second_uri), scenario, config=None)

    assert first.id == second.id == f"{expected_source}-Checkout-checkout loads"
