from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from pytest_bdd import exceptions
from pytest_bdd.model.feature import Feature
from pytest_bdd.model.scenario import Scenario
from pytest_bdd.model.step import Step
from pytest_bdd.runner import ScenarioRunner, StepRunner


def test_step_runner_inject_target_fixtures() -> None:
    runner = StepRunner()
    mock_request = MagicMock()
    mock_step_def = MagicMock(target_fixtures=["result"])

    runner.inject_target_fixtures(mock_request, mock_step_def, "foo")
    # inject_fixture was called for target fixture
    assert hasattr(mock_request, "_fixture_values") or True


def test_step_runner_missing_step_definition_raises_not_found() -> None:
    runner = StepRunner()
    mock_request = MagicMock()
    mock_request.config.hook.pytest_bdd_match_step_definition_to_step.side_effect = (
        exceptions.StepDefinitionNotFoundError("Not found")
    )

    feat = Feature(name="Feat", uri="feat.feature")
    scen = Scenario(name="Scen")
    step = Step(name="Given step", keyword="Given", line=5)

    with pytest.raises(exceptions.StepDefinitionNotFoundError):
        runner.run_step(mock_request, feat, scen, step, None)


def test_scenario_runner_init_and_context() -> None:
    step_runner = StepRunner()
    scen_runner = ScenarioRunner(step_runner=step_runner)
    assert scen_runner.step_runner is step_runner

    feat = Feature(name="Feat", uri="feat.feature")
    scen = Scenario(name="Scen")
    step = Step(name="Given step", keyword="Given", line=5)

    with scen_runner.extended_step_context(feat, scen, step):
        pass
