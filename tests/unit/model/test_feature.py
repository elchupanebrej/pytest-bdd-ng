from __future__ import annotations

from pytest_bdd.model.background import Background
from pytest_bdd.model.feature import Feature
from pytest_bdd.model.rule import Rule
from pytest_bdd.model.scenario import Scenario
from pytest_bdd.model.step import Step
from pytest_bdd.model.tag import Tag


def test_feature_model() -> None:
    tag = Tag(name="@core")
    bg = Background(name="BG", steps=(Step(name="init", keyword="Given "),))
    sc = Scenario(name="Sc 1", steps=(Step(name="run", keyword="When "),))
    rule = Rule(name="Rule 1", scenarios=(Scenario(name="Sc in rule"),))
    feature = Feature(
        name="Test Feature",
        tags=(tag,),
        description="Feature description",
        background=bg,
        scenarios=(sc,),
        rules=(rule,),
        uri="test.feature",
    )

    assert feature.name == "Test Feature"
    assert feature.tag_names == ("core",)
    assert len(feature.all_scenarios) == 2
    assert feature.uri == "test.feature"
