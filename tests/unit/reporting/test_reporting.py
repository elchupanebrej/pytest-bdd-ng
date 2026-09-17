from __future__ import annotations

from types import SimpleNamespace

from pytest_bdd.model.step import StepType
from pytest_bdd.reporting import (
    ScenarioReport,
    ScenarioReporterPlugin,
    StepReport,
    serialize_step_keyword,
    serialize_step_type,
)

from pytest import mark

pytestmark = mark.unit


class FeatureStub:
    name = "Stub Feature"
    filename = "/tmp/stub.feature"
    uri = "file:/tmp/stub.feature"
    line = 0
    description = "desc"
    tag_names = ("feature_tag",)

    def _get_pickle_line_number(self, pickle: object) -> int:
        return 42

    def _get_step_line_number(self, step: object) -> int:
        return 7

    def _get_step_keyword(self, step: object) -> str:
        return "Given"


class PickleStub:
    name = "Stub Scenario [table_rows:[line: 4]]"
    line = 0
    tag_names = ("feature_tag", "scenario_tag")
    steps = (SimpleNamespace(name="step one", text="", line=0, type=StepType.context, keyword="Given "),)


class ScenarioStub:
    name = "S"
    line = 0
    tag_names = ()
    steps = (
        SimpleNamespace(name="first", text="", line=0, type=None, keyword=""),
        SimpleNamespace(name="second", text="", line=0, type=None, keyword=""),
        SimpleNamespace(name="third", text="", line=0, type=None, keyword=""),
    )


def test_serialize_step_type_and_keyword_vocabulary() -> None:
    assert serialize_step_type(SimpleNamespace(prefix="Given")) == "Given"
    assert serialize_step_type(SimpleNamespace(prefix="", type=StepType.context)) == "context"
    assert serialize_step_type(SimpleNamespace(prefix="", type=None)) == ""
    assert serialize_step_keyword(SimpleNamespace(keyword=" Given ")) == "Given"
    assert serialize_step_keyword(SimpleNamespace()) == ""


def test_step_report_duration_is_zero_until_finalized() -> None:
    step = SimpleNamespace(name="s", text="", line=0, type=None, keyword="Given")
    report = StepReport(step)
    assert report.duration == 0.0
    report.finalize(failed=True)
    assert report.failed is True
    assert report.duration >= 0.0


def test_scenario_report_serializes_uri_fallback_and_pickle_steps() -> None:
    report = ScenarioReport(feature=FeatureStub(), scenario=PickleStub())
    data = report.serialize()

    assert data["name"].rstrip() == "Stub Scenario"
    assert data["line_number"] == 42
    assert data["tags"] == ["scenario_tag"]
    assert data["feature"]["rel_filename"] == "/tmp/stub.feature"
    assert data["feature"]["tags"] == ["feature_tag"]
    assert data["steps"][0]["type"] == "context"
    assert data["steps"][0]["keyword"] == "Given"
    assert data["steps"][0]["line_number"] == 7


def test_scenario_report_fail_appends_remaining_scenario_steps() -> None:
    report = ScenarioReport(feature=FeatureStub(), scenario=ScenarioStub())
    report.add_step_report(StepReport(step=ScenarioStub.steps[0]))

    report.fail()

    assert len(report.step_reports) == 3
    assert report.current_step_report.failed is True
    assert all(step_report.failed for step_report in report.step_reports)


def test_reporter_plugin_hooks_are_noops_without_active_report() -> None:
    plugin = ScenarioReporterPlugin()
    assert plugin.current_report is None

    plugin.pytest_bdd_step_error(None, None, None, None, None, None, ValueError("x"))
    plugin.pytest_bdd_before_step(None, None, None, None, None)
    plugin.pytest_bdd_after_step(None, None, None, None, None, None)

    assert plugin.current_report is None
