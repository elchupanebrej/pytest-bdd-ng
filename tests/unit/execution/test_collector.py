from __future__ import annotations

from unittest.mock import MagicMock

from pytest_bdd.collector import (
    FeatureFileCollector,
    FeatureFileModule,
    Module,
    ModuleCollector,
    PackageCollector,
    ScenarioItem,
)
from pytest_bdd.scenario import FeaturePathType as PathType


def test_collector_classes_and_aliases() -> None:
    assert FeatureFileCollector is FeatureFileModule
    assert ModuleCollector is Module
    assert issubclass(PackageCollector, object)
    assert issubclass(ScenarioItem, object)


def test_detect_uri_pathtype() -> None:
    path, p_type = FeatureFileCollector.detect_uri_pathtype("file:///tmp/test.feature")
    assert p_type == PathType.PATH
    assert path == "/tmp/test.feature"

    url, u_type = FeatureFileCollector.detect_uri_pathtype("http://example.com/test.feature")
    assert u_type == PathType.URL
    assert url == "http://example.com/test.feature"

    none_path, none_type = FeatureFileCollector.detect_uri_pathtype(None)
    assert none_path is None
    assert none_type == PathType.UNDEFINED


def test_scenario_item_init_and_reportinfo() -> None:
    mock_parent = MagicMock()
    mock_feature = MagicMock(uri="features/login.feature")
    mock_scenario = MagicMock(name="Successful Login", line=10)

    item = ScenarioItem.from_parent(
        parent=mock_parent,
        name="test_login",
        feature=mock_feature,
        scenario=mock_scenario,
    )
    assert item.feature is mock_feature
    assert item.scenario is mock_scenario

    _path, line, desc = item.reportinfo()
    assert line == 10
    assert desc == "Scenario: test_login"

    # runtest is callable
    item.runtest()
