"""Unit tests for Envelope-driven reporter projections."""

from __future__ import annotations

from io import StringIO
from types import SimpleNamespace

import pytest
from _pytest._io.terminalwriter import TerminalWriter
from cucumber_messages import (
    Duration,
    Envelope,
    Pickle,
    PickleStep,
    TestCase as CucumberTestCase,
    TestCaseFinished as CucumberTestCaseFinished,
    TestCaseStarted as CucumberTestCaseStarted,
    TestStep as CucumberTestStep,
    TestStepFinished as CucumberTestStepFinished,
    TestStepResult as CucumberTestStepResult,
    TestStepResultStatus as CucumberTestStepResultStatus,
    Timestamp,
)

from pytest_bdd.model.message_reporter import CucumberMessageReportStore
from pytest_bdd.parser import GherkinParser
from pytest_bdd.plugin.cucumber_json.plugin import LogBDDCucumberJSON
from pytest_bdd.plugin.gherkin_terminal_reporter.plugin import GherkinTerminalReporter
from pytest_bdd.util.other import IdGenerator

pytestmark = [pytest.mark.unit]


def _config() -> SimpleNamespace:
    """Build the minimal parser configuration used by the test."""
    return SimpleNamespace(stash={IdGenerator.STASH_KEY: IdGenerator()}, hook=SimpleNamespace())


def test_store_projects_finished_envelopes_to_cucumber_json(tmp_path) -> None:
    """Project a Cucumber Messages lifecycle into one Cucumber JSON scenario."""
    feature_path = tmp_path / "sample.feature"
    feature_path.write_text("Feature: F\n  Scenario: S\n    Given foo\n", encoding="utf-8")
    document = (
        GherkinParser(id_generator=IdGenerator())
        .parse(
            _config(),
            feature_path,
            f"file:{feature_path}",
        )
        .gherkin_document
    )
    store = CucumberMessageReportStore()
    messages = [
        Envelope(gherkin_document=document),
        Envelope(
            pickle=Pickle(
                ast_node_ids=["1"],
                id="pickle-1",
                language="en",
                name="S",
                steps=[PickleStep(ast_node_ids=["0"], id="pickle-step-1", text="foo")],
                tags=[],
                uri=f"file:{feature_path}",
            ),
        ),
        Envelope(
            test_case=CucumberTestCase(
                id="test-case-1",
                pickle_id="pickle-1",
                test_steps=[CucumberTestStep(id="test-step-1", pickle_step_id="pickle-step-1")],
            ),
        ),
        Envelope(
            test_case_started=CucumberTestCaseStarted(
                attempt=0,
                id="attempt-1",
                test_case_id="test-case-1",
                timestamp=Timestamp(seconds=0, nanos=0),
            ),
        ),
        Envelope(
            test_step_finished=CucumberTestStepFinished(
                test_case_started_id="attempt-1",
                test_step_id="test-step-1",
                test_step_result=CucumberTestStepResult(
                    duration=Duration(seconds=0, nanos=2),
                    status=CucumberTestStepResultStatus.passed,
                ),
                timestamp=Timestamp(seconds=1, nanos=0),
            ),
        ),
        Envelope(
            test_case_finished=CucumberTestCaseFinished(
                test_case_started_id="attempt-1",
                timestamp=Timestamp(seconds=1, nanos=0),
                will_be_retried=False,
            ),
        ),
    ]

    projections = [projection for message in messages if (projection := store.consume(message)) is not None]

    assert len(projections) == 1
    assert projections[0]["feature"]["name"] == "F"
    assert projections[0]["scenario"]["name"] == "S"
    assert projections[0]["scenario"]["steps"][0]["result"]["status"] == "passed"
    assert projections[0]["scenario"]["steps"][0]["result"]["duration"] == 2
    assert len(store.render()) == 1

    output_path = tmp_path / "cucumber.json"
    plugin = LogBDDCucumberJSON(str(output_path))
    for message in messages:
        plugin.pytest_bdd_message(config=SimpleNamespace(), message=message)
    plugin.pytest_sessionfinish()

    assert output_path.read_text(encoding="utf-8").startswith('[{"keyword": "Feature"')

    output = StringIO()
    terminal_reporter = GherkinTerminalReporter.__new__(GherkinTerminalReporter)
    terminal_reporter._message_store = CucumberMessageReportStore()
    terminal_reporter._message_mode = False
    terminal_reporter.config = SimpleNamespace(option=SimpleNamespace(verbose=2))
    terminal_reporter.currentfspath = None
    terminal_reporter._tw = TerminalWriter(file=output)
    for message in messages:
        terminal_reporter.pytest_bdd_message(config=_config(), message=message)

    assert "Feature: F" in output.getvalue()
    assert "Given  foo (PASSED)" in output.getvalue()
