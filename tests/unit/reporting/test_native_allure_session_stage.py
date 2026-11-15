import json

import pytest

pytest.importorskip("allure_commons")

from pytest_cuke.model.message_types import Envelope, ExceptionMessage, Timestamp
from pytest_cuke.model.message_types import TestRunFinished as RunFinished
from pytest_cuke.model.message_types import TestRunStarted as RunStarted
from pytest_cuke.native_allure import NativeAllureReporter


def _timestamp() -> Timestamp:
    return Timestamp(seconds=1, nanos=0)


def _finish_run(tmp_path, *, message, exception_type, exception_message):
    reporter = NativeAllureReporter(tmp_path)
    started = RunStarted(timestamp=_timestamp(), id="run")
    reporter._consume(
        Envelope(test_run_started=started),
        {"testRunStarted": {"id": "run", "timestamp": {"seconds": 1, "nanos": 0}}},
    )
    finished = RunFinished(
        success=False,
        timestamp=_timestamp(),
        message=message,
        exception=ExceptionMessage(type=exception_type, message=exception_message, stack_trace=exception_message),
        test_run_started_id="run",
    )
    reporter._consume(
        Envelope(test_run_finished=finished),
        {
            "testRunFinished": {
                "success": False,
                "timestamp": {"seconds": 1, "nanos": 0},
                "message": message,
                "testRunStartedId": "run",
                "exception": {"type": exception_type, "message": exception_message, "stackTrace": exception_message},
            }
        },
    )
    containers = list(tmp_path.glob("*-container.json"))
    assert len(containers) == 1
    return json.loads(containers[0].read_text(encoding="utf-8"))


def _run_stage(container):
    return next(fixture for fixture in container["afters"] if fixture["name"] == "pytest test run")


def test_failed_tests_do_not_make_the_shared_allure_stage_broken(tmp_path):
    container = _finish_run(
        tmp_path,
        message="pytest session exit status: 1",
        exception_type="PytestExitCode",
        exception_message="1",
    )

    assert _run_stage(container)["status"] == "passed"


def test_reporting_failure_keeps_the_shared_allure_stage_broken(tmp_path):
    container = _finish_run(
        tmp_path,
        message="pytest session exit status: 1; Messages reporting failed",
        exception_type="MessageReportingError",
        exception_message="Messages reporting failed",
    )

    assert _run_stage(container)["status"] == "broken"
