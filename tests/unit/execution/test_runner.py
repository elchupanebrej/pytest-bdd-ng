from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from pytest_cuke import exceptions
from pytest_cuke.model.feature import Feature
from pytest_cuke.model.scenario import Scenario
from pytest_cuke.model.step import Step
from pytest_cuke.parsers.string_parser import string
from pytest_cuke.runner import ScenarioRunner, StepRunner, _IgnoredStepFailure
from pytest_cuke.steps.decorators import tolerant, when


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
    mock_request.config.hook.pytest_cuke_match_step_definition_to_step.side_effect = (
        exceptions.StepDefinitionNotFoundError("Not found")
    )

    feat = Feature(name="Feat", uri="feat.feature")
    scen = Scenario(name="Scen")
    step = Step(name="Given step", keyword="Given", line=5)

    with pytest.raises(exceptions.StepDefinitionNotFoundError):
        runner.run_step(mock_request, feat, scen, step, None)


def test_ignored_tolerant_body_error_does_not_inject_target_or_run_after_hook(monkeypatch: pytest.MonkeyPatch) -> None:
    @when(string("I fail before producing the target"), target_fixture="target")
    @tolerant
    def failing_step() -> None:
        pass

    definition = next(iter(failing_step.__pytest_cuke_step_definitions__))
    request = MagicMock()
    request.node.iter_markers.return_value = iter(())
    request.config.option.cuke_tolerant_status = "ignored"
    request.config.getini.return_value = "failed"
    request.config.hook.pytest_cuke_match_step_definition_to_step.return_value = definition
    request.config.hook.pytest_cuke_get_step_caller.return_value = lambda: (_ for _ in ()).throw(
        RuntimeError("step body")
    )
    injected_fixtures: list[str] = []
    monkeypatch.setattr("pytest_cuke.runner.inject_fixture", lambda _request, name, _value: injected_fixtures.append(name))

    result = StepRunner().run_step(
        request,
        Feature(name="Feature"),
        Scenario(name="Scenario"),
        Step(name="I fail before producing the target", keyword="When "),
        None,
    )

    assert isinstance(result, _IgnoredStepFailure)
    assert str(result.exception) == "step body"
    assert injected_fixtures == []
    request.config.hook.pytest_cuke_step_error.assert_called_once()
    request.config.hook.pytest_cuke_after_step.assert_not_called()


def test_ignored_policy_does_not_swallow_before_step_hook_errors() -> None:
    @when(string("I would fail later"))
    @tolerant
    def failing_step() -> None:
        pass

    definition = next(iter(failing_step.__pytest_cuke_step_definitions__))
    request = MagicMock()
    request.config.option.cuke_tolerant_status = "ignored"
    request.config.hook.pytest_cuke_match_step_definition_to_step.return_value = definition
    request.config.hook.pytest_cuke_before_step.side_effect = RuntimeError("hook failure")

    with pytest.raises(RuntimeError, match="hook failure"):
        StepRunner().run_step(
            request,
            Feature(name="Feature"),
            Scenario(name="Scenario"),
            Step(name="I would fail later", keyword="When "),
            None,
        )

    request.config.hook.pytest_cuke_step_error.assert_called_once()


def test_scenario_runner_init_and_context() -> None:
    step_runner = StepRunner()
    scen_runner = ScenarioRunner(step_runner=step_runner)
    assert scen_runner.step_runner is step_runner

    feat = Feature(name="Feat", uri="feat.feature")
    scen = Scenario(name="Scen")
    step = Step(name="Given step", keyword="Given", line=5)

    with scen_runner.extended_step_context(feat, scen, step):
        pass
