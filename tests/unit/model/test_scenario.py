from __future__ import annotations

from pytest_bdd.model.background import Background
from pytest_bdd.model.rule import Rule
from pytest_bdd.model.scenario import Scenario
from pytest_bdd.model.step import Step
from pytest_bdd.model.tag import Tag


def test_scenario_and_rule() -> None:
    t = Tag(name="@smoke")
    s = Step(name="step 1", keyword="Given ")
    bg = Background(steps=(s,))
    sc = Scenario(name="Sc 1", tags=(t,), background=bg, steps=(Step("step 2", "When "),))
    assert sc.tag_names == ("smoke",)
    assert len(sc.all_steps) == 2

    rule = Rule(name="Rule 1", scenarios=(sc,))
    assert rule.name == "Rule 1"
    assert len(rule.scenarios) == 1
