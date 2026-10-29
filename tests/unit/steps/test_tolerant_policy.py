from __future__ import annotations

from types import SimpleNamespace

import pytest

from pytest_cuke.model.scenario import Scenario
from pytest_cuke.model.tag import Tag
from pytest_cuke.steps.status_policy import (
    configured_tolerant_status,
    configured_wip_status,
    resolve_tolerant_status,
    resolve_wip_status,
)


class MarkerItem:
    def __init__(self, *markers: object) -> None:
        self.markers = markers

    def iter_markers(self, name: str | None = None):
        return iter(marker for marker in self.markers if name is None or marker.name == name)


def _config(
    cli: str | None = None,
    ini: str = "failed",
    wip_cli: str | None = None,
    wip_ini: str = "failed",
) -> SimpleNamespace:
    ini_values = {"cuke_tolerant_status": ini, "cuke_wip_status": wip_ini}
    return SimpleNamespace(
        option=SimpleNamespace(cuke_tolerant_status=cli, cuke_wip_status=wip_cli),
        getini=lambda name: ini_values[name],
    )


def _marker(name: str, *args: object) -> SimpleNamespace:
    return SimpleNamespace(name=name, args=args)


def test_cli_policy_overrides_ini_and_invalid_global_policy_is_rejected() -> None:
    assert configured_tolerant_status(_config(cli="ignored", ini="failed")) == "ignored"
    assert configured_tolerant_status(_config(ini="failed")) == "failed"

    with pytest.raises(ValueError, match="cuke_tolerant_status"):
        configured_tolerant_status(_config(ini="ignore"))


def test_marker_precedes_tag_and_global_policy_and_normalizes_value() -> None:
    item = MarkerItem(
        _marker("tolerant-status-failed"),
        _marker("tolerant_status", " IGNORED "),
    )
    scenario = Scenario(name="policy", tags=(Tag("@tolerant-status-failed"),))

    assert resolve_tolerant_status(_config(ini="failed"), item, scenario) == "ignored"


def test_invalid_marker_and_tag_fall_through_to_the_next_policy() -> None:
    tagged = Scenario(name="policy", tags=(Tag("@tolerant-status-ignored"),))
    invalid_marker = MarkerItem(_marker("tolerant_status", "sometimes"))
    assert resolve_tolerant_status(_config(ini="failed"), invalid_marker, tagged) == "ignored"

    invalid_tag = Scenario(name="policy", tags=(Tag("@tolerant-status-sometimes"),))
    assert resolve_tolerant_status(_config(ini="ignored"), MarkerItem(), invalid_tag) == "ignored"


def test_tag_status_normalizes_underscores_and_case() -> None:
    scenario = Scenario(name="policy", tags=(Tag("@TOLERANT_STATUS_IGNORED"),))
    assert resolve_tolerant_status(_config(), MarkerItem(), scenario) == "ignored"


def test_wip_cli_policy_overrides_ini_and_rejects_invalid_global_values() -> None:
    assert configured_wip_status(_config(wip_cli="passed", wip_ini="skipped")) == "passed"
    assert configured_wip_status(_config(wip_ini="skipped")) == "skipped"

    with pytest.raises(ValueError, match="cuke_wip_status"):
        configured_wip_status(_config(wip_ini="pass"))


def test_wip_marker_precedes_tag_and_global_policy_and_normalizes_value() -> None:
    item = MarkerItem(
        _marker("wip-status-failed"),
        _marker("wip_status", " PASSED "),
    )
    scenario = Scenario(name="policy", tags=(Tag("@wip-status-failed"),))

    assert resolve_wip_status(_config(wip_ini="skipped"), item, scenario) == "passed"


def test_invalid_wip_marker_and_tag_fall_through_to_next_policy() -> None:
    tagged = Scenario(name="policy", tags=(Tag("@wip-status-passed"),))
    invalid_marker = MarkerItem(_marker("wip_status", "later"))
    assert resolve_wip_status(_config(wip_ini="failed"), invalid_marker, tagged) == "passed"

    invalid_tag = Scenario(name="policy", tags=(Tag("@wip-status-later"),))
    assert resolve_wip_status(_config(wip_ini="skipped"), MarkerItem(), invalid_tag) == "skipped"


def test_wip_tag_status_normalizes_underscores_and_case() -> None:
    scenario = Scenario(name="policy", tags=(Tag("@WIP_STATUS_SKIPPED"),))
    assert resolve_wip_status(_config(), MarkerItem(), scenario) == "skipped"
