import json

import pytest

from pytest_cuke.allure_conversion import convert_allure_messages
from pytest_cuke.const import PYTEST_STEP_OUTCOME_MEDIA_TYPE
from pytest_cuke.model.message_types import (
    Attachment,
    ContentEncoding,
    Duration,
    Envelope,
    Pickle,
    PickleStep,
    Status,
    TestCase as Case,
    TestCaseFinished as CaseFinished,
    TestCaseStarted as CaseStarted,
    TestRunFinished as RunFinished,
    TestRunStarted as RunStarted,
    TestStep as Step,
    TestStepFinished as StepFinished,
    TestStepResult as StepResult,
    TestStepStarted as StepStarted,
    Timestamp,
    message_to_dict,
)

_DIAGNOSTIC = {
    "testCaseStartedId": "tcs1",
    "testStepId": "ts1",
    "outcome": "tolerated-failure",
    "actualResult": {
        "status": "FAILED",
        "message": "tolerated assertion sentinel",
        "exception": {
            "type": "AssertionError",
            "message": "tolerated assertion sentinel",
            "stackTrace": "trace sentinel",
        },
    },
}


def _time() -> Timestamp:
    return Timestamp(seconds=1, nanos=0)


def _messages() -> list[Envelope]:
    return [
        Envelope(test_run_started=RunStarted(timestamp=_time(), id="run")),
        Envelope(
            pickle=Pickle(
                ast_node_ids=["ast1"],
                id="p1",
                language="en",
                name="Tolerant",
                steps=[PickleStep(id="ps1", ast_node_ids=["ast1"], text="tolerant step")],
                tags=[],
                uri="a.feature",
            )
        ),
        Envelope(
            test_case=Case(
                id="tc1",
                pickle_id="p1",
                test_steps=[Step(id="ts1", pickle_step_id="ps1", step_definition_ids=[])],
            )
        ),
        Envelope(test_case_started=CaseStarted(attempt=0, id="tcs1", test_case_id="tc1", timestamp=_time())),
        Envelope(test_step_started=StepStarted(test_case_started_id="tcs1", test_step_id="ts1", timestamp=_time())),
        Envelope(
            attachment=Attachment(
                body=json.dumps(_DIAGNOSTIC),
                content_encoding=ContentEncoding.identity,
                media_type=PYTEST_STEP_OUTCOME_MEDIA_TYPE,
                test_case_started_id="tcs1",
            )
        ),
        Envelope(
            test_step_finished=StepFinished(
                test_case_started_id="tcs1",
                test_step_id="ts1",
                timestamp=_time(),
                test_step_result=StepResult(status=Status.passed, duration=Duration(seconds=0, nanos=1)),
            )
        ),
        Envelope(
            test_case_finished=CaseFinished(test_case_started_id="tcs1", timestamp=_time(), will_be_retried=False)
        ),
        Envelope(test_run_finished=RunFinished(success=True, timestamp=_time(), test_run_started_id="run")),
    ]


def _result(output_dir):
    results = list(output_dir.glob("*-result.json"))
    assert len(results) == 1
    return json.loads(results[0].read_text(encoding="utf-8"))


def test_replay_conversion_keeps_the_tolerated_step_diagnostic(tmp_path):
    source = tmp_path / "messages.ndjson"
    source.write_text(
        "".join(json.dumps(message_to_dict(message)) + "\n" for message in _messages()),
        encoding="utf-8",
    )
    output_dir = tmp_path / "allure-results"

    convert_allure_messages(source, output_dir)

    result = _result(output_dir)
    step = result["steps"][0]
    assert result["status"] == "passed"
    assert step["status"] == "passed"
    assert step["statusDetails"] == {"message": "tolerated assertion sentinel", "trace": "trace sentinel"}


def test_native_allure_keeps_the_tolerated_step_diagnostic(tmp_path):
    pytest.importorskip("allure_commons")
    from pytest_cuke.native_allure import NativeAllureReporter

    reporter = NativeAllureReporter(tmp_path)
    for message in _messages():
        reporter.pytest_cuke_message_validated(config=None, message=message)
    reporter.stop()

    result = _result(tmp_path)
    step = result["steps"][0]
    assert result["status"] == "passed"
    assert step["status"] == "passed"
    assert step["statusDetails"] == {"message": "tolerated assertion sentinel", "trace": "trace sentinel"}
