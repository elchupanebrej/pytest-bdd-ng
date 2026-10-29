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


def test_interrupted_scenario_run_keeps_unknown_step_and_marks_remaining_steps_skipped() -> None:
    steps = (
        Step(name="interrupted step", keyword="Given "),
        Step(name="unstarted step", keyword="And "),
    )
    feature = Feature(name="Interrupted reporting")
    scenario = Scenario(name="Interrupted", steps=steps)
    context = RunContext()
    scenario_run = context.start_scenario(
        nodeid="runtime.feature::Interrupted",
        feature=feature,
        scenario=scenario,
    )
    step_run = context.start_step(steps[0])
    context.finish_step(step_run, status="interrupted", exception=KeyboardInterrupt("interrupt sentinel"))
    context.finish_active(status="interrupted", exception=KeyboardInterrupt("interrupt sentinel"))

    report = ScenarioReport.from_scenario_run(scenario_run).serialize()

    assert [step["status"] for step in report["steps"]] == ["unknown", "skipped"]
    assert report["steps"][0]["error_message"] == "interrupt sentinel"


def test_interrupted_before_first_step_is_not_serialized_as_passed() -> None:
    steps = (Step(name="first step", keyword="Given "), Step(name="second step", keyword="And "))
    feature = Feature(name="Interrupted setup")
    scenario = Scenario(name="Before first step", steps=steps)
    context = RunContext()
    scenario_run = context.start_scenario(
        nodeid="runtime.feature::Before first step",
        feature=feature,
        scenario=scenario,
    )
    context.finish_active(status="interrupted", exception=KeyboardInterrupt("setup interrupt"))

    report = ScenarioReport.from_scenario_run(scenario_run).serialize()

    assert [step["status"] for step in report["steps"]] == ["unknown", "skipped"]
    assert report["steps"][0]["error_message"] == "setup interrupt"


def test_teardown_interrupt_marks_terminal_completed_step_unknown() -> None:
    steps = (
        Step(name="completed first step", keyword="Given "),
        Step(name="completed final step", keyword="Then "),
    )
    feature = Feature(name="Teardown interruption")
    scenario = Scenario(name="Teardown interrupt", steps=steps)
    context = RunContext()
    scenario_run = context.start_scenario(
        nodeid="runtime.feature::Teardown interrupt",
        feature=feature,
        scenario=scenario,
    )

    for step in steps:
        step_run = context.start_step(step)
        context.finish_step(step_run, status="passed")
    context.finish_active(status="passed")
    context.record_teardown_error(KeyboardInterrupt("teardown interrupt sentinel"), status="interrupted")

    report = ScenarioReport.from_scenario_run(scenario_run).serialize()

    assert [step["status"] for step in report["steps"]] == ["passed", "unknown"]
    assert report["steps"][-1]["error_message"] == "teardown interrupt sentinel"


def test_teardown_interrupt_overrides_skipped_terminal_step() -> None:
    steps = (Step(name="skipped step", keyword="Given "),)
    feature = Feature(name="Teardown interruption")
    scenario = Scenario(name="Skipped step then teardown interrupt", steps=steps)
    context = RunContext()
    scenario_run = context.start_scenario(
        nodeid="runtime.feature::Skipped step then teardown interrupt",
        feature=feature,
        scenario=scenario,
    )
    step_run = context.start_step(steps[0])
    context.finish_step(step_run, status="skipped", failure_reason="step skip sentinel")
    context.finish_active(status="skipped")
    context.record_teardown_error(KeyboardInterrupt("teardown interrupt sentinel"), status="interrupted")

    report = ScenarioReport.from_scenario_run(scenario_run).serialize()

    assert report["steps"][0]["status"] == "unknown"
    assert report["steps"][0]["skipped"] is False
    assert report["steps"][0]["error_message"] == "teardown interrupt sentinel"


def test_teardown_interrupt_after_nonterminal_skip_marks_final_unstarted_step_unknown() -> None:
    steps = (
        Step(name="completed step", keyword="Given "),
        Step(name="skipped step", keyword="When "),
        Step(name="final unstarted step", keyword="Then "),
    )
    feature = Feature(name="Teardown interruption")
    scenario = Scenario(name="Nonterminal skip then teardown interrupt", steps=steps)
    context = RunContext()
    scenario_run = context.start_scenario(
        nodeid="runtime.feature::Nonterminal skip then teardown interrupt",
        feature=feature,
        scenario=scenario,
    )
    completed_run = context.start_step(steps[0])
    context.finish_step(completed_run, status="passed")
    skipped_run = context.start_step(steps[1])
    context.finish_step(skipped_run, status="skipped", failure_reason="step skip sentinel")
    context.finish_active(status="skipped")
    context.record_teardown_error(KeyboardInterrupt("teardown interrupt sentinel"), status="interrupted")

    report = ScenarioReport.from_scenario_run(scenario_run).serialize()

    assert [step["status"] for step in report["steps"]] == ["passed", "skipped", "unknown"]
    assert report["steps"][1]["skipped"] is True
    assert report["steps"][2]["skipped"] is False
    assert report["steps"][2]["error_message"] == "teardown interrupt sentinel"


@pytest.mark.parametrize("step_status", ("failed", "undefined"))
def test_teardown_interrupt_after_nonterminal_error_preserves_error_and_marks_final_step_unknown(
    step_status: str,
) -> None:
    steps = (
        Step(name="error step", keyword="Given "),
        Step(name="unstarted middle step", keyword="When "),
        Step(name="final unstarted step", keyword="Then "),
    )
    feature = Feature(name="Teardown interruption")
    scenario = Scenario(name="Nonterminal step error then teardown interrupt", steps=steps)
    context = RunContext()
    scenario_run = context.start_scenario(
        nodeid=f"runtime.feature::Nonterminal {step_status} then teardown interrupt",
        feature=feature,
        scenario=scenario,
    )
    step_run = context.start_step(steps[0])
    context.finish_step(step_run, status=step_status, exception=RuntimeError("earlier step error sentinel"))
    context.finish_active(status=step_status, exception=RuntimeError("earlier step error sentinel"))
    context.record_teardown_error(KeyboardInterrupt("teardown interrupt sentinel"), status="interrupted")

    report = ScenarioReport.from_scenario_run(scenario_run).serialize()

    assert [step["status"] for step in report["steps"]] == [step_status, "skipped", "unknown"]
    assert report["steps"][0]["error_message"] == "earlier step error sentinel"
    assert report["steps"][1]["skipped"] is True
    assert report["steps"][2]["skipped"] is False
    assert report["steps"][2]["error_message"] == "teardown interrupt sentinel"


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
