from __future__ import annotations

from types import SimpleNamespace

import pytest

from pytest_cuke.model.scenario import Scenario
from pytest_cuke.model.tag import Tag
from pytest_cuke.steps.tolerant_policy import configured_tolerant_status, resolve_tolerant_status


class MarkerItem:
    def __init__(self, *markers: object) -> None:
        self.markers = markers

    def iter_markers(self, name: str | None = None):
        return iter(marker for marker in self.markers if name is None or marker.name == name)


def _config(cli: str | None = None, ini: str = "failed") -> SimpleNamespace:
    return SimpleNamespace(option=SimpleNamespace(cuke_tolerant_status=cli), getini=lambda _name: ini)


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
