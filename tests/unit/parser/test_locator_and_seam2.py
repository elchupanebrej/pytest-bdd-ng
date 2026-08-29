from __future__ import annotations

from typing import TYPE_CHECKING

from pytest_bdd.model import Feature
from pytest_bdd.scenario_locator import (
    FileScenarioLocator,
    ScenarioLocatorFeatureResolver,
    ScenarioLocatorResolver,
)

if TYPE_CHECKING:
    from pathlib import Path


def test_file_scenario_locator_single_file(tmp_path: Path) -> None:
    feature_file = tmp_path / "simple.feature"
    feature_file.write_text(
        "Feature: Locator Test\n\n  Scenario: S1\n    Given step 1\n",
        encoding="utf-8",
    )
    locator = FileScenarioLocator(feature_paths=[feature_file])
    features = list(locator.resolve_features())

    assert len(features) == 1
    feat = features[0]
    assert isinstance(feat, Feature)
    assert feat.name == "Locator Test"
    assert len(feat.scenarios) == 1
    assert feat.scenarios[0].name == "S1"
    assert len(feat.scenarios[0].steps) == 1
    assert feat.scenarios[0].steps[0].name == "step 1"


def test_file_scenario_locator_directory_glob(tmp_path: Path) -> None:
    f1 = tmp_path / "f1.feature"
    f1.write_text("Feature: F1\n  Scenario: S1\n    Given a\n", encoding="utf-8")
    f2 = tmp_path / "f2.feature.md"
    f2.write_text("# Feature: F2\n## Scenario: S2\n* Given b\n", encoding="utf-8")
    f3 = tmp_path / "f3.bdd.yaml"
    f3.write_text("Name: F3\nSteps:\n  - Step:\n      Name: S3\n      Steps:\n        - Given: c\n", encoding="utf-8")

    locator = FileScenarioLocator(features_base_dir=tmp_path, feature_paths=["**/*"])
    features = list(locator.resolve_features())

    names = {f.name for f in features}
    assert "F1" in names
    assert "F2" in names
    assert "F3" in names


def test_file_scenario_locator_filtering(tmp_path: Path) -> None:
    f = tmp_path / "filter.feature"
    f.write_text(
        "Feature: Filtering\n\n"
        "  @smoke\n"
        "  Scenario: Keep Me\n"
        "    Given step a\n\n"
        "  Scenario: Skip Me\n"
        "    Given step b\n",
        encoding="utf-8",
    )
    locator = FileScenarioLocator(
        feature_paths=[f],
        filter_=lambda _config, _feat, sc: sc.name == "Keep Me",
    )
    resolved = list(locator.resolve())
    assert len(resolved) == 1
    feat, sc = resolved[0]
    assert feat.name == "Filtering"
    assert sc.name == "Keep Me"


def test_protocols_conformance() -> None:
    locator = FileScenarioLocator(feature_paths=["dummy.feature"])
    assert isinstance(locator, ScenarioLocatorFeatureResolver)
    assert isinstance(locator, ScenarioLocatorResolver)
