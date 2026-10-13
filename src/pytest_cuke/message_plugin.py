"""Cucumber Messages streaming and HTML report plugin."""

from __future__ import annotations

import json
import os
import re
import sys
import tempfile
import traceback
from base64 import b64encode
from contextlib import suppress
from inspect import getfile, getsourcelines
from io import BufferedIOBase, TextIOBase
from pathlib import Path
from platform import machine, processor, system, version
from queue import Empty, Queue
from threading import Event, Lock, Thread
from time import monotonic, sleep, time_ns
from typing import TYPE_CHECKING, Any, ClassVar, Literal, cast

import chevron  # type: ignore[import-untyped]  # chevron ships no type information
import pytest
from attr import attrib, attrs
from ci_environment import detect_ci_environment
from filelock import FileLock
from pytest import ExitCode, hookimpl

from pytest_cuke.compatibility.path import relpath
from pytest_cuke.compatibility.pytest import (
    Config,
    FixtureDef,
    FixtureRequest,
    Parser,
    get_config_root_path,
    get_metafunc_call_arg,
)
from pytest_cuke.formatter_catalog import resolve_formatter_requests
from pytest_cuke.formatter_runtime import FormatterSession
from pytest_cuke.ide_bindings import (
    IDE_BINDING_WORKER_OUTPUT_KEY,
    IDE_DIAGNOSTIC_MEDIA_TYPE,
    IDE_LAUNCH_MEDIA_TYPE,
    IDE_STEP_BINDING_MEDIA_TYPE,
    IdeBindingCollection,
    definition_reference,
    match_arguments,
    source_identity,
)
from pytest_cuke.message_schema_sync import resolve_upstream_release
from pytest_cuke.model.execution_steps import execution_steps
from pytest_cuke.model.message_consolidation import (
    MessageFragment,
    consolidate_message_fragments,
    namespace_envelope_ids,
)
from pytest_cuke.model.message_converter import feature_to_gherkin_document, scenario_pickle_id, scenario_to_pickle
from pytest_cuke.model.message_stream_validation import MessageStreamValidator
from pytest_cuke.model.message_transport import MessageEnvelopeView, ValidatedMessageTransport
from pytest_cuke.model.message_types import (
    Attachment,
    Ci,
    ContentEncoding,
    Duration,
    ExceptionMessage,
    Hook,
    HookType,
    Location,
    Meta,
    ParameterType,
    Product,
    Source,
    SourceMediaType,
    SourceReference,
    Status,
    TestCase,
    TestCaseFinished,
    TestCaseStarted,
    TestRunFinished,
    TestRunHookFinished,
    TestRunHookStarted,
    TestRunStarted,
    TestStep,
    TestStepFinished,
    TestStepResult,
    TestStepStarted,
    Timestamp,
    UndefinedParameterType,
    message_from_dict,
    message_to_dict,
)
from pytest_cuke.model.message_types import Envelope as Message
from pytest_cuke.model.message_validation import (
    MessageValidationCode,
    MessageValidationError,
    integration_diagnostic,
    message_diagnostic_to_dict,
)
from pytest_cuke.model.message_worker_transport import (
    MessageBatch,
    MessageBatcher,
    WorkerMessageReceiver,
)
from pytest_cuke.model.run_access import get_run_context
from pytest_cuke.model.session_run import RunContext
from pytest_cuke.npm_resource import check_npm, check_npm_package, find_resource
from pytest_cuke.packaging import get_distribution_version
from pytest_cuke.scenario_locator import ScenarioLocatorFilterMixin
from pytest_cuke.steps import Matcher
from pytest_cuke.utils import PytestBDDIdGeneratorHandler, deepattrgetter

if TYPE_CHECKING:
    from collections.abc import Callable, Generator, Iterable

    from cucumber_expressions.parameter_type_registry import ParameterTypeRegistry
    from pytest import Session

    from pytest_cuke.compatibility.pytest import Item, Metafunc, TestReport
    from pytest_cuke.formatter_api import FormatterRequest
    from pytest_cuke.model import Step
    from pytest_cuke.model.message_validation import MessageValidationDiagnostic

_WORKER_MESSAGE_BATCH_KEY = "pytest_cuke_message_batch"
_WORKER_MESSAGE_OUTPUT_KEY = "pytest_cuke_message_transport"


def _set_test_run_success(envelopes: list[dict[str, Any]], success: bool) -> None:
    for envelope in reversed(envelopes):
        test_run_finished = envelope.get("testRunFinished")
        if isinstance(test_run_finished, dict):
            test_run_finished["success"] = success
            return


def _write_message_stream(path: Path, envelopes: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    handle, temporary_path = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(handle, "w", encoding="utf-8", newline="\n") as stream:
            for envelope in envelopes:
                stream.write(json.dumps(envelope, ensure_ascii=False, separators=(",", ":")))
                stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary_path, path)
    except Exception:
        with suppress(OSError):
            os.unlink(temporary_path)
        raise


def _worker_id_from_config(config: Config) -> str | None:
    worker_input = getattr(config, "workerinput", None)
    if not isinstance(worker_input, dict):
        return None
    for key in ("workerid", "gateway", "gateway_id"):
        worker_id = worker_input.get(key)
        if isinstance(worker_id, str) and worker_id:
            return worker_id
    return None


def _xdist_controller_requested(config: Config) -> bool:
    option = getattr(config, "option", None)
    numprocesses = getattr(option, "numprocesses", None)
    if isinstance(numprocesses, int):
        if numprocesses > 0:
            return True
    elif isinstance(numprocesses, str) and numprocesses.strip().lower() not in {"", "0", "none"}:
        return True
    transactions = getattr(option, "tx", None)
    return isinstance(transactions, (list, tuple)) and bool(transactions)


@attrs(frozen=True, slots=True)
class PendingTestStepFinish:
    test_case_started: TestCaseStarted = attrib()
    test_step: TestStep = attrib()
    start_timestamp: Timestamp = attrib()
    finish_timestamp: Timestamp = attrib()
    status: Status = attrib()
    message: str | None = attrib(default=None)
    exception: ExceptionMessage | None = attrib(default=None)
    exception_stack_trace: str | None = attrib(default=None)


@attrs(eq=False)
class MessagePlugin:
    # These registries deduplicate messages emitted once per pytest session. They must not be
    # ClassVars: in-process pytest runs (e.g. pytester) share one process, and a process-global
    # id-keyed registry leaks across sessions. A freed hook function's address can be reused by
    # the next session's function, so the "already emitted" check silently skips a message (#232).
    config: Config = attrib()
    formatter_requests: tuple[FormatterRequest, ...] = attrib(factory=tuple)
    formatter_session: FormatterSession | None = attrib(default=None)
    message_transport: ValidatedMessageTransport | None = attrib(default=None)
    process_messages_error: Exception | None = attrib(default=None)
    process_messages_error_reported: bool = attrib(default=False)
    process_messages_closed: bool = attrib(default=False)
    process_messages_lock: Any = attrib(factory=Lock)
    test_cases_by_nodeid: dict[str, TestCase] = attrib(factory=dict)
    test_case_hook_steps_by_nodeid: dict[str, dict[str, TestStep]] = attrib(factory=dict)
    parameter_type_registry: set[int] = attrib(factory=set)
    hook_registry: set[int] = attrib(factory=set)
    ide_bindings: IdeBindingCollection = attrib(factory=IdeBindingCollection)
    test_run_started_id: str | None = attrib(default=None)
    after_test_run_hook_id: str | None = attrib(default=None)
    test_run_hook_failed: bool = attrib(default=False)
    message_diagnostics: list[Any] = attrib(factory=list)
    message_diagnostics_summary_emitted: bool = attrib(default=False)
    message_diagnostics_reported_after_summary: int = attrib(default=0)
    accepted_message_payloads: list[dict[str, Any]] = attrib(factory=list)
    is_xdist_worker: bool = attrib(default=False)
    is_xdist_controller: bool = attrib(default=False)
    xdist_worker_id: str | None = attrib(default=None)
    worker_message_batcher: MessageBatcher | None = attrib(default=None)
    worker_message_receiver: WorkerMessageReceiver | None = attrib(default=None)
    npm_formatter_package: ClassVar[str] = "@cucumber/html-formatter"

    def _configured_output(self, name: str) -> str | None:
        value = getattr(self.config.option, name, None)
        if isinstance(value, str):
            return value
        ini_value = self.config.getini(name)
        return ini_value if isinstance(ini_value, str) and ini_value else None

    def _active_scenario_run(self) -> Any:
        run_context = get_run_context(self.config)
        return run_context.active_scenario_run if run_context is not None else None

    def _get_scenario_state(self, name: str, default: Any) -> Any:
        scenario_run = self._active_scenario_run()
        message_state = scenario_run.message_state if scenario_run is not None else None
        return getattr(message_state, name, default) if message_state is not None else default

    def _set_scenario_state(self, name: str, value: Any) -> None:
        scenario_run = self._active_scenario_run()
        if scenario_run is not None:
            setattr(scenario_run.message_state, name, value)

    @property
    def current_test_case(self) -> TestCase | None:
        return cast("TestCase | None", self._get_scenario_state("test_case", None))

    @current_test_case.setter
    def current_test_case(self, value: TestCase | None) -> None:
        self._set_scenario_state("test_case", value)

    @property
    def current_test_case_step_id_to_step_mapping(self) -> dict[int, TestStep]:
        return cast("dict[int, TestStep]", self._get_scenario_state("test_steps_by_identity", {}))

    @current_test_case_step_id_to_step_mapping.setter
    def current_test_case_step_id_to_step_mapping(self, value: dict[int, TestStep]) -> None:
        self._set_scenario_state("test_steps_by_identity", value)

    @property
    def current_test_case_step_order(self) -> list[TestStep]:
        return cast("list[TestStep]", self._get_scenario_state("test_steps", []))

    @current_test_case_step_order.setter
    def current_test_case_step_order(self, value: list[TestStep]) -> None:
        self._set_scenario_state("test_steps", value)

    @property
    def current_finished_test_step_ids(self) -> set[str]:
        return cast("set[str]", self._get_scenario_state("finished_test_step_ids", set()))

    @current_finished_test_step_ids.setter
    def current_finished_test_step_ids(self, value: set[str]) -> None:
        self._set_scenario_state("finished_test_step_ids", value)

    @property
    def current_test_step_start_timestamps(self) -> dict[str, Timestamp]:
        return cast("dict[str, Timestamp]", self._get_scenario_state("test_step_start_timestamps", {}))

    @current_test_step_start_timestamps.setter
    def current_test_step_start_timestamps(self, value: dict[str, Timestamp]) -> None:
        self._set_scenario_state("test_step_start_timestamps", value)

    @property
    def current_active_test_step_id(self) -> str | None:
        return cast("str | None", self._get_scenario_state("active_test_step_id", None))

    @current_active_test_step_id.setter
    def current_active_test_step_id(self, value: str | None) -> None:
        self._set_scenario_state("active_test_step_id", value)

    @property
    def current_test_step_exception_traces(self) -> dict[str, str]:
        return cast("dict[str, str]", self._get_scenario_state("test_step_exception_traces", {}))

    @current_test_step_exception_traces.setter
    def current_test_step_exception_traces(self, value: dict[str, str]) -> None:
        self._set_scenario_state("test_step_exception_traces", value)

    @property
    def pending_test_step_finish(self) -> PendingTestStepFinish | None:
        return cast("PendingTestStepFinish | None", self._get_scenario_state("pending_test_step_finish", None))

    @pending_test_step_finish.setter
    def pending_test_step_finish(self, value: PendingTestStepFinish | None) -> None:
        self._set_scenario_state("pending_test_step_finish", value)

    @property
    def current_test_case_start(self) -> TestCaseStarted | None:
        return cast("TestCaseStarted | None", self._get_scenario_state("test_case_started", None))

    @current_test_case_start.setter
    def current_test_case_start(self, value: TestCaseStarted | None) -> None:
        self._set_scenario_state("test_case_started", value)

    def __attrs_post_init__(self) -> None:
        self.formatter_requests = resolve_formatter_requests(self.config)
        messages_path = self._configured_output("cuke_messages_ndjson")
        html_path = self._configured_output("cuke_html")
        allure_path = self._configured_output("cuke_allure")
        self.is_disabled = all(
            [
                messages_path is None,
                html_path is None,
                allure_path is None,
                not self.formatter_requests,
            ]
        )

        if self.is_disabled:
            return

        self.xdist_worker_id = _worker_id_from_config(self.config)
        self.is_xdist_worker = self.xdist_worker_id is not None
        self.is_xdist_controller = not self.is_xdist_worker and _xdist_controller_requested(self.config)
        if self.is_xdist_worker:
            self.worker_message_batcher = MessageBatcher(cast("str", self.xdist_worker_id))
        elif self.is_xdist_controller:
            self.worker_message_receiver = WorkerMessageReceiver()

        if self.is_xdist_worker:
            # Workers send accepted envelopes through xdist reports and their
            # completion manifest. They never write or convert a local stream,
            # so allocating a per-worker tempfile only creates an artifact that
            # can be stranded if the worker exits abruptly.
            self.is_messages_file_temp = False
            self.messages_file_path = Path(os.devnull)
        elif messages_path is None:
            self.is_messages_file_temp = True
            handle, messages_file_path_raw = tempfile.mkstemp()
            os.close(handle)
            self.messages_file_path = Path(messages_file_path_raw)
        else:
            self.is_messages_file_temp = False
            self.messages_file_path = Path(messages_path)

        self.message_transport = ValidatedMessageTransport()
        if not self.is_xdist_worker:
            self.message_transport.add_sink(self._deliver_validated_message, name="pytest_cuke_message_validated")
        self.message_transport.add_sink(self._capture_accepted_message, name="Cucumber Messages memory fragment")
        self.message_transport.add_sink(self._queue_validated_message, name="Cucumber Messages NDJSON writer")

        if self.formatter_requests and not self.is_xdist_worker:
            self.formatter_session = FormatterSession(self.config, self.formatter_requests)
            self.config.pluginmanager.register(self.formatter_session, name="pytest_cuke_formatter_session")

        if html_path is not None:
            self.check_npm_and_cucumber_packages()

    def start_process_messages_thread(self) -> None:
        self.process_messages_io_queue: Queue[str] = Queue()
        self.process_messages_stop_event = Event()
        with self.process_messages_lock:
            self.process_messages_error = None
            self.process_messages_error_reported = False
            self.process_messages_closed = False
        if self.is_xdist_worker:
            return
        self.process_messages_thread = Thread(
            target=self._process_messages_safely,
            daemon=True,
        )
        self.process_messages_thread.start()
        sleep(0)

    def finish_process_messages_thread(self) -> None:
        with self.process_messages_lock:
            self.process_messages_closed = True
        self.process_messages_stop_event.set()
        self.process_messages_thread.join()
        with self.process_messages_lock:
            if self.process_messages_error is not None:
                self._discard_queued_messages_locked()
        self.process_messages_io_queue.join()

    def flush_process_messages_thread(self) -> None:
        with self.process_messages_lock:
            if self.process_messages_error is not None:
                self._discard_queued_messages_locked()
                return
        self.process_messages_io_queue.join()

    def _discard_queued_messages_locked(self) -> None:
        while True:
            try:
                self.process_messages_io_queue.get_nowait()
            except Empty:
                break
            else:
                self.process_messages_io_queue.task_done()

    def _process_messages_safely(self) -> None:
        try:
            self.process_messages(
                self.process_messages_io_queue,
                self.process_messages_stop_event,
                self.messages_file_path,
            )
        except Exception as error:
            with self.process_messages_lock:
                self.process_messages_error = error
                self._discard_queued_messages_locked()

    @staticmethod
    def process_messages(queue: Queue[str], stop_event: Event, messages_file_path: str | Path) -> None:
        with tempfile.TemporaryDirectory() as tmpdirname:
            last_enter = False
            while not (stop_event.is_set() and last_enter):  # give one more enter to take all left messages
                if stop_event.is_set():
                    last_enter = True

                if queue.empty():
                    sleep(0.01)
                    continue

                lock_file = os.path.join(tmpdirname, f"{messages_file_path}.lock")
                with (
                    FileLock(lock_file),
                    Path(messages_file_path).open(mode="at+", buffering=1, encoding="utf-8") as f,
                ):
                    lines = []
                    while not queue.empty():
                        try:
                            message_json = queue.get(timeout=1)
                        except Empty:
                            sleep(0)
                            continue

                        try:
                            payload = json.loads(message_json)
                            validation_payload = json.loads(message_json)
                            for event_key in ("testStepFinished", "testRunFinished"):
                                event = validation_payload.get(event_key)
                                if not isinstance(event, dict):
                                    continue
                                result = event.get("testStepResult") if event_key == "testStepFinished" else event
                                if not isinstance(result, dict):
                                    continue
                                exception = result.get("exception")
                                if isinstance(exception, dict) and "stackTrace" in exception:
                                    stack_trace = exception.pop("stackTrace")
                                    if not isinstance(stack_trace, str):
                                        raise ValueError("exception stackTrace must be a string")
                            message_from_dict(validation_payload, Message)
                            lines.append(f"{json.dumps(payload, ensure_ascii=False)}\n")
                        finally:
                            queue.task_done()
                        sleep(0)
                    f.writelines(lines)
                    f.flush()

    @staticmethod
    def get_timestamp() -> Timestamp:
        timestamp = time_ns()
        test_run_started_seconds = timestamp // 10**9
        test_run_started_nanos = timestamp - test_run_started_seconds * 10**9
        return Timestamp(seconds=test_run_started_seconds, nanos=test_run_started_nanos)

    @staticmethod
    def add_options(parser: Parser) -> None:
        """Add canonical Cucumber report options."""
        group = parser.getgroup("cuke", "Cucumber NDJSON")
        group.addoption(
            "--cuke-messages-ndjson",
            action="store",
            dest="cuke_messages_ndjson",
            metavar="path",
            default=None,
            help="messages ndjson report file at given path.",
        )
        parser.addini("cuke_messages_ndjson", "Cucumber Messages NDJSON report path.", default="", type="string")
        group = parser.getgroup("cuke", "Cucumber HTML")
        group.addoption(
            "--cuke-html",
            action="store",
            dest="cuke_html",
            metavar="path",
            default=None,
            help="cucumber html report at given path.",
        )
        parser.addini("cuke_html", "Cucumber HTML report path.", default="", type="string")
        group = parser.getgroup("cuke", "Allure reporting")
        group.addoption(
            "--cuke-allure",
            action="store",
            nargs="?",
            const="allure-results",
            dest="cuke_allure",
            metavar="dir",
            default=None,
            help="Allure result directory (default: allure-results); write native results during pytest.",
        )
        parser.addini("cuke_allure", "Allure result directory for native pytest reporting.", default="", type="string")
        group.addoption(
            "--cuke-allure-messages-in",
            action="store",
            dest="cuke_allure_messages_in",
            metavar="path",
            default=None,
            help="convert a saved Cucumber Messages NDJSON stream without collecting tests.",
        )
        parser.addini(
            "cuke_allure_messages_in",
            "Saved Cucumber Messages NDJSON input for pytest Allure conversion.",
            default="",
            type="string",
        )
        group = parser.getgroup("cuke", "Cucumber pretty output")
        group.addoption(
            "--cuke-pretty",
            action="store_true",
            dest="cuke_pretty",
            default=None,
            help="render live Cucumber feature and step output with the official pretty formatter.",
        )
        parser.addini(
            "cuke_pretty",
            "Render live Cucumber feature and step output with the official pretty formatter.",
            default=False,
            type="bool",
        )

    def generate_html_report(self) -> None:
        if self.is_disabled:
            return

        html_path = self._configured_output("cuke_html")
        if html_path is None:
            return

        script_content = ""
        for candidate in (Path("dist") / "main.js", Path("main.js"), Path("dist") / "cucumber-html.js"):
            found = list(find_resource(self.npm_formatter_package, str(candidate)))
            if found:
                script_content = Path(found[0]).read_text(encoding="utf-8")
                break

        css_content = ""
        for candidate in (Path("dist") / "main.css", Path("main.css"), Path("dist") / "cucumber-html.css"):
            found = list(find_resource(self.npm_formatter_package, str(candidate)))
            if found:
                css_content = Path(found[0]).read_text(encoding="utf-8")
                break

        template = (
            "<!DOCTYPE html>\n"
            "<html>\n"
            "<head>\n"
            '    <meta charset="UTF-8">\n'
            "    <style>{{&css}}</style>\n"
            "</head>\n"
            "<body>\n"
            "    <script>{{&script}}</script>\n"
            '    <div id="content"></div>\n'
            "    <script>\n"
            "        window.CUCUMBER_MESSAGES = [{{&messages}}];\n"
            "    </script>\n"
            "</body>\n"
            "</html>\n"
        )
        for candidate in (
            Path("src") / "index.mustache.html",
            Path("index.mustache.html"),
            Path("dist") / "index.mustache.html",
            Path("templates") / "index.mustache.html",
        ):
            found = list(find_resource(self.npm_formatter_package, str(candidate)))
            if found:
                raw = Path(found[0]).read_text(encoding="utf-8")
                template = re.sub(r"\{\{", "{{&", raw)
                break

        messages = ""
        if self.messages_file_path and self.messages_file_path.exists():
            with self.messages_file_path.open(mode="r", encoding="utf-8") as f:
                messages = ",".join(f.readlines())

        html_out_path = Path(html_path)
        html_out_path.parent.mkdir(parents=True, exist_ok=True)
        html_out_path.write_text(
            chevron.render(
                template,
                {
                    "css": css_content,
                    "script": script_content,
                    "messages": messages,
                },
            ),
            encoding="utf-8",
        )

    @staticmethod
    def build_source(feature: Feature) -> Source | None:
        filename = feature.filename
        if filename is None:
            return None
        path = Path(filename)
        try:
            data = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            return None
        media_type = Mimetype.markdown.value if path.name.endswith(".md") else Mimetype.gherkin_plain.value
        return Source(uri=feature.uri or path.as_posix(), data=data, media_type=media_type)

    @staticmethod
    def build_pickle_id(feature: Feature, scenario: Scenario) -> str:
        uri = feature.uri or feature.filename or "feature"
        scenario_ref = scenario.id or f"{scenario.name}-{scenario.line}"
        return f"{uri}:{scenario_ref}"

    @hookimpl(hookwrapper=True)
    def pytest_generate_tests(self, metafunc: Metafunc) -> Generator[None, None, None]:
        yield
        if self.is_disabled:
            return

        if all(
            [
                "feature" in metafunc.fixturenames,
                "scenario" in metafunc.fixturenames,
                metafunc._calls,
            ]
        ):
            config = metafunc.config

            feature_registry: set[str] = set()
            pickle_registry: set[int] = set()
            for call in metafunc._calls:
                feature = get_metafunc_call_arg(call, "feature")
                scenario = get_metafunc_call_arg(call, "scenario")
                feature_is_set = feature is not None and is_set(feature)
                scenario_is_set = scenario is not None and is_set(scenario)

                if feature_is_set and feature.uri not in feature_registry:
                    feature_registry.add(feature.uri)
                    if feature.source_content is not None:
                        config.hook.pytest_cuke_message(
                            config=config,
                            message=Message(
                                source=Source(
                                    uri=feature.uri or feature.filename or "",
                                    data=feature.source_content,
                                    media_type=cast(
                                        "SourceMediaType",
                                        feature.source_media_type or "text/x.cucumber.gherkin+plain",
                                    ),
                                )
                            ),
                        )
                    config.hook.pytest_cuke_message(
                        config=config,
                        message=Message(
                            gherkin_document=feature_to_gherkin_document(
                                feature, uri=feature.uri or feature.filename or feature.name
                            )
                        ),
                    )
                if scenario_is_set and id(scenario) not in pickle_registry:
                    pickle_registry.add(id(scenario))
                    feature_uri = feature.uri or feature.filename or feature.name if feature_is_set else ""
                    config.hook.pytest_cuke_message(
                        config=config,
                        message=Message(
                            pickle=scenario_to_pickle(
                                scenario,
                                uri=feature_uri,
                                default_id=f"{feature_uri}#{call.id}",
                                feature=feature if feature_is_set else None,
                            )
                        ),
                    )

    def pytest_cuke_message(self, config: Config, message: Message) -> None:
        if self.is_disabled:
            return

        if self.message_transport is None:
            return
        message = self._with_exception_stack_trace(message)
        try:
            sink_diagnostics = self.message_transport.emit(message)
        except MessageValidationError as error:
            self._report_message_diagnostics(error.diagnostics)
            return

        self._report_message_diagnostics(sink_diagnostics)

    def _capture_accepted_message(self, message: Message) -> None:
        self.accepted_message_payloads.append(message_to_dict(message))

    def _deliver_validated_message(self, message: Message) -> None:
        self.config.hook.pytest_cuke_message_validated(config=self.config, message=message)

    @staticmethod
    def _worker_id_for_node(node: Any) -> str | None:
        gateway = getattr(node, "gateway", None)
        worker_id = getattr(gateway, "id", None)
        if isinstance(worker_id, str) and worker_id:
            return worker_id
        worker_input = getattr(node, "workerinput", None)
        worker_id = worker_input.get("workerid") if isinstance(worker_input, dict) else None
        return worker_id if isinstance(worker_id, str) and worker_id else None

    def _take_worker_message_batch(self) -> dict[str, Any] | None:
        if self.worker_message_batcher is None or not hasattr(self, "process_messages_io_queue"):
            return None
        envelopes: list[dict[str, Any]] = []
        while True:
            try:
                raw_message = self.process_messages_io_queue.get_nowait()
            except Empty:
                break
            else:
                try:
                    payload = json.loads(raw_message)
                    if isinstance(payload, dict):
                        envelopes.append(payload)
                finally:
                    self.process_messages_io_queue.task_done()
        if not envelopes:
            return None
        return self.worker_message_batcher.make_batch(envelopes).to_payload()

    def _receive_worker_message_batch(self, payload: Any) -> None:
        if not isinstance(payload, dict) or self.worker_message_receiver is None:
            return
        try:
            batch = MessageBatch.from_payload(payload)
        except ValueError:
            self.worker_message_receiver.receive_batch(payload)
            return
        if self.worker_message_receiver.receive_batch(batch.to_payload()):
            self._publish_worker_message_batch(batch)

    def _publish_worker_message_batch(self, batch: MessageBatch) -> None:
        live_batch = {
            "worker_id": batch.worker_id,
            "sequence": batch.sequence,
            "envelopes": [namespace_envelope_ids(envelope, worker_id=batch.worker_id) for envelope in batch.envelopes],
            "complete": False,
        }
        try:
            self.config.hook.pytest_cuke_message_batch(config=self.config, batch=live_batch)
        except Exception as error:
            if self.message_transport is not None:
                diagnostic = self.message_transport.record_sink_failure("pytest_cuke_message_batch", error)
                self._report_message_diagnostics((diagnostic,))

    @hookimpl(optionalhook=True, hookwrapper=True, tryfirst=True)
    def pytest_report_to_serializable(self, config: Config, report: Any) -> Generator[None, Any, Any]:
        del config
        batch = self._take_worker_message_batch() if self.is_xdist_worker else None
        if batch is not None:
            setattr(report, _WORKER_MESSAGE_BATCH_KEY, batch)
        outcome = yield
        serialized = outcome.get_result()
        if batch is not None and isinstance(serialized, dict):
            serialized[_WORKER_MESSAGE_BATCH_KEY] = batch

    @hookimpl(optionalhook=True, hookwrapper=True, tryfirst=True)
    def pytest_report_from_serializable(
        self,
        config: Config,
        data: dict[str, Any],
    ) -> Generator[None, Any, Any]:
        batch = data.pop(_WORKER_MESSAGE_BATCH_KEY, None) if self.is_xdist_controller else None
        if batch is not None:
            self._receive_worker_message_batch(batch)
        yield

    @hookimpl(optionalhook=True)
    def pytest_configure_node(self, node: Any) -> None:
        if self.is_disabled or not self.is_xdist_controller or self.worker_message_receiver is None:
            return
        worker_id = self._worker_id_for_node(node)
        if worker_id is not None:
            self.worker_message_receiver.register_expected_worker(worker_id)

    def _with_exception_stack_trace(self, message: Message) -> Message:
        finished_step = message.test_step_finished
        if finished_step is None or finished_step.test_step_result.exception is None:
            return message

        stack_trace = self.current_test_step_exception_traces.get(finished_step.test_step_id)
        if stack_trace is None:
            run_context = get_run_context(self.config)
            if run_context is not None:
                for scenario_run in run_context.scenario_runs_by_nodeid.values():
                    message_state = scenario_run.message_state
                    test_case_started = message_state.test_case_started
                    if test_case_started is not None and test_case_started.id == finished_step.test_case_started_id:
                        stack_trace = message_state.test_step_exception_traces.get(finished_step.test_step_id)
                        break
        if stack_trace is None:
            return message

        return cast(
            "Message",
            MessageEnvelopeView(message, exception_stack_trace=stack_trace),
        )

    def _queue_validated_message(self, message: Message) -> None:
        message_data = message_to_dict(message)
        message_json = json.dumps(message_data, ensure_ascii=False)
        with self.process_messages_lock:
            if self.process_messages_closed:
                raise RuntimeError("Cucumber Messages writer has already stopped")
            if self.process_messages_error is not None:
                raise RuntimeError(
                    "Cucumber Messages writer has failed: "
                    f"{type(self.process_messages_error).__name__}: {self.process_messages_error}"
                )
            self.process_messages_io_queue.put_nowait(message_json)

    def _report_message_diagnostics(self, diagnostics: Iterable[MessageValidationDiagnostic]) -> None:
        pending = tuple(diagnostics)
        if not pending:
            return
        self.message_diagnostics.extend(pending)
        if not self.message_diagnostics_summary_emitted:
            return
        terminalreporter = self.config.pluginmanager.get_plugin("terminalreporter")
        if terminalreporter is not None:
            first_unreported = self.message_diagnostics_reported_after_summary
            pending_after_summary = self.message_diagnostics[first_unreported:]
            self._write_message_diagnostics(terminalreporter, pending_after_summary)
            self.message_diagnostics_reported_after_summary = len(self.message_diagnostics)

    @staticmethod
    def _write_message_diagnostics(terminalreporter: Any, diagnostics: Iterable[MessageValidationDiagnostic]) -> None:
        for diagnostic in diagnostics:
            payload = message_diagnostic_to_dict(diagnostic)
            terminalreporter.write_line(
                "PYTEST_CUKE_MESSAGE_DIAGNOSTIC=" + json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
            )

    @hookimpl(trylast=True)
    def pytest_terminal_summary(self, terminalreporter: Any, exitstatus: int | ExitCode, config: Config) -> None:
        del exitstatus, config
        self.message_diagnostics_summary_emitted = True
        self._write_message_diagnostics(terminalreporter, self.message_diagnostics)
        self.message_diagnostics.clear()
        self.message_diagnostics_reported_after_summary = 0

    def _emit_test_run_hook_definition(self, config: Config, phase: Literal["before", "after"]) -> str:
        generator = cast("PytestBDDIdGeneratorHandler", config).pytest_cuke_id_generator
        is_before = phase == "before"
        hook_id = generator.get_next_id()
        hook_name = "pytest session start" if is_before else "pytest session finish"
        hook_type = HookType.before_test_run if is_before else HookType.after_test_run
        hook_handler = config.hook
        hook_handler.pytest_cuke_message(
            config=config,
            message=Message(
                hook=Hook(
                    id=hook_id,
                    name=hook_name,
                    type=hook_type,
                    source_reference=SourceReference(
                        uri="pytest-cuke:runtime",
                        location=Location(line=1),
                    ),
                )
            ),
        )
        return hook_id

    def _start_test_run_hook(self, config: Config, hook_id: str, run_id: str) -> str:
        started_id = cast("PytestBDDIdGeneratorHandler", config).pytest_cuke_id_generator.get_next_id()
        config.hook.pytest_cuke_message(
            config=config,
            message=Message(
                test_run_hook_started=TestRunHookStarted(
                    id=started_id,
                    test_run_started_id=run_id,
                    hook_id=hook_id,
                    timestamp=self.get_timestamp(),
                )
            ),
        )
        return started_id

    def _finish_test_run_hook(
        self,
        config: Config,
        started_id: str,
        started_at: float,
        error: BaseException | None,
    ) -> None:
        elapsed = max(0.0, monotonic() - started_at)
        duration_seconds = int(elapsed)
        duration = Duration(seconds=duration_seconds, nanos=int((elapsed - duration_seconds) * 1_000_000_000))
        exception = (
            ExceptionMessage(
                type=type(error).__name__,
                message=str(error),
                stack_trace="".join(traceback.format_exception(error)),
            )
            if error is not None
            else None
        )
        result = TestStepResult(
            duration=duration,
            status=Status.failed if error is not None else Status.passed,
            exception=exception,
            message=str(error) if error is not None else None,
        )
        config.hook.pytest_cuke_message(
            config=config,
            message=Message(
                test_run_hook_finished=TestRunHookFinished(
                    test_run_hook_started_id=started_id,
                    result=result,
                    timestamp=self.get_timestamp(),
                )
            ),
        )
        if error is not None:
            self.test_run_hook_failed = True

    def _emit_ide_attachment(self, config: Config, media_type: str, payload: dict[str, Any]) -> None:
        config.hook.pytest_cuke_message(
            config=config,
            message=Message(
                attachment=Attachment(
                    body=json.dumps(payload, ensure_ascii=False),
                    content_encoding=ContentEncoding.identity,
                    media_type=media_type,
                )
            ),
        )

    @staticmethod
    def _item_source(item: Item) -> tuple[Any, Any] | None:
        callspec = getattr(item, "callspec", None)
        params = getattr(callspec, "params", {})
        if not isinstance(params, dict):
            return None
        feature = params.get("feature")
        scenario = params.get("scenario")
        return (feature, scenario) if feature is not None and scenario is not None else None

    @hookimpl(trylast=True)
    def pytest_collection_modifyitems(self, config: Config, items: list[Item]) -> None:
        """Index scenario source rows and pytest bindings once collection is complete."""
        if self.is_disabled:
            return

        run_context = get_run_context(config)
        if run_context is None:
            return

        for item in items:
            item_source = self._item_source(item)
            if item_source is None:
                continue
            feature, scenario = item_source
            binding = run_context.bind_feature(feature)
            binding.register_scenario(scenario)
            identity = source_identity(feature, scenario, binding)
            self.ide_bindings.register_source(identity, item.nodeid)

        for binding in run_context.feature_bindings_by_uri.values():
            for feature, scenario in ScenarioLocatorFilterMixin().filter_scenarios(binding.feature):
                identity = source_identity(feature, scenario, binding)
                self.ide_bindings.register_source(identity)

    def _emit_source_binding_diagnostics(self, session: Session) -> None:
        config = session.config
        for diagnostic in self.ide_bindings.diagnostics():
            self._emit_ide_attachment(config, IDE_DIAGNOSTIC_MEDIA_TYPE, diagnostic)

    @hookimpl(optionalhook=True)
    def pytest_testnodedown(self, node: Any, error: object | None) -> None:
        """Merge worker collection and execution identities on the xdist controller."""
        worker_id = self._worker_id_for_node(node) or "unknown"
        worker_output = getattr(node, "workeroutput", None)
        if isinstance(worker_output, dict):
            self.ide_bindings.merge_worker_output(
                worker_output.get(IDE_BINDING_WORKER_OUTPUT_KEY),
                worker_id=worker_id,
            )
        if not self.is_xdist_controller or self.worker_message_receiver is None:
            return
        if isinstance(worker_output, dict):
            transport_output = worker_output.get(_WORKER_MESSAGE_OUTPUT_KEY)
            if isinstance(transport_output, dict):
                tail_batch = transport_output.get("tail_batch")
                if isinstance(tail_batch, dict):
                    self._receive_worker_message_batch(tail_batch)
                manifest = transport_output.get("manifest")
                if isinstance(manifest, dict):
                    self.worker_message_receiver.record_manifest(manifest, expected_worker_id=worker_id)
        self.worker_message_receiver.mark_worker_down(worker_id, error)

    def _get_current_test_case(self) -> TestCase:
        if self.current_test_case is None:
            raise RuntimeError("There is no active pytest-cuke test case.")
        return self.current_test_case

    def _get_current_test_case_start(self) -> TestCaseStarted:
        if self.current_test_case_start is None:
            raise RuntimeError("There is no active pytest-cuke test case start event.")
        return self.current_test_case_start

    def _has_external_hook_implementation(self, hook_caller: Any) -> bool:
        get_hookimpls = getattr(hook_caller, "get_hookimpls", None)
        if not callable(get_hookimpls):
            return False
        return any(getattr(implementation, "plugin", None) is not self for implementation in get_hookimpls())

    def _new_scenario_hook_test_step(self, config: Config, *, phase: Literal["before", "after"]) -> TestStep:
        generator = cast("PytestBDDIdGeneratorHandler", config).pytest_cuke_id_generator
        hook_id = generator.get_next_id()
        hook_type = HookType.before_test_case if phase == "before" else HookType.after_test_case
        hook_name = f"pytest_cuke_{phase}_scenario"
        config.hook.pytest_cuke_message(
            config=config,
            message=Message(
                hook=Hook(
                    id=hook_id,
                    name=hook_name,
                    type=hook_type,
                    source_reference=SourceReference(
                        uri="pytest-cuke:runtime",
                        location=Location(line=1),
                    ),
                )
            ),
        )
        return TestStep(id=generator.get_next_id(), hook_id=hook_id)

    def _finish_scenario_hook_test_step(
        self,
        *,
        config: Config,
        test_case_started: TestCaseStarted,
        test_step: TestStep,
        start_timestamp: Timestamp,
        exception: BaseException | None,
    ) -> None:
        if exception is None:
            status = Status.passed
        elif isinstance(exception, (pytest.skip.Exception, pytest.xfail.Exception)):
            status = Status.skipped
        elif isinstance(exception, KeyboardInterrupt):
            status = Status.unknown
        else:
            status = Status.failed
        exception_message = (
            ExceptionMessage(
                type=type(exception).__name__,
                message=str(exception),
                stack_trace="".join(traceback.format_exception(exception)),
            )
            if exception is not None
            else None
        )
        self._finish_test_step(
            config=config,
            test_case_started=test_case_started,
            test_step=test_step,
            start_timestamp=start_timestamp,
            status=status,
            message=str(exception) if exception is not None else None,
            exception=exception_message,
            exception_stack_trace=exception_message.stack_trace if exception_message is not None else None,
        )

    @staticmethod
    def _cucumber_attempt(item: Any) -> int:
        """Return the zero-based Cucumber attempt number for a pytest item."""
        execution_count = getattr(item, "execution_count", 0)
        if isinstance(execution_count, int) and not isinstance(execution_count, bool):
            return max(0, execution_count - 1)
        return 0

    @hookimpl(hookwrapper=True, tryfirst=True)
    def pytest_sessionstart(self, session: Session) -> Generator[None, Any, Any]:
        if self.is_disabled:
            yield
            return

        protocol_version = resolve_upstream_release()[1].protocol_version
        if self.formatter_session is not None:
            self.formatter_session.start()
        self.start_process_messages_thread()

        config = session.config
        hook_handler = config.hook

        hook_handler.pytest_cuke_message(
            config=config,
            message=Message(
                meta=Meta(
                    protocol_version=protocol_version,
                    implementation=Product(name="pytest-cuke", version=str(get_distribution_version("pytest-cuke"))),
                    runtime=Product(name="Python", version=sys.version),
                    os=Product(name=system(), version=version()),
                    cpu=Product(name=machine(), version=processor()),
                    ci=message_from_dict(obj, Ci) if (obj := detect_ci_environment(os.environ)) is not None else None,
                ),
            ),
        )

        run_id = cast("PytestBDDIdGeneratorHandler", config).pytest_cuke_id_generator.get_next_id()
        self.test_run_started_id = run_id
        before_hook_id = self._emit_test_run_hook_definition(config, "before")
        after_hook_id = self._emit_test_run_hook_definition(config, "after")
        self.after_test_run_hook_id = after_hook_id
        hook_handler.pytest_cuke_message(
            config=config,
            message=Message(test_run_started=TestRunStarted(timestamp=self.get_timestamp(), id=run_id)),
        )
        hook_started_id = self._start_test_run_hook(config, before_hook_id, run_id)
        started_at = monotonic()
        outcome = yield
        error = outcome.excinfo[1] if outcome.excinfo is not None else None
        self._finish_test_run_hook(config, hook_started_id, started_at, error)

        if self.formatter_session is not None:
            try:
                self.formatter_session.check_running()
            except Exception as formatter_error:
                self._record_final_sink_failure(session, "live Cucumber formatter", formatter_error)

    def _pytest_sessionfinish(self, session: Session, exitstatus: int | ExitCode) -> Generator[None, Any, Any]:
        if self.is_disabled:
            yield
            return
        config = session.config
        hook_handler = config.hook

        run_context = get_run_context(config)
        if run_context is not None:
            for scenario_run in run_context.scenario_runs_by_nodeid.values():
                self._finish_scenario_test_case(scenario_run)

        after_hook_id = cast("str", getattr(self, "after_test_run_hook_id", ""))
        run_id = cast("str", getattr(self, "test_run_started_id", ""))
        hook_started_id = self._start_test_run_hook(config, after_hook_id, run_id)
        started_at = monotonic()
        outcome = yield
        error = outcome.excinfo[1] if outcome.excinfo is not None else None
        self._finish_test_run_hook(config, hook_started_id, started_at, error)

        worker_output = getattr(config, "workeroutput", None)
        if isinstance(worker_output, dict):
            worker_output[IDE_BINDING_WORKER_OUTPUT_KEY] = self.ide_bindings.to_worker_output()
        else:
            self._emit_source_binding_diagnostics(session)

        if hasattr(self, "process_messages_thread"):
            self.flush_process_messages_thread()
            self._report_process_messages_error(session)

        is_testrun_success = (
            ((isinstance(exitstatus, int) and exitstatus == 0) or exitstatus is ExitCode.OK)
            and not self.test_run_hook_failed
            and not (self.formatter_session and self.formatter_session.failed)
        )
        terminal_timestamp = self.get_timestamp()
        terminal_message = Message(
            test_run_finished=TestRunFinished(
                timestamp=terminal_timestamp,
                success=is_testrun_success and not (self.message_transport and self.message_transport.has_errors),
                test_run_started_id=self.test_run_started_id,
            )
        )
        if self.message_transport is not None and self.message_transport.preview_finish(terminal_message):
            terminal_message = Message(
                test_run_finished=TestRunFinished(
                    timestamp=terminal_timestamp,
                    success=False,
                    test_run_started_id=self.test_run_started_id,
                )
            )
        hook_handler.pytest_cuke_message(
            config=config,
            message=terminal_message,
        )

        if self.message_transport is not None:
            self._report_message_diagnostics(self.message_transport.finish())
            if self.message_transport.has_errors:
                self._mark_session_failed(session)

        if not self.is_xdist_worker:
            try:
                self.finish_process_messages_thread()
            except Exception as error:
                self._record_final_sink_failure(session, "Cucumber Messages NDJSON writer", error)
        self._report_process_messages_error(session)
        if self.is_xdist_worker:
            self._publish_worker_message_manifest(session)
            if self.is_messages_file_temp and self.messages_file_path.exists():
                try:
                    os.unlink(self.messages_file_path)
                except OSError as error:
                    self._record_final_sink_failure(session, "temporary Cucumber Messages cleanup", error)
            return
        xdist_stream_complete = True
        if self.is_xdist_controller:
            xdist_stream_complete = self._finalize_xdist_message_stream(session)
        if self.formatter_session is not None:
            if xdist_stream_complete:
                try:
                    self.formatter_session.finish()
                except Exception as error:
                    self._record_final_sink_failure(session, "live Cucumber formatter", error)
            else:
                self.formatter_session.abort()
                self._mark_session_failed(session)
            if self.formatter_session.failed:
                self._mark_session_failed(session)
        try:
            if self._configured_output("cuke_html") is not None:
                try:
                    self.generate_html_report()
                except Exception as error:
                    self._record_final_sink_failure(session, "Cucumber HTML report", error)
        finally:
            if self.is_messages_file_temp and self.messages_file_path.exists():
                try:
                    os.unlink(self.messages_file_path)
                except OSError as error:
                    self._record_final_sink_failure(session, "temporary Cucumber Messages cleanup", error)

        if self.message_transport is not None and self.message_transport.has_errors:
            self._mark_session_failed(session)

    def _publish_worker_message_manifest(self, session: Session) -> None:
        worker_output = getattr(session.config, "workeroutput", None)
        batcher = self.worker_message_batcher
        if not isinstance(worker_output, dict) or batcher is None:
            self._record_final_sink_failure(
                session,
                "xdist worker Messages manifest",
                RuntimeError("pytest-xdist did not provide workeroutput for the Messages completion manifest"),
            )
            return
        tail_batch = self._take_worker_message_batch()
        complete = self.message_transport is not None and not self.message_transport.has_errors
        manifest = batcher.make_manifest(
            complete=complete,
            interruption_reason=None if complete else "worker message validation or a transport sink failed",
        )
        worker_output[_WORKER_MESSAGE_OUTPUT_KEY] = {
            "manifest": manifest.to_payload(),
            "tail_batch": tail_batch,
        }
        with self.process_messages_lock:
            self.process_messages_closed = True

    def _finalize_xdist_message_stream(self, session: Session) -> bool:
        receiver = self.worker_message_receiver
        if receiver is None:
            self._record_final_sink_failure(
                session,
                "xdist worker Messages receiver",
                RuntimeError("The xdist controller has no worker Messages receiver to finalize."),
            )
            return False
        received = receiver.finalize()
        fragments = [
            MessageFragment(worker_id="master", role="controller", envelopes=tuple(self.accepted_message_payloads))
        ]
        fragments.extend(
            MessageFragment(worker_id=fragment.worker_id, role="worker", envelopes=fragment.envelopes)
            for fragment in received.fragments
        )
        consolidated = consolidate_message_fragments(fragments)
        diagnostics = [
            integration_diagnostic(
                code=cast("MessageValidationCode", diagnostic.code),
                position=len(consolidated.envelope_dicts),
                payload_kind=None,
                message=diagnostic.message,
                offending_ids=(diagnostic.worker_id,) if diagnostic.worker_id is not None else (),
            )
            for diagnostic in received.diagnostics
        ]
        diagnostics.extend(
            integration_diagnostic(
                code=cast("MessageValidationCode", diagnostic.code),
                position=len(consolidated.envelope_dicts),
                payload_kind=None,
                message=diagnostic.message,
                offending_ids=(diagnostic.worker_id,) if diagnostic.worker_id is not None else (),
            )
            for diagnostic in consolidated.diagnostics
        )

        wire_stream = [json.loads(json.dumps(envelope, ensure_ascii=False)) for envelope in consolidated.envelope_dicts]
        if diagnostics:
            _set_test_run_success(wire_stream, False)

        validator = MessageStreamValidator()
        for payload in wire_stream:
            try:
                validator.accept(message_from_dict(payload, Message))
            except MessageValidationError as error:
                diagnostics.extend(error.diagnostics)
        diagnostics.extend(validator.finish())
        if diagnostics:
            _set_test_run_success(wire_stream, False)
            for diagnostic in diagnostics:
                self._report_message_diagnostics((diagnostic,))
            self._mark_session_failed(session)

        write_succeeded = True
        try:
            _write_message_stream(self.messages_file_path, wire_stream)
        except Exception as error:
            self._record_final_sink_failure(session, "consolidated Cucumber Messages writer", error)
            write_succeeded = False
        return not diagnostics and write_succeeded

    @staticmethod
    def _mark_session_failed(session: Session) -> None:
        if getattr(session, "exitstatus", ExitCode.OK) == ExitCode.OK:
            session.exitstatus = ExitCode.TESTS_FAILED

    def _record_final_sink_failure(self, session: Session, sink_name: str, error: Exception) -> None:
        if self.message_transport is not None:
            diagnostic = self.message_transport.record_sink_failure(sink_name, error)
            self._report_message_diagnostics((diagnostic,))
        self._mark_session_failed(session)

    def _report_process_messages_error(self, session: Session) -> None:
        with self.process_messages_lock:
            error = self.process_messages_error
            if error is None or self.process_messages_error_reported:
                return
            self.process_messages_error_reported = True
        self._record_final_sink_failure(
            session,
            "Cucumber Messages NDJSON writer",
            error,
        )

    @hookimpl(hookwrapper=True)
    def pytest_fixture_setup(self, fixturedef: FixtureDef[Any], request: FixtureRequest) -> Generator[None, None, None]:
        if self.is_disabled:
            yield
            return
        func = fixturedef.func
        func_id = id(func)

        if func_id in self.hook_registry:
            yield
            return

        config = request.config
        hook_handler = config.hook

        if hasattr(func, "__pytest_cuke_is_hook__"):
            self.hook_registry.add(func_id)

            hook_name = getattr(func, "__pytest_cuke_hook_name__", None)
            hook_expression = getattr(func, "__pytest_cuke_hook_expression__", None)

            hook_handler.pytest_cuke_message(
                config=config,
                message=Message(
                    hook=Hook(
                        id=cast("PytestBDDIdGeneratorHandler", config).pytest_cuke_id_generator.get_next_id(),
                        **({"name": hook_name} if hook_name is not None else {}),
                        source_reference=SourceReference(
                            uri=str(
                                relpath(
                                    getfile(func),
                                    str(get_config_root_path(config)),
                                )
                            ),
                            location=Location(line=getsourcelines(func)[1]),
                        ),
                        **({"tag_expression": hook_expression} if hook_expression is not None else {}),
                    )
                ),
            )

        yield

    @hookimpl(hookwrapper=True)
    def pytest_runtest_setup(self, item: Item) -> Generator[None, None, None]:
        yield
        if self.is_disabled:
            return

        if not {"feature", "scenario"}.issubset(getattr(item, "fixturenames", ())):
            return

        session = item.session
        config: Config = session.config

        hook_handler = config.hook

        request = item._request
        scenario = request.getfixturevalue("scenario")
        feature = request.getfixturevalue("feature")

        step_registry = request.getfixturevalue("step_registry")
        seen_steps = set()
        available_step_definitions = []
        while step_registry is not None:
            for step_definition in step_registry:
                if id(step_definition) not in seen_steps:
                    seen_steps.add(id(step_definition))
                    available_step_definitions.append(step_definition)
                    hook_handler.pytest_cuke_message(
                        config=config, message=Message(step_definition=step_definition.as_message(config=config))
                    )
            step_registry = step_registry.parent

        step_registry = request.getfixturevalue("step_registry")
        seen_steps = set()
        while step_registry is not None:
            not_yet_registered_parameter_types: dict[int, Any] = {}
            for step_definition in step_registry:
                if id(step_definition) not in seen_steps:
                    parameter_type_registry_getter: Callable[[FixtureRequest], ParameterTypeRegistry] = deepattrgetter(
                        "_get_parameter_type_registry", default=None
                    )(step_definition.parser)[0]

                    if parameter_type_registry_getter is None:
                        continue

                    parameter_type_registry = parameter_type_registry_getter(request)

                    parameter_types = {id(pt): pt for pt in parameter_type_registry.parameter_types}

                    not_yet_registered_parameter_types = {
                        key: parameter_type
                        for key, parameter_type in parameter_types.items()
                        if key not in self.parameter_type_registry
                    }

                    for parameter_type in not_yet_registered_parameter_types.values():
                        hook_handler.pytest_cuke_message(
                            config=config,
                            message=Message(
                                parameter_type=ParameterType(
                                    name=parameter_type.name,
                                    regular_expressions=parameter_type.regexps,
                                    prefer_for_regular_expression_match=parameter_type._prefer_for_regexp_match,
                                    use_for_snippets=parameter_type._use_for_snippets,
                                    id=cast(
                                        "PytestBDDIdGeneratorHandler", config
                                    ).pytest_cuke_id_generator.get_next_id(),
                                ),
                            ),
                        )
            self.parameter_type_registry.update(not_yet_registered_parameter_types)
            step_registry = step_registry.parent

        cached_test_case = self.test_cases_by_nodeid.get(item.nodeid)
        hook_caller_by_phase: dict[Literal["before", "after"], Any] = {
            "before": hook_handler.pytest_cuke_before_scenario,
            "after": hook_handler.pytest_cuke_after_scenario,
        }
        external_hook_phases: set[Literal["before", "after"]] = set()
        for phase, hook_caller in hook_caller_by_phase.items():
            if self._has_external_hook_implementation(hook_caller):
                external_hook_phases.add(phase)
        case_hook_steps = self.test_case_hook_steps_by_nodeid.get(item.nodeid, {})
        test_steps = []
        previous_step = None

        self._reset_current_test_case()
        self._set_scenario_state("attempt", self._cucumber_attempt(item))
        self._set_scenario_state("defer_test_case_finish", True)
        feature_uri = feature.uri or feature.filename or feature.name
        callspec_id = getattr(getattr(request.node, "callspec", None), "id", "")
        fallback_id = f"{feature_uri}#{callspec_id}" if callspec_id else ""
        scenario_id = scenario_pickle_id(scenario, uri=feature_uri, default_id=fallback_id)
        step_binding_records: list[tuple[Step, Any | None, tuple[Any, ...]]] = []

        scenario_steps = list(execution_steps(feature, scenario))
        if cached_test_case is not None and (
            len(cached_test_case.test_steps) != len(scenario_steps) + len(external_hook_phases)
            or set(case_hook_steps) != external_hook_phases
        ):
            cached_test_case = None
            case_hook_steps = {}

        for step_index, step in enumerate(scenario_steps):
            try:
                step_matcher = request.getfixturevalue("step_matcher")
            except Exception:
                step_matcher = None
            if hasattr(step_matcher, "last_matches"):
                step_matcher.last_matches = ()
            try:
                inspection_context = RunContext.from_config(config)
                with inspection_context.inspect_step(
                    feature=feature,
                    scenario=scenario,
                    step=step,
                    previous_step=previous_step,
                    nodeid=item.nodeid,
                ) as run:
                    step_definition = hook_handler.pytest_cuke_match_step_definition_to_step(
                        request=request,
                        run=run,
                    )
            except Matcher.MatchNotFoundError:
                step_definition = None
                step_definition_ids = []
            else:
                step_definition_ids = [step_definition.as_message(config).id]
            finally:
                previous_step = step

            step_matches = tuple(getattr(step_matcher, "last_matches", ()))
            step_binding_records.append((step, step_definition, step_matches))

            cached_step_index = step_index + int("before" in case_hook_steps)
            test_step = (
                cached_test_case.test_steps[cached_step_index]
                if cached_test_case is not None
                else TestStep(
                    id=cast("PytestBDDIdGeneratorHandler", config).pytest_cuke_id_generator.get_next_id(),
                    pickle_step_id=f"{scenario_id}-step-{step_index}",
                    step_definition_ids=step_definition_ids,
                )
            )
            test_steps.append(test_step)
            self.current_test_case_step_id_to_step_mapping[id(step)] = test_step

        if cached_test_case is None:
            case_hook_steps = {
                phase: self._new_scenario_hook_test_step(config, phase=phase) for phase in sorted(external_hook_phases)
            }
            self.test_case_hook_steps_by_nodeid[item.nodeid] = case_hook_steps

        case_test_steps = [
            *([case_hook_steps["before"]] if "before" in case_hook_steps else []),
            *test_steps,
            *([case_hook_steps["after"]] if "after" in case_hook_steps else []),
        ]
        self.current_test_case_step_order = case_test_steps

        current_test_case = cached_test_case or TestCase(
            id=cast("PytestBDDIdGeneratorHandler", config).pytest_cuke_id_generator.get_next_id(),
            pickle_id=scenario_id,
            test_steps=case_test_steps,
        )
        self.current_test_case = current_test_case
        self.test_cases_by_nodeid[item.nodeid] = current_test_case
        run_context = get_run_context(config)
        if run_context is not None:
            active_run = run_context.active_scenario_run
            if active_run is not None and active_run.nodeid == request.node.nodeid:
                run_context.set_test_case(
                    test_case_id=current_test_case.id,
                    test_step_ids=[test_step.id for test_step in case_test_steps],
                    test_steps=case_test_steps,
                )

        if cached_test_case is None:
            hook_handler.pytest_cuke_message(
                config=config,
                message=Message(test_case=current_test_case),
            )

        run_context = get_run_context(config)
        binding = run_context.bind_feature(feature) if run_context is not None else None
        if binding is not None:
            binding.register_scenario(scenario)
        identity = source_identity(feature, scenario, binding)
        self.ide_bindings.register_source(identity, request.node.nodeid)
        self.ide_bindings.record_test_case(
            request.node.nodeid,
            current_test_case.id,
            worker_id=run_context.worker_id if run_context is not None else None,
        )

        launch_payload: dict[str, Any] = {
            "testCaseId": current_test_case.id,
            "pickleId": current_test_case.pickle_id,
            "nodeid": request.node.nodeid,
            "sourceIdentity": identity,
        }
        if external_source := scenario.external_example_source:
            launch_payload["externalExamplesSource"] = {
                "path": external_source.path,
                "markerLine": external_source.marker_line,
                "sectionIndex": external_source.section_index,
                "rowIndex": external_source.row_index,
                "sourceLine": external_source.source_line,
            }
        self._emit_ide_attachment(config, IDE_LAUNCH_MEDIA_TYPE, launch_payload)

        available_definitions = [definition_reference(definition, config) for definition in available_step_definitions]
        for test_step, (step, definition, candidates) in zip(test_steps, step_binding_records, strict=True):
            if definition is None:
                self._emit_ide_attachment(
                    config,
                    IDE_DIAGNOSTIC_MEDIA_TYPE,
                    {
                        "kind": "missing-step",
                        "severity": "warning",
                        "testCaseId": current_test_case.id,
                        "pickleStepId": test_step.pickle_step_id,
                        "unmatchedStepText": step.name,
                        "availableStepDefinitions": available_definitions,
                    },
                )
                continue

            matched_definition = definition_reference(definition, config)
            self._emit_ide_attachment(
                config,
                IDE_STEP_BINDING_MEDIA_TYPE,
                {
                    "testCaseId": current_test_case.id,
                    "pickleStepId": test_step.pickle_step_id,
                    "stepDefinitionId": matched_definition["stepDefinitionId"],
                    "sourceReference": matched_definition["sourceReference"],
                    "matchArguments": match_arguments(definition, request, step),
                },
            )
            if len(candidates) > 1:
                self._emit_ide_attachment(
                    config,
                    IDE_DIAGNOSTIC_MEDIA_TYPE,
                    {
                        "kind": "ambiguous-step",
                        "severity": "warning",
                        "testCaseId": current_test_case.id,
                        "pickleStepId": test_step.pickle_step_id,
                        "candidates": [definition_reference(candidate, config) for candidate in candidates],
                    },
                )

    @hookimpl(tryfirst=True)
    def pytest_runtest_logreport(self, report: TestReport) -> None:
        if self.is_disabled:
            return
        run_context = get_run_context(self.config)
        if run_context is None:
            return
        scenario_run = run_context.get_scenario_run(report.nodeid)
        if scenario_run is None:
            return

        if getattr(report, "outcome", None) == "rerun":
            scenario_run.message_state.will_be_retried = True
            if report.when == "teardown":
                self._finish_scenario_test_case(scenario_run)
            return

        if report.when == "setup" and report.outcome == "skipped":
            self._finish_setup_skipped_test_case(scenario_run, report)
            return

        if report.when == "teardown":
            self._finish_scenario_test_case(scenario_run)

    def _start_test_case(self, *, config: Config, test_case: TestCase, attempt: int) -> TestCaseStarted:
        test_case_started = TestCaseStarted(
            attempt=attempt,
            id=cast("PytestBDDIdGeneratorHandler", config).pytest_cuke_id_generator.get_next_id(),
            test_case_id=test_case.id,
            worker_id=os.environ.get("PYTEST_XDIST_WORKER", "master"),
            timestamp=self.get_timestamp(),
        )
        self.current_test_case_start = test_case_started
        config.hook.pytest_cuke_message(
            config=config,
            message=Message(test_case_started=test_case_started),
        )
        return test_case_started

    def _finish_setup_skipped_test_case(self, scenario_run: Any, report: TestReport) -> None:
        message_state = scenario_run.message_state
        test_case = message_state.test_case
        if test_case is None or message_state.test_case_started is not None:
            return

        test_case_started = self._start_test_case(
            config=self.config,
            test_case=test_case,
            attempt=message_state.attempt,
        )
        scenario_run.test_case_started_id = test_case_started.id
        scenario_run.attempt_id = test_case_started.id

        longrepr = getattr(report, "longrepr", None)
        skip_reason = str(longrepr[-1] if isinstance(longrepr, tuple) and longrepr else longrepr or "")
        for test_step in message_state.test_steps:
            start_timestamp = self._start_test_step(
                config=self.config,
                test_case_started=test_case_started,
                test_step=test_step,
            )
            self._finish_test_step(
                config=self.config,
                test_case_started=test_case_started,
                test_step=test_step,
                start_timestamp=start_timestamp,
                status=Status.skipped,
                message=skip_reason,
                scenario_message_state=message_state,
                defer_final_step=False,
            )
        self._emit_test_case_finished(
            self.config,
            test_case_started,
            will_be_retried=message_state.will_be_retried,
        )
        self._reset_scenario_message_state(message_state)

    def _finish_scenario_test_case(self, scenario_run: Any) -> None:
        message_state = scenario_run.message_state
        test_case_started = message_state.test_case_started
        if test_case_started is None:
            return

        pending = message_state.pending_test_step_finish
        if pending is not None:
            status = pending.status
            message = pending.message
            exception = pending.exception
            exception_stack_trace = pending.exception_stack_trace
            step_statuses = {step_run.status for step_run in scenario_run.steps}
            fallback_status: Status | None = None
            fallback_type = ""
            fallback_message = ""
            terminal_step = scenario_run.steps[-1] if scenario_run.steps else None
            if (
                scenario_run.status == "failed"
                and terminal_step is not None
                and terminal_step.status == "failed"
                and terminal_step.exception is scenario_run.exception
                and terminal_step.test_step_id == pending.test_step.id
                and pending.status not in (Status.failed, Status.undefined, Status.unknown)
            ):
                fallback_status = Status.failed
                error = terminal_step.exception
                fallback_type = type(error).__name__ if error is not None else "Exception"
                fallback_message = str(error) if error is not None else "Scenario failed during teardown."
            elif (
                scenario_run.status == "interrupted"
                and "interrupted" not in step_statuses
                and pending.status
                not in (
                    Status.failed,
                    Status.undefined,
                    Status.unknown,
                )
            ):
                fallback_status = Status.unknown
                fallback_type = "KeyboardInterrupt"
                fallback_message = "Scenario interrupted during teardown."
            if fallback_status is not None:
                status = fallback_status
                error = scenario_run.exception
                message = str(error) if error is not None else fallback_message
                exception = ExceptionMessage(
                    type=type(error).__name__ if error is not None else fallback_type,
                    message=message,
                )
                exception_stack_trace = (
                    "".join(traceback.format_exception(type(error), error, error.__traceback__))
                    if error is not None
                    else None
                )

            self._finish_test_step(
                config=self.config,
                test_case_started=test_case_started,
                test_step=pending.test_step,
                start_timestamp=pending.start_timestamp,
                status=status,
                message=message,
                exception=exception,
                exception_stack_trace=exception_stack_trace,
                scenario_message_state=message_state,
                defer_final_step=False,
                finish_timestamp=pending.finish_timestamp,
            )

        self._emit_test_case_finished(
            self.config,
            test_case_started,
            will_be_retried=message_state.will_be_retried,
        )
        self._reset_scenario_message_state(message_state)

    @hookimpl(hookwrapper=True, tryfirst=True)
    def pytest_cuke_before_scenario(self, request: FixtureRequest, run: RunContext) -> Generator[None, Any, Any]:
        if self.is_disabled:
            yield
            return
        config = request.config
        run.require_feature("pytest_cuke_before_scenario")
        run.require_scenario("pytest_cuke_before_scenario")
        current_test_case = self._get_current_test_case()

        current_test_case_start = self._start_test_case(
            config=config,
            test_case=current_test_case,
            attempt=self._get_scenario_state("attempt", self._cucumber_attempt(request.node)),
        )
        active_run = run.active_scenario_run
        if active_run is not None and active_run.nodeid == request.node.nodeid:
            run.set_attempt_id(current_test_case_start.id)

        hook_step = self.test_case_hook_steps_by_nodeid.get(request.node.nodeid, {}).get("before")
        hook_start_timestamp = (
            self._start_test_step(config=config, test_case_started=current_test_case_start, test_step=hook_step)
            if hook_step is not None
            else None
        )
        outcome = yield
        exc_info = outcome.excinfo
        exception = exc_info[1] if exc_info is not None else None
        if hook_step is not None and hook_start_timestamp is not None:
            self._finish_scenario_hook_test_step(
                config=config,
                test_case_started=current_test_case_start,
                test_step=hook_step,
                start_timestamp=hook_start_timestamp,
                exception=exception,
            )

    @hookimpl(hookwrapper=True, tryfirst=True)
    def pytest_cuke_after_scenario(self, request: FixtureRequest, run: RunContext) -> Generator[None, Any, Any]:
        if self.is_disabled:
            yield
            return
        config = request.config
        run.require_scenario("pytest_cuke_after_scenario")

        current_test_case_start = self.current_test_case_start
        if current_test_case_start is None:
            yield
            self._reset_current_test_case()
            return

        hook_step = self.test_case_hook_steps_by_nodeid.get(request.node.nodeid, {}).get("after")
        hook_start_timestamp = (
            self._start_test_step(config=config, test_case_started=current_test_case_start, test_step=hook_step)
            if hook_step is not None
            else None
        )
        outcome = yield
        exc_info = outcome.excinfo
        exception = exc_info[1] if exc_info is not None else None
        if hook_step is not None and hook_start_timestamp is not None:
            self._finish_scenario_hook_test_step(
                config=config,
                test_case_started=current_test_case_start,
                test_step=hook_step,
                start_timestamp=hook_start_timestamp,
                exception=exception,
            )

        active_run = run.active_scenario_run
        retain_until_teardown = active_run is not None and active_run.nodeid == request.node.nodeid
        try:
            for test_step in self.current_test_case_step_order:
                if test_step.id in self.current_finished_test_step_ids:
                    continue
                start_timestamp = self.current_test_step_start_timestamps.get(test_step.id)
                status = Status.failed if start_timestamp is not None else Status.skipped
                if start_timestamp is None:
                    start_timestamp = self._start_test_step(
                        config=config,
                        test_case_started=current_test_case_start,
                        test_step=test_step,
                    )
                self._finish_test_step(
                    config=config,
                    test_case_started=current_test_case_start,
                    test_step=test_step,
                    start_timestamp=start_timestamp,
                    status=status,
                )

            if not retain_until_teardown:
                self._emit_test_case_finished(config, current_test_case_start)
        finally:
            if not retain_until_teardown:
                self._reset_current_test_case()

    def _emit_test_case_finished(
        self,
        config: Config,
        test_case_started: TestCaseStarted,
        *,
        will_be_retried: bool = False,
    ) -> None:
        config.hook.pytest_cuke_message(
            config=config,
            message=Message(
                test_case_finished=TestCaseFinished(
                    test_case_started_id=test_case_started.id,
                    timestamp=self.get_timestamp(),
                    will_be_retried=will_be_retried,
                )
            ),
        )

    def _reset_current_test_case(self) -> None:
        scenario_run = self._active_scenario_run()
        if scenario_run is not None:
            self._reset_scenario_message_state(scenario_run.message_state)

    @staticmethod
    def _reset_scenario_message_state(message_state: Any) -> None:
        message_state.test_case = None
        message_state.test_case_started = None
        message_state.attempt = 0
        message_state.will_be_retried = False
        message_state.test_steps = []
        message_state.test_steps_by_identity = {}
        message_state.finished_test_step_ids = set()
        message_state.test_step_start_timestamps = {}
        message_state.active_test_step_id = None
        message_state.test_step_exception_traces = {}
        message_state.pending_test_step_finish = None
        message_state.defer_test_case_finish = False

    def pytest_cuke_before_step(self, request: FixtureRequest, run: RunContext, step_func: Any) -> None:
        if self.is_disabled:
            return
        config = request.config
        current_test_case_start = self._get_current_test_case_start()
        step = run.require_step("pytest_cuke_before_step")

        step_definition = self.current_test_case_step_id_to_step_mapping[id(step)]

        self._start_test_step(
            config=config,
            test_case_started=current_test_case_start,
            test_step=step_definition,
        )
        self.current_test_case_started_step_ids.add(step_definition.id)

    def pytest_cuke_step_bypassed(
        self,
        request: FixtureRequest,
        run: RunContext,
        step_definition: Any,
        status: Literal["passed", "skipped"],
        message: str | None = None,
    ) -> None:
        if self.is_disabled:
            return
        config = request.config
        current_test_case_start = self._get_current_test_case_start()
        step = run.require_step("pytest_cuke_step_bypassed")
        test_step = self.current_test_case_step_id_to_step_mapping[id(step)]
        start_timestamp = self._start_test_step(
            config=config,
            test_case_started=current_test_case_start,
            test_step=test_step,
        )
        self._finish_test_step(
            config=config,
            test_case_started=current_test_case_start,
            test_step=test_step,
            start_timestamp=start_timestamp,
            status=Status.passed if status == "passed" else Status.skipped,
            message=message,
        )

    def pytest_cuke_after_step(self, request: FixtureRequest, run: RunContext, step_func: Any) -> None:
        if self.is_disabled:
            return
        config = request.config
        current_test_case_start = self._get_current_test_case_start()
        step = run.require_step("pytest_cuke_after_step")

        step_definition = self.current_test_case_step_id_to_step_mapping[id(step)]
        self._finish_test_step(
            config=config,
            test_case_started=current_test_case_start,
            test_step=step_definition,
            start_timestamp=self.current_test_step_start_timestamps[step_definition.id],
            status=Status.passed,
        )
        self.current_test_case_finished_step_ids.add(step_definition.id)

    def pytest_cuke_step_error(
        self,
        request: FixtureRequest,
        run: RunContext,
        step_func: Any,
        step_func_args: dict[str, Any],
        exception: BaseException,
        step_definition: Any,
        tolerated: bool,
    ) -> None:
        if self.is_disabled:
            return
        config = request.config
        current_test_case_start = self._get_current_test_case_start()
        step = run.require_step("pytest_cuke_step_error")

        step_definition = self.current_test_case_step_id_to_step_mapping[id(step)]
        if isinstance(exception, (pytest.skip.Exception, pytest.xfail.Exception)):
            status = Status.skipped
        elif isinstance(exception, KeyboardInterrupt):
            # Cucumber Messages has no interrupted outcome; UNKNOWN keeps this
            # distinct from a scenario that completed with an ordinary failure.
            status = Status.unknown
        else:
            status = Status.failed
        start_timestamp = self.current_test_step_start_timestamps.get(step_definition.id)
        if start_timestamp is None:
            start_timestamp = self._start_test_step(
                config=config,
                test_case_started=current_test_case_start,
                test_step=step_definition,
            )
        self._finish_test_step(
            config=config,
            test_case_started=current_test_case_start,
            test_step=step_definition,
            start_timestamp=start_timestamp,
            status=status,
            message=str(exception),
            exception=ExceptionMessage(
                type=type(exception).__name__,
                message=str(exception),
            ),
            exception_stack_trace="".join(
                traceback.format_exception(type(exception), exception, exception.__traceback__)
            ),
        )
        if tolerated:
            return

        failed_step_index = next(
            index
            for index, ordered_step in enumerate(self.current_test_case_step_order)
            if ordered_step is step_definition
        )
        for skipped_step in self.current_test_case_step_order[failed_step_index + 1 :]:
            if skipped_step.id in self.current_finished_test_step_ids:
                continue
            skipped_start = self._start_test_step(
                config=config,
                test_case_started=current_test_case_start,
                test_step=skipped_step,
            )
            self._finish_test_step(
                config=config,
                test_case_started=current_test_case_start,
                test_step=skipped_step,
                start_timestamp=skipped_start,
                status=Status.skipped,
            )

    def pytest_cuke_step_func_lookup_error(
        self,
        request: FixtureRequest,
        run: RunContext,
        exception: Exception,
    ) -> None:
        if self.is_disabled:
            return
        config = request.config
        current_test_case_start = self._get_current_test_case_start()
        step = run.require_step("pytest_cuke_step_func_lookup_error")
        test_step = self.current_test_case_step_id_to_step_mapping[id(step)]

        for expression, name in self._undefined_parameter_types_from(exception):
            config.hook.pytest_cuke_message(
                config=config,
                message=Message(undefined_parameter_type=UndefinedParameterType(expression=expression, name=name)),
            )

        start_timestamp = self.current_test_step_start_timestamps.get(test_step.id)
        if start_timestamp is None:
            start_timestamp = self._start_test_step(
                config=config,
                test_case_started=current_test_case_start,
                test_step=test_step,
            )
        self._finish_test_step(
            config=config,
            test_case_started=current_test_case_start,
            test_step=test_step,
            start_timestamp=start_timestamp,
            status=Status.undefined,
            message=str(exception),
        )

    @staticmethod
    def _undefined_parameter_types_from(exception: BaseException) -> tuple[tuple[str, str], ...]:
        diagnostics: dict[tuple[str, str], None] = {}
        pending: list[BaseException] = [exception]
        visited: set[int] = set()
        while pending:
            current = pending.pop()
            if id(current) in visited:
                continue
            visited.add(id(current))

            for diagnostic in getattr(current, "undefined_parameter_types", ()):
                if (
                    isinstance(diagnostic, tuple)
                    and len(diagnostic) == 2
                    and isinstance(diagnostic[0], str)
                    and isinstance(diagnostic[1], str)
                    and diagnostic[1]
                ):
                    diagnostics.setdefault(diagnostic, None)

            chained_diagnostic = getattr(current, "_pytest_cuke_undefined_parameter_type", None)
            if (
                isinstance(chained_diagnostic, tuple)
                and len(chained_diagnostic) == 2
                and isinstance(chained_diagnostic[0], str)
                and isinstance(chained_diagnostic[1], str)
                and chained_diagnostic[1]
            ):
                diagnostics.setdefault(chained_diagnostic, None)

            cause = current.__cause__ or current.__context__
            if cause is not None:
                pending.append(cause)

        return tuple(diagnostics)

    def _start_test_step(self, *, config: Config, test_case_started: TestCaseStarted, test_step: TestStep) -> Timestamp:
        timestamp = self.get_timestamp()
        self.current_test_step_start_timestamps[test_step.id] = timestamp
        self.current_active_test_step_id = test_step.id
        config.hook.pytest_cuke_message(
            config=config,
            message=Message(
                test_step_started=TestStepStarted(
                    test_case_started_id=test_case_started.id,
                    timestamp=timestamp,
                    test_step_id=test_step.id,
                )
            ),
        )
        return timestamp

    def _finish_test_step(
        self,
        *,
        config: Config,
        test_case_started: TestCaseStarted,
        test_step: TestStep,
        start_timestamp: Timestamp,
        status: Status,
        message: str | None = None,
        exception: ExceptionMessage | None = None,
        exception_stack_trace: str | None = None,
        scenario_message_state: Any | None = None,
        defer_final_step: bool = True,
        finish_timestamp: Timestamp | None = None,
    ) -> None:
        finish_timestamp = finish_timestamp or self.get_timestamp()
        if (
            defer_final_step
            and scenario_message_state is None
            and self._get_scenario_state("defer_test_case_finish", False)
            and self.current_test_case_step_order
            and test_step.id == self.current_test_case_step_order[-1].id
        ):
            self.pending_test_step_finish = PendingTestStepFinish(
                test_case_started=test_case_started,
                test_step=test_step,
                start_timestamp=start_timestamp,
                finish_timestamp=finish_timestamp,
                status=status,
                message=message,
                exception=exception,
                exception_stack_trace=exception_stack_trace,
            )
            if self.current_active_test_step_id == test_step.id:
                self.current_active_test_step_id = None
            self.current_finished_test_step_ids.add(test_step.id)
            return

        if exception_stack_trace is not None:
            if scenario_message_state is None:
                self.current_test_step_exception_traces[test_step.id] = exception_stack_trace
            else:
                scenario_message_state.test_step_exception_traces[test_step.id] = exception_stack_trace
        duration_total_nanos = (finish_timestamp.seconds * 10**9 + finish_timestamp.nanos) - (
            start_timestamp.seconds * 10**9 + start_timestamp.nanos
        )
        duration_seconds = duration_total_nanos // 10**9
        duration_nanos = duration_total_nanos - duration_seconds * 10**9
        duration = Duration(seconds=duration_seconds, nanos=duration_nanos)
        try:
            config.hook.pytest_cuke_message(
                config=config,
                message=Message(
                    test_step_finished=TestStepFinished(
                        test_case_started_id=test_case_started.id,
                        timestamp=finish_timestamp,
                        test_step_id=test_step.id,
                        test_step_result=TestStepResult(
                            duration=duration,
                            status=status,
                            message=message,
                            exception=exception,
                        ),
                    )
                ),
            )
        finally:
            if scenario_message_state is None:
                self.current_test_step_exception_traces.pop(test_step.id, None)
            else:
                scenario_message_state.test_step_exception_traces.pop(test_step.id, None)
        if scenario_message_state is None:
            self.current_test_step_start_timestamps.pop(test_step.id, None)
            if self.current_active_test_step_id == test_step.id:
                self.current_active_test_step_id = None
            self.current_finished_test_step_ids.add(test_step.id)
        else:
            scenario_message_state.pending_test_step_finish = None
            scenario_message_state.test_step_start_timestamps.pop(test_step.id, None)
            if scenario_message_state.active_test_step_id == test_step.id:
                scenario_message_state.active_test_step_id = None
            scenario_message_state.finished_test_step_ids.add(test_step.id)

    def pytest_cuke_attach(
        self,
        request: FixtureRequest,
        run: RunContext,
        attachment: Any,
        media_type: str | None,
        file_name: str | None,
    ) -> None:
        if self.is_disabled:
            return
        config = request.config
        hook_handler = config.hook
        self._get_current_test_case()
        current_test_case_start = self._get_current_test_case_start()
        active_scenario_run = run.active_scenario_run
        active_test_step_id = (
            active_scenario_run.message_state.active_test_step_id
            if active_scenario_run is not None
            else self.current_active_test_step_id
        )
        if active_test_step_id not in self.current_test_step_start_timestamps:
            active_test_step_id = None

        if isinstance(attachment, str | TextIOBase):
            content_encoding = AttachmentContentEncoding.identity
            _media_type = "text/plain;charset=UTF-8" if media_type is None else media_type
        elif isinstance(attachment, bytes | bytearray | BufferedIOBase):
            content_encoding = AttachmentContentEncoding.base64
            _media_type = "application/octet-stream" if media_type is None else media_type
        else:
            content_encoding = AttachmentContentEncoding.identity
            _media_type = "text/plain;charset=UTF-8" if media_type is None else media_type

        if isinstance(attachment, str):
            body = attachment
        elif isinstance(attachment, TextIOBase):
            body = attachment.read()
        elif isinstance(attachment, bytes | bytearray | BufferedIOBase):
            if isinstance(attachment, bytes):
                body_bytes = attachment
            elif isinstance(attachment, bytearray):
                body_bytes = bytes(attachment)
            elif isinstance(attachment, BufferedIOBase):
                body_bytes = attachment.read()
            else:  # pragma: no cover
                body_bytes = b""

            body = b64encode(body_bytes).decode("ascii")
        else:
            body = str(attachment)

        hook_handler.pytest_cuke_message(
            config=config,
            message=Message(
                attachment=Attachment(
                    test_step_id=active_test_step_id,
                    test_case_started_id=current_test_case_start.id,
                    media_type=_media_type,
                    file_name=str(file_name) if file_name is not None else None,
                    content_encoding=content_encoding,
                    body=body,
                )
            ),
        )

    def check_npm_and_cucumber_packages(self) -> None:
        if not check_npm():
            pytest.exit("Npm wasn't found in the environment so unable generate html report")

        if not any(
            [
                check_npm_package(self.npm_formatter_package, global_install=True),
                check_npm_package(self.npm_formatter_package),
            ]
        ):
            pytest.exit(f"Npm package '{self.npm_formatter_package}' wasn't found so unable generate html report")


class MessageSessionFinishHookAdapter:
    def __init__(self, message_plugin: MessagePlugin | None = None) -> None:
        self.message_plugin = message_plugin

    def bind(self, message_plugin: MessagePlugin) -> None:
        self.message_plugin = message_plugin

    def _run(self, session: Session, exitstatus: int | ExitCode) -> Generator[None, Any, Any]:
        message_plugin = self.message_plugin
        if message_plugin is None:
            yield
            return
        yield from message_plugin._pytest_sessionfinish(session, exitstatus)

    @hookimpl(hookwrapper=True, tryfirst=True)
    def pytest_sessionfinish(self, session: Session, exitstatus: int | ExitCode) -> Generator[None, Any, Any]:
        yield from self._run(session, exitstatus)


def message_session_finish_hook(message_plugin: MessagePlugin | None = None) -> MessageSessionFinishHookAdapter:
    return MessageSessionFinishHookAdapter(message_plugin)
