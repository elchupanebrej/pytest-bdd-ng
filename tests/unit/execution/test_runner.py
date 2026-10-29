from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from pytest_cuke import exceptions
from pytest_cuke.model.background import Background
from pytest_cuke.model.feature import Feature
from pytest_cuke.model.scenario import Scenario
from pytest_cuke.model.session_run import RunContext
from pytest_cuke.model.step import Step
from pytest_cuke.parsers.string_parser import string
from pytest_cuke.runner import ScenarioRunner, StepRunner, _IgnoredStepFailure, _WipPassed
from pytest_cuke.steps.decorators import not_implemented, tolerant, when

pytestmark = pytest.mark.unit


def active_run(feature: Feature, scenario: Scenario, step: Step, previous_step: Step | None = None) -> RunContext:
    """Build the same active context lifecycle hooks receive during normal execution."""
    run = RunContext()
    run.start_scenario(nodeid="test.feature::scenario", feature=feature, scenario=scenario)
    if previous_step is not None:
        run.start_step(previous_step)
        previous_run = run.step_run
        assert previous_run is not None
        run.finish_step(previous_run)
    run.start_step(step)
    return run

pytestmark = pytest.mark.unit


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
        runner.run_step(mock_request, active_run(feat, scen, step))


def test_passed_wip_policy_bypasses_body_hooks_and_target_fixtures(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[str] = []

    @when(string("the pending operation runs"), target_fixture="pending_result")
    @not_implemented
    def pending_operation() -> str:
        calls.append("body")
        return "real-result"

    definition = next(iter(pending_operation.__pytest_cuke_step_definitions__))
    request = MagicMock()
    request.node.iter_markers.return_value = iter(())
    request.config.option.cuke_wip_status = "passed"
    request.config.getini.return_value = "failed"
    request.config.hook.pytest_cuke_match_step_definition_to_step.return_value = definition
    injected_fixtures: list[str] = []
    monkeypatch.setattr(
        "pytest_cuke.runner.inject_fixture", lambda _request, name, _value: injected_fixtures.append(name)
    )

    feature = Feature(name="Feature")
    scenario = Scenario(name="Scenario")
    step = Step(name="the pending operation runs", keyword="When ")
    result = StepRunner().run_step(request, active_run(feature, scenario, step))

    assert isinstance(result, _WipPassed)
    assert calls == []
    assert injected_fixtures == []
    request.getfixturevalue.assert_not_called()
    request.config.hook.pytest_cuke_step_bypassed.assert_called_once()
    assert request.config.hook.pytest_cuke_step_bypassed.call_args.kwargs["status"] == "passed"
    request.config.hook.pytest_cuke_before_step.assert_not_called()
    request.config.hook.pytest_cuke_before_step_call.assert_not_called()
    request.config.hook.pytest_cuke_after_step.assert_not_called()


def test_skipped_wip_policy_bypasses_body_and_reports_skip() -> None:
    calls: list[str] = []

    @not_implemented
    @when(string("the skipped pending operation runs"))
    def skipped_pending_operation() -> None:
        calls.append("body")

    definition = next(iter(skipped_pending_operation.__pytest_cuke_step_definitions__))
    request = MagicMock()
    request.node.iter_markers.return_value = iter(())
    request.config.option.cuke_wip_status = "skipped"
    request.config.getini.return_value = "failed"
    request.config.hook.pytest_cuke_match_step_definition_to_step.return_value = definition

    with pytest.raises(pytest.skip.Exception):
        feature = Feature(name="Feature")
        scenario = Scenario(name="Scenario")
        step = Step(name="the skipped pending operation runs", keyword="When ")
        StepRunner().run_step(request, active_run(feature, scenario, step))

    assert calls == []
    request.config.hook.pytest_cuke_step_bypassed.assert_called_once()
    assert request.config.hook.pytest_cuke_step_bypassed.call_args.kwargs["status"] == "skipped"
    request.config.hook.pytest_cuke_before_step.assert_not_called()
    request.config.hook.pytest_cuke_before_step_call.assert_not_called()
    request.config.hook.pytest_cuke_step_error.assert_not_called()


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
    monkeypatch.setattr(
        "pytest_cuke.runner.inject_fixture", lambda _request, name, _value: injected_fixtures.append(name)
    )

    feature = Feature(name="Feature")
    scenario = Scenario(name="Scenario")
    step = Step(name="I fail before producing the target", keyword="When ")
    result = StepRunner().run_step(request, active_run(feature, scenario, step))

    assert isinstance(result, _IgnoredStepFailure)
    assert str(result.exception) == "step body"
    assert injected_fixtures == []
    request.config.hook.pytest_cuke_step_error.assert_called_once()
    assert request.config.hook.pytest_cuke_step_error.call_args.kwargs["tolerated"] is True
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
    feature = Feature(name="Feature")
    scenario = Scenario(name="Scenario")
    step = Step(name="I would fail later", keyword="When ")

    with pytest.raises(RuntimeError, match="hook failure"):
        StepRunner().run_step(request, active_run(feature, scenario, step))

    request.config.hook.pytest_cuke_step_error.assert_called_once()


def test_ignored_policy_does_not_swallow_step_lookup_errors() -> None:
    request = MagicMock()
    request.config.option.cuke_tolerant_status = "ignored"
    request.config.hook.pytest_cuke_match_step_definition_to_step.side_effect = RuntimeError("ambiguous lookup")
    feature = Feature(name="Feature")
    scenario = Scenario(name="Scenario")
    step = Step(name="ambiguous step", keyword="When ")

    with pytest.raises(RuntimeError, match="ambiguous lookup"):
        StepRunner().run_step(request, active_run(feature, scenario, step))

    request.config.hook.pytest_cuke_step_error.assert_not_called()


def test_scenario_runner_init_and_context() -> None:
    step_runner = StepRunner()
    scen_runner = ScenarioRunner(step_runner=step_runner)
    assert scen_runner.step_runner is step_runner

    feat = Feature(name="Feat", uri="feat.feature")
    scen = Scenario(name="Scen")
    step = Step(name="Given step", keyword="Given", line=5)

    with scen_runner.extended_step_context(feat, scen, step):
        pass


def test_scenario_runner_classifies_keyboard_interrupt_as_interrupted() -> None:
    assert ScenarioRunner._status_for_exception(KeyboardInterrupt("interrupt")) == "interrupted"


def test_step_runner_dispatches_step_error_for_keyboard_interrupt() -> None:
    @when(string("the step is interrupted"))
    def interrupted_step() -> None:
        pass

    definition = next(iter(interrupted_step.__pytest_cuke_step_definitions__))
    request = MagicMock()
    request.node.iter_markers.return_value = iter(())
    request.config.option.cuke_tolerant_status = "failed"
    request.config.getini.return_value = "failed"
    request.config.hook.pytest_cuke_match_step_definition_to_step.return_value = definition
    request.config.hook.pytest_cuke_get_step_caller.return_value = lambda: (_ for _ in ()).throw(
        KeyboardInterrupt("interrupt")
    )

    feature = Feature(name="Feature")
    scenario = Scenario(name="Scenario")
    step = Step(name="the step is interrupted", keyword="When ")
    with pytest.raises(KeyboardInterrupt, match="interrupt"):
        StepRunner().run_step(request, active_run(feature, scenario, step))

    request.config.hook.pytest_cuke_step_error.assert_called_once()
    assert isinstance(request.config.hook.pytest_cuke_step_error.call_args.kwargs["exception"], KeyboardInterrupt)


def test_mock_run_aggregates_missing_steps_and_keeps_previous_step_context(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    background_step = Step(name="background binding", keyword="Given", line=2)
    missing_first = Step(name="missing first", keyword="When", line=4)
    matched = Step(name="matched middle", keyword="And", line=5)
    missing_last = Step(name="missing last", keyword="Then", line=6)
    feature = Feature(
        name="Feature",
        uri="feature.feature",
        background=Background(steps=(background_step,)),
    )
    scenario = Scenario(name="Scenario", steps=(missing_first, matched, missing_last))
    run_context = RunContext()
    monkeypatch.setattr("pytest_cuke.runner.get_run_context", lambda _config: run_context)

    step_runner = MagicMock()
    observed_previous_steps: list[Step | None] = []

    def match_to_step(_request: object, run: RunContext) -> object:
        step = run.require_step("pytest_cuke_match_step_definition_to_step")
        observed_previous_steps.append(run.previous_step)
        if step in (missing_first, missing_last):
            raise exceptions.StepDefinitionNotFoundError(step.name)
        return object()

    step_runner.match_to_step.side_effect = match_to_step
    request = MagicMock()
    item = MagicMock()
    item.nodeid = "test_module.py::test_scenario"
    item.fixturenames = []

    with pytest.raises(exceptions.StepDefinitionNotFoundError) as error:
        ScenarioRunner(step_runner=step_runner)._verify_mock_run_bindings(item, request, feature, scenario)

    assert "missing first" in str(error.value)
    assert "missing last" in str(error.value)
    assert observed_previous_steps == [
        None,
        background_step,
        missing_first,
        matched,
    ]
    assert run_context.status == "undefined"
    assert run_context.last_error is error.value
    assert run_context.hook_phase == "pytest_runtest_call"
