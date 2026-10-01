from __future__ import annotations

from typing import TYPE_CHECKING

from pytest_cuke.compatibility.struct_bdd import STRUCT_BDD_INSTALLED
from pytest_cuke.model import Feature, Scenario, Step
from pytest_cuke.scenario_locator import FileScenarioLocator

from pytest import mark

pytestmark = mark.contract


if TYPE_CHECKING:
    from pathlib import Path


def test_seam2_contract_all_formats(tmp_path: Path) -> None:
    """Canned Gherkin, Markdown, and YAML features resolve to the expected model trees."""
    gherkin = tmp_path / "test.feature"
    gherkin.write_text("Feature: Gherkin\n  Scenario: G\n    Given g1\n", encoding="utf-8")

    markdown = tmp_path / "test.md"
    markdown.write_text("# Feature: Markdown\n## Scenario: M\n* Given m1\n", encoding="utf-8")

    feature_paths = [gherkin, markdown]
    expected = {
        "Gherkin": ("G", "g1"),
        "Markdown": ("M", "m1"),
    }
    if STRUCT_BDD_INSTALLED:
        yaml = tmp_path / "test.bdd.yaml"
        yaml.write_text(
            "Name: StructBDD\nSteps:\n  - Step:\n      Name: Y\n      Steps:\n        - Given: y1\n",
            encoding="utf-8",
        )
        feature_paths.append(yaml)
        expected["StructBDD"] = ("Y", "y1")

    features = list(FileScenarioLocator(feature_paths=feature_paths).resolve_features())
    features_by_name = {feature.name: feature for feature in features}
    assert set(features_by_name) == set(expected)

    for feature_name, (scenario_name, step_name) in expected.items():
        feature = features_by_name[feature_name]
        assert isinstance(feature, Feature)
        assert len(feature.scenarios) == 1

        scenario = feature.scenarios[0]
        assert isinstance(scenario, Scenario)
        assert scenario.name == scenario_name
        assert len(scenario.steps) == 1

        step = scenario.steps[0]
        assert isinstance(step, Step)
        assert step.keyword.strip() == "Given"
        assert step.name == step_name
