from __future__ import annotations

import json
import os
from pathlib import Path
from queue import Queue
from types import SimpleNamespace
from typing import Any
from unittest.mock import MagicMock

from pytest_cuke.model.message_validation import MessageValidationDiagnostic
from pytest_cuke.formatter_api import FormatterRequest
from pytest_cuke.model.message_types import (
    Attachment,
    ContentEncoding,
    Duration,
    Envelope as Message,
    ExceptionMessage,
    Pickle,
    PickleStep,
    Status,
    TestCase,
    TestCaseStarted,
    TestRunFinished,
    TestRunStarted,
    TestStep,
    TestStepFinished,
    TestStepResult,
    TestStepStarted,
    Timestamp,
    message_to_dict,
)
from pytest import ExitCode
from pytest_cuke.message_plugin import MessagePlugin, message_session_finish_hook
from pytest_cuke.message_schema_sync import resolve_upstream_release
from pytest_cuke.model.feature import Feature
from pytest_cuke.model.scenario import Scenario
from pytest_cuke.model.session_run import RunContext
from pytest_cuke.model.step import Step
from pytest_cuke.utils import IdGenerator

TestCase.__test__ = False
TestCaseStarted.__test__ = False
TestRunFinished.__test__ = False
TestRunStarted.__test__ = False
TestStep.__test__ = False
TestStepFinished.__test__ = False
TestStepResult.__test__ = False
TestStepStarted.__test__ = False


def _complete_hook_wrapper(wrapper: Any, *, excinfo: Any = None) -> None:
    next(wrapper)
    try:
        wrapper.send(SimpleNamespace(excinfo=excinfo))
    except StopIteration:
        return
    raise AssertionError("pytest hook wrapper did not complete")


def _drain_messages(plugin: MessagePlugin) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    while not plugin.process_messages_io_queue.empty():
        result.append(json.loads(plugin.process_messages_io_queue.get_nowait()))
    return result


def test_message_plugin_add_options() -> None:
    parser = MagicMock()
    group = MagicMock()
    parser.getgroup.return_value = group

    MessagePlugin.add_options(parser)
    assert parser.getgroup.call_count == 4
    assert group.addoption.call_count == 5
    assert any(call.args[0] == "--cuke-pretty" for call in group.addoption.call_args_list)
    assert any(call.args[0] == "cuke_pretty" for call in parser.addini.call_args_list)


def test_message_plugin_disabled_when_no_options() -> None:
    config = MagicMock()
    config.rootpath = Path.cwd()
    config.option.cuke_messages_ndjson = None
    config.option.cuke_html = None
    config.getini.return_value = ""

    plugin = MessagePlugin(config=config)
    assert plugin.is_disabled is True
    assert plugin.message_transport is None


def test_xdist_worker_does_not_allocate_a_local_messages_file(monkeypatch) -> None:
    config = SimpleNamespace(
        option=SimpleNamespace(cuke_messages_ndjson=None, cuke_html=None, cuke_allure=None),
        workerinput={"workerid": "gw0"},
        rootpath=Path.cwd(),
        getini=lambda name: "",
    )
    request = FormatterRequest(name="worker-probe", command=("python",))
    monkeypatch.setattr("pytest_cuke.message_plugin.resolve_formatter_requests", lambda config: (request,))

    def fail_temporary_file_creation(*args: Any, **kwargs: Any) -> Any:
        raise AssertionError("xdist workers must not allocate local Messages files")

    monkeypatch.setattr("pytest_cuke.message_plugin.tempfile.mkstemp", fail_temporary_file_creation)

    plugin = MessagePlugin(config=config)

    assert plugin.is_xdist_worker is True
    assert plugin.is_messages_file_temp is False
    assert plugin.messages_file_path == Path(os.devnull)


def test_message_plugin_get_timestamp() -> None:
    ts = MessagePlugin.get_timestamp()
    assert ts.seconds > 0
    assert ts.nanos >= 0


def test_message_plugin_pytest_cuke_message_queue() -> None:
    config = MagicMock()
    config.rootpath = Path.cwd()
    config.option.cuke_messages_ndjson = "messages.ndjson"
    config.option.cuke_html = None

    plugin = MessagePlugin(config=config)
    assert plugin.is_disabled is False
    plugin.process_messages_io_queue = Queue()

    msg = Message(
        attachment=Attachment(
            body="tc-1",
            content_encoding=ContentEncoding.identity,
            media_type="text/plain",
        )
    )
    plugin.pytest_cuke_message(config, msg)

    assert not plugin.process_messages_io_queue.empty()
    item = plugin.process_messages_io_queue.get_nowait()
    assert "tc-1" in item


def test_validated_message_hook_and_ndjson_receive_the_same_accepted_order() -> None:
    observed: list[Message] = []
    config = SimpleNamespace(
        stash={},
        rootpath=Path.cwd(),
        option=SimpleNamespace(cuke_messages_ndjson="messages.ndjson", cuke_html=None, cuke_allure=None),
        getini=lambda name: "",
        hook=SimpleNamespace(pytest_cuke_message_validated=lambda *, config, message: observed.append(message)),
    )
    plugin = MessagePlugin(config=config)
    plugin.process_messages_io_queue = Queue()
    messages = [
        Message(
            attachment=Attachment(
                body="first",
                content_encoding=ContentEncoding.identity,
                media_type="text/plain",
            )
        ),
        Message(
            attachment=Attachment(
                body="second",
                content_encoding=ContentEncoding.identity,
                media_type="text/plain",
            )
        ),
    ]

    for message in messages:
        plugin.pytest_cuke_message(config, message)

    queued = [plugin.process_messages_io_queue.get_nowait() for _ in messages]
    assert observed == messages
    assert [json.loads(value)["attachment"]["body"] for value in queued] == ["first", "second"]


def test_validated_hook_and_ndjson_receive_the_same_exception_stack_trace() -> None:
    context = RunContext()
    scenario_run = context.start_scenario(
        nodeid="test.feature::Scenario",
        feature=Feature(name="Failure", uri="failure.feature"),
        scenario=Scenario(name="Failure"),
    )
    scenario_run.message_state.test_step_exception_traces = {"ts-1": "failure stack trace"}
    observed: list[Message] = []
    config = SimpleNamespace(
        stash={RunContext.STASH_KEY: context},
        rootpath=Path.cwd(),
        option=SimpleNamespace(cuke_messages_ndjson="messages.ndjson", cuke_html=None, cuke_allure=None),
        getini=lambda name: "",
        hook=SimpleNamespace(pytest_cuke_message_validated=lambda *, config, message: observed.append(message)),
    )
    plugin = MessagePlugin(config=config)
    plugin.process_messages_io_queue = Queue()
    events = [
        Message(test_run_started=TestRunStarted(timestamp=Timestamp(seconds=1, nanos=0))),
        Message(
            pickle=Pickle(
                id="p-1",
                uri="failure.feature",
                name="Failure",
                language="en",
                steps=[PickleStep(id="ps-1", ast_node_ids=["ast-1"], text="a failing step")],
                tags=[],
                ast_node_ids=["ast-1"],
            )
        ),
        Message(
            test_case=TestCase(
                id="tc-1",
                pickle_id="p-1",
                test_steps=[TestStep(id="ts-1", pickle_step_id="ps-1", step_definition_ids=[])],
            )
        ),
        Message(
            test_case_started=TestCaseStarted(
                attempt=0,
                id="tcs-1",
                test_case_id="tc-1",
                worker_id="master",
                timestamp=Timestamp(seconds=2, nanos=0),
            )
        ),
        Message(
            test_step_started=TestStepStarted(
                test_case_started_id="tcs-1",
                test_step_id="ts-1",
                timestamp=Timestamp(seconds=3, nanos=0),
            )
        ),
        Message(
            test_step_finished=TestStepFinished(
                test_case_started_id="tcs-1",
                test_step_id="ts-1",
                timestamp=Timestamp(seconds=4, nanos=0),
                test_step_result=TestStepResult(
                    duration=Duration(seconds=1, nanos=0),
                    status=Status.failed,
                    exception=ExceptionMessage(type="AssertionError", message="failure"),
                ),
            )
        ),
    ]

    for event in events:
        plugin.pytest_cuke_message(config, event)

    observed_payloads = [message_to_dict(event) for event in observed]
    queued_payloads = [json.loads(plugin.process_messages_io_queue.get_nowait()) for _ in events]
    assert observed_payloads == queued_payloads
    assert queued_payloads[-1]["testStepFinished"]["testStepResult"]["exception"]["stackTrace"] == (
        "failure stack trace"
    )


def test_message_plugin_rejects_invalid_envelope_before_both_sinks() -> None:
    observed: list[Message] = []
    config = SimpleNamespace(
        stash={},
        rootpath=Path.cwd(),
        option=SimpleNamespace(cuke_messages_ndjson="messages.ndjson", cuke_html=None, cuke_allure=None),
        getini=lambda name: "",
        hook=SimpleNamespace(pytest_cuke_message_validated=lambda *, config, message: observed.append(message)),
    )
    plugin = MessagePlugin(config=config)
    plugin.process_messages_io_queue = Queue()
    invalid = Message(
        test_run_started=TestRunStarted(timestamp=Timestamp(seconds=123, nanos=456)),
        test_run_finished=TestRunFinished(success=True, timestamp=Timestamp(seconds=124, nanos=0)),
    )

    plugin.pytest_cuke_message(config, invalid)

    assert observed == []
    assert plugin.process_messages_io_queue.empty()
    assert len(plugin.message_diagnostics) == 1
    diagnostic = plugin.message_diagnostics[0]
    assert diagnostic.code == "INVALID_PAYLOAD_SHAPE"
    assert diagnostic.severity == "error"
    assert diagnostic.position == 0
    assert diagnostic.payload_kind is None
    assert diagnostic.offending_ids == ()

    terminal_reporter = MagicMock()
    plugin.pytest_terminal_summary(terminal_reporter, ExitCode.TESTS_FAILED, config)
    diagnostic_line = terminal_reporter.write_line.call_args.args[0]
    assert diagnostic_line.startswith("PYTEST_CUKE_MESSAGE_DIAGNOSTIC={")
    assert json.loads(diagnostic_line.removeprefix("PYTEST_CUKE_MESSAGE_DIAGNOSTIC=")) == {
        "code": "INVALID_PAYLOAD_SHAPE",
        "severity": "error",
        "position": 0,
        "payload_kind": None,
        "message": diagnostic.message,
        "offending_ids": [],
        "instance_path": None,
    }


def test_message_plugin_meta_uses_the_installed_protocol_release() -> None:
    config = SimpleNamespace(
        option=SimpleNamespace(cuke_messages_ndjson="messages.ndjson", cuke_html=None, cuke_allure=None),
        rootpath=Path.cwd(),
        getini=lambda name: "",
        hook=None,
    )
    plugin = MessagePlugin(config=config)
    plugin.process_messages_io_queue = Queue()
    plugin.start_process_messages_thread = lambda: None
    config.pytest_cuke_id_generator = IdGenerator()
    config.hook = SimpleNamespace(
        pytest_cuke_message=lambda *, config, message: plugin.pytest_cuke_message(config, message),
        pytest_cuke_message_validated=lambda *, config, message: None,
    )

    _complete_hook_wrapper(plugin.pytest_sessionstart(SimpleNamespace(config=config)))

    envelopes = _drain_messages(plugin)
    envelope = envelopes[0]
    assert envelope["meta"]["protocolVersion"] == resolve_upstream_release()[1].protocol_version
    assert [next(iter(item)) for item in envelopes] == [
        "meta",
        "hook",
        "hook",
        "testRunStarted",
        "testRunHookStarted",
        "testRunHookFinished",
    ]


def test_late_message_diagnostics_are_written_after_terminal_summary() -> None:
    terminalreporter = MagicMock()
    config = SimpleNamespace(
        option=SimpleNamespace(cuke_messages_ndjson=None, cuke_html=None, cuke_allure=None),
        rootpath=Path.cwd(),
        getini=lambda name: "",
        hook=None,
        pluginmanager=SimpleNamespace(get_plugin=lambda name: terminalreporter),
    )
    plugin = MessagePlugin(config=config)
    plugin.message_diagnostics_summary_emitted = True
    diagnostic = MessageValidationDiagnostic(
        code="partial_stream",
        severity="error",
        position=0,
        payload_kind=None,
        message="worker transfer was incomplete",
    )
    next_diagnostic = MessageValidationDiagnostic(
        code="missing_worker_manifest",
        severity="error",
        position=1,
        payload_kind=None,
        message="worker manifest was not published",
    )

    plugin._report_message_diagnostics((diagnostic,))
    plugin._report_message_diagnostics((next_diagnostic,))

    assert [call.args[0] for call in terminalreporter.write_line.call_args_list] == [
        'PYTEST_CUKE_MESSAGE_DIAGNOSTIC={"code":"partial_stream","severity":"error","position":0,'
        '"payload_kind":null,"message":"worker transfer was incomplete","offending_ids":[],"instance_path":null}',
        'PYTEST_CUKE_MESSAGE_DIAGNOSTIC={"code":"missing_worker_manifest","severity":"error","position":1,'
        '"payload_kind":null,"message":"worker manifest was not published","offending_ids":[],"instance_path":null}',
    ]
    assert plugin.message_diagnostics == [diagnostic, next_diagnostic]


def test_invalid_stream_marks_terminal_message_and_pytest_run_failed() -> None:
    config = SimpleNamespace(
        option=SimpleNamespace(cuke_messages_ndjson="messages.ndjson", cuke_html=None, cuke_allure=None),
        rootpath=Path.cwd(),
        getini=lambda name: "",
        workeroutput={},
        hook=None,
    )
    plugin = MessagePlugin(config=config)
    plugin.process_messages_io_queue = Queue()
    plugin.finish_process_messages_thread = lambda: None
    plugin.start_process_messages_thread = lambda: None
    config.pytest_cuke_id_generator = IdGenerator()
    config.hook = SimpleNamespace(
        pytest_cuke_message=lambda *, config, message: plugin.pytest_cuke_message(config, message),
        pytest_cuke_message_validated=lambda *, config, message: None,
    )
    _complete_hook_wrapper(plugin.pytest_sessionstart(SimpleNamespace(config=config)))
    plugin.pytest_cuke_message(
        config,
        Message(
            test_run_started=TestRunStarted(timestamp=Timestamp(seconds=123, nanos=456)),
            test_run_finished=TestRunFinished(success=True, timestamp=Timestamp(seconds=124, nanos=0)),
        ),
    )
    session = SimpleNamespace(config=config, exitstatus=ExitCode.OK)

    _complete_hook_wrapper(message_session_finish_hook(plugin).pytest_sessionfinish(session, ExitCode.OK))

    envelopes = _drain_messages(plugin)
    terminal = [envelope["testRunFinished"] for envelope in envelopes if "testRunFinished" in envelope]
    assert len(terminal) == 1
    assert terminal[0]["success"] is False
    assert session.exitstatus is ExitCode.TESTS_FAILED
    assert [diagnostic.code for diagnostic in plugin.message_diagnostics] == ["INVALID_PAYLOAD_SHAPE"]


def test_message_plugin_pytest_cuke_attach() -> None:
    context = RunContext()
    scenario_run = context.start_scenario(
        nodeid="test.feature::Scenario",
        feature=Feature(name="Attachment", uri="attachment.feature"),
        scenario=Scenario(name="Attachment"),
    )
    scenario_run.message_state.test_case = TestCase(id="tc-1", pickle_id="p-1", test_steps=[])
    scenario_run.message_state.test_case_started = TestCaseStarted(
        attempt=0,
        id="tcs-1",
        test_case_id="tc-1",
        worker_id="master",
        timestamp=Timestamp(seconds=1, nanos=0),
    )
    config = SimpleNamespace(
        stash={RunContext.STASH_KEY: context},
        rootpath=Path.cwd(),
        option=SimpleNamespace(cuke_messages_ndjson="messages.ndjson", cuke_html=None, cuke_allure=None),
        getini=lambda name: "",
        hook=MagicMock(),
    )

    plugin = MessagePlugin(config=config)

    request = SimpleNamespace(config=config)

    plugin.pytest_cuke_attach(request, context, "hello attachment", "text/plain", "file.txt")
    config.hook.pytest_cuke_message.assert_called_once()


def test_tolerated_step_error_keeps_later_message_steps_executable() -> None:
    failed_step = Step(name="tolerated failure", keyword="When ")
    later_step = Step(name="later real step", keyword="Then ")
    scenario = Scenario(name="Tolerated", steps=(failed_step, later_step))
    feature = Feature(name="Tolerant messages", uri="tolerant.feature")
    context = RunContext()
    scenario_run = context.start_scenario(nodeid="tolerant.feature::Tolerated", feature=feature, scenario=scenario)
    failed_test_step = TestStep(id="ts-failed", pickle_step_id="ps-failed", step_definition_ids=[])
    later_test_step = TestStep(id="ts-later", pickle_step_id="ps-later", step_definition_ids=[])
    scenario_run.message_state.test_case_started = TestCaseStarted(
        attempt=0,
        id="attempt-1",
        test_case_id="tc-1",
        worker_id="master",
        timestamp=Timestamp(seconds=1, nanos=0),
    )
    scenario_run.message_state.test_steps = [failed_test_step, later_test_step]
    scenario_run.message_state.test_steps_by_identity = {
        id(failed_step): failed_test_step,
        id(later_step): later_test_step,
    }
    config = SimpleNamespace(
        stash={RunContext.STASH_KEY: context},
        rootpath=Path.cwd(),
        option=SimpleNamespace(cuke_messages_ndjson="messages.ndjson", cuke_html=None, cuke_allure=None),
        getini=lambda name: "",
        hook=MagicMock(),
    )
    plugin = MessagePlugin(config=config)

    context.start_step(failed_step)
    plugin.pytest_cuke_step_error(
        request=SimpleNamespace(config=config),
        run=context,
        step_func=lambda: None,
        step_func_args={},
        exception=AssertionError("tolerated failure"),
        step_definition=object(),
        tolerated=True,
    )

    assert scenario_run.message_state.finished_test_step_ids == {"ts-failed"}
    assert len(config.hook.pytest_cuke_message.call_args_list) == 2


def test_bypassed_steps_emit_finished_messages_without_user_step_hooks() -> None:
    step = Step(name="pending step", keyword="When ")
    scenario = Scenario(name="Pending", steps=(step,))
    feature = Feature(name="Pending messages", uri="pending.feature")
    context = RunContext()
    scenario_run = context.start_scenario(nodeid="pending.feature::Pending", feature=feature, scenario=scenario)
    test_step = TestStep(id="ts-pending", pickle_step_id="ps-pending", step_definition_ids=[])
    scenario_run.message_state.test_case_started = TestCaseStarted(
        attempt=0,
        id="attempt-pending",
        test_case_id="tc-pending",
        worker_id="master",
        timestamp=Timestamp(seconds=1, nanos=0),
    )
    scenario_run.message_state.test_steps = [test_step]
    scenario_run.message_state.test_steps_by_identity = {id(step): test_step}
    context.start_step(step)
    config = SimpleNamespace(
        stash={RunContext.STASH_KEY: context},
        rootpath=Path.cwd(),
        option=SimpleNamespace(cuke_messages_ndjson="messages.ndjson", cuke_html=None, cuke_allure=None),
        getini=lambda name: "",
        hook=MagicMock(),
    )
    plugin = MessagePlugin(config=config)

    plugin.pytest_cuke_step_bypassed(
        request=SimpleNamespace(config=config),
        run=context,
        step_definition=object(),
        status="passed",
    )

    messages = [call.kwargs["message"] for call in config.hook.pytest_cuke_message.call_args_list]
    assert [message.test_step_started.test_step_id for message in messages if message.test_step_started] == [
        "ts-pending"
    ]
    finished = [message.test_step_finished for message in messages if message.test_step_finished]
    assert len(finished) == 1
    assert finished[0].test_case_started_id == "attempt-pending"
    assert finished[0].test_step_result.status == Status.passed
    assert scenario_run.message_state.finished_test_step_ids == {"ts-pending"}
    assert scenario_run.message_state.active_test_step_id is None


def test_message_plugin_ignores_ordinary_pytest_tests() -> None:
    config = MagicMock()
    config.rootpath = Path.cwd()
    config.option.cuke_messages_ndjson = "messages.ndjson"
    config.option.cuke_html = None

    plugin = MessagePlugin(config=config)
    request = MagicMock()
    item = MagicMock()
    item.fixturenames = ["pytestconfig"]
    item._request = request

    list(plugin.pytest_runtest_setup(item))

    request.getfixturevalue.assert_not_called()
