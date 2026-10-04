from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from pytest_cuke.model.background import Background
from pytest_cuke.model.feature import Feature
from pytest_cuke.model.scenario import Scenario
from pytest_cuke.model.scenario_report import ScenarioReport as RuntimeScenarioReport
from pytest_cuke.model.session_run import RunContext
from pytest_cuke.model.step import Step
from pytest_cuke.reporting import ScenarioReport, ScenarioReporterPlugin, StepReport


def test_scenario_report_uses_normalized_file_uri_independent_of_cwd(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    project = tmp_path / "project"
    tools = project / "tools"
    source = project / "selected-features" / "invocation.feature"
    tools.mkdir(parents=True)
    source.parent.mkdir()
    monkeypatch.chdir(tools)
    feature = Feature(name="Invocation", uri="file:invocation.feature", filename=str(source))

    report = ScenarioReport(feature=feature, scenario=Scenario(name="Selected root"))

    assert feature.rel_filename == source.as_posix()
    assert report.serialize()["feature"]["rel_filename"] == "invocation.feature"


def test_failed_step_report_marks_unexecuted_background_and_scenario_steps_skipped() -> None:
    background_steps = (
        Step(name="background fails", keyword="Given "),
        Step(name="remaining background", keyword="And "),
    )
    scenario_steps = (
        Step(name="scenario action", keyword="When "),
        Step(name="scenario result", keyword="Then "),
    )
    background = Background(steps=background_steps)
    feature = Feature(name="Background reporting", background=background)
    scenario = Scenario(name="Failure", background=background, steps=scenario_steps)
    report = ScenarioReport(feature=feature, scenario=scenario)
    report.add_step_report(StepReport(background_steps[0]))

    report.fail()

    serialized_steps = report.serialize()["steps"]
    assert [step["status"] for step in serialized_steps] == ["failed", "skipped", "skipped", "skipped"]


def test_failed_scenario_run_keeps_later_steps_as_skipped() -> None:
    steps = (
        Step(name="completed step", keyword="Given "),
        Step(name="failed step", keyword="When "),
        Step(name="unexecuted step", keyword="Then "),
    )
    feature = Feature(name="Runtime reporting")
    scenario = Scenario(name="Failure", steps=steps)
    context = RunContext()
    scenario_run = context.start_scenario(
        nodeid="runtime.feature::Failure",
        feature=feature,
        scenario=scenario,
    )

    for step, status in ((steps[0], "passed"), (steps[1], "failed")):
        step_run = context.start_step(step)
        context.finish_step(step_run, status=status)
    context.finish_active(status="failed", exception=RuntimeError("step failed"))

    report = ScenarioReport.from_scenario_run(scenario_run)

    assert [step["status"] for step in report.serialize()["steps"]] == ["passed", "failed", "skipped"]


def test_ignored_failed_step_keeps_scenario_passed_and_preserves_error() -> None:
    step = Step(name="tolerated step", keyword="When ")
    feature = Feature(name="Runtime reporting")
    scenario = Scenario(name="Tolerated", steps=(step,))
    context = RunContext()
    scenario_run = context.start_scenario(nodeid="runtime.feature::Tolerated", feature=feature, scenario=scenario)
    step_run = context.start_step(step)
    context.finish_step(step_run, status="failed", exception=RuntimeError("body assertion"))
    context.finish_active(status="passed")

    report = ScenarioReport.from_scenario_run(scenario_run).serialize()

    assert scenario_run.status == "passed"
    assert report["steps"][0]["status"] == "failed"
    assert report["steps"][0]["error_message"] == "body assertion"

    runtime_report = RuntimeScenarioReport.from_scenario_run(scenario_run).serialize()
    assert runtime_report["failed"] is False
    assert runtime_report["status"] == "passed"
    assert runtime_report["error_message"] is None
    assert runtime_report["steps"][0]["error_message"] == "body assertion"


def test_scenario_report_failure_before_first_step_is_not_serialized_as_passed() -> None:
    step = Step(name="background setup", keyword="Given ")
    feature = Feature(name="Background setup", background=Background(steps=(step,)))
    scenario = Scenario(name="Setup failure")
    report = ScenarioReport(feature=feature, scenario=scenario)

    report.fail()

    serialized_steps = report.serialize()["steps"]
    assert [step["status"] for step in serialized_steps] == ["failed"]


def test_scenario_report_skip_marks_remaining_steps_skipped() -> None:
    background = Background(steps=(Step(name="skip now", keyword="Given "),))
    feature = Feature(name="Background skip", background=background)
    scenario = Scenario(
        name="Skip",
        background=background,
        steps=(Step(name="scenario action", keyword="When "),),
    )
    report = ScenarioReport(feature=feature, scenario=scenario)
    report.add_step_report(StepReport(background.steps[0]))

    report.skip()

    serialized_steps = report.serialize()["steps"]
    assert [step["status"] for step in serialized_steps] == ["skipped", "skipped"]


def test_plain_test_call_does_not_inherit_previous_scenario_report() -> None:
    plugin = ScenarioReporterPlugin()
    report = SimpleNamespace(passed=True, failed=False, skipped=False)
    item = SimpleNamespace(name="test_plain", get_closest_marker=lambda name: None)
    call = SimpleNamespace(when="call")
    outcome = SimpleNamespace(get_result=lambda: report)
    hook = plugin.pytest_runtest_makereport(item=item, call=call)

    next(hook)
    with pytest.raises(StopIteration):
        hook.send(outcome)

    assert not hasattr(report, "scenario")
