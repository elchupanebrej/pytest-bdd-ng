"""Cucumber Messages streaming and HTML report plugin."""

from __future__ import annotations

import json
import logging
import os
import re
import sys
import tempfile
import traceback
from base64 import b64encode
from inspect import getfile, getsourcelines
from io import BufferedIOBase, TextIOBase
from pathlib import Path
from platform import machine, processor, system, version
from pprint import pformat
from queue import Empty, Queue
from threading import Event, Thread
from time import sleep, time_ns
from typing import TYPE_CHECKING, Any, ClassVar, cast

import chevron
import pytest
from attr import attrib, attrs
from ci_environment import detect_ci_environment
from filelock import FileLock
from pydantic import ValidationError
from pytest import ExitCode, hookimpl

from messages import (
    Attachment,
    Ci,
    ContentEncoding,
    Duration,
    ExceptionMessage,
    Hook,
    Location,
    Meta,
    ParameterType,
    Product,
    Source,
    SourceReference,
    Status,
    TestCase,
    TestCaseFinished,
    TestCaseStarted,
    TestRunFinished,
    TestRunStarted,
    TestStep,
    TestStepFinished,
    TestStepResult,
    TestStepStarted,
    Timestamp,
    UndefinedParameterType,
)
from messages import Envelope as Message
from pytest_cuke.allure_conversion import AllureConversionError, convert_allure_messages
from pytest_cuke.compatibility.path import relpath
from pytest_cuke.compatibility.pytest import (
    Config,
    FixtureDef,
    FixtureRequest,
    Parser,
    get_config_root_path,
    get_metafunc_call_arg,
    is_set,
)
from pytest_cuke.model.execution_steps import execution_steps
from pytest_cuke.model.message_converter import feature_to_gherkin_document, scenario_message_id, scenario_to_pickle
from pytest_cuke.model.run_access import get_run_context
from pytest_cuke.npm_resource import check_npm, check_npm_package, find_resource
from pytest_cuke.packaging import get_distribution_version
from pytest_cuke.steps import Matcher
from pytest_cuke.utils import PytestBDDIdGeneratorHandler, deepattrgetter

if TYPE_CHECKING:
    from collections.abc import Callable, Generator

    from cucumber_expressions.parameter_type_registry import ParameterTypeRegistry
    from pytest import Session

    from pytest_cuke.compatibility.pytest import Item, Metafunc
    from pytest_cuke.model import Feature, Step


@attrs(eq=False)
class MessagePlugin:
    config: Config = attrib()
    allure_output_path: Path | None = attrib(default=None)
    parameter_type_registry: set[int] = attrib(factory=set)
    hook_registry: set[int] = attrib(factory=set)
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
    def current_test_case_start(self) -> TestCaseStarted | None:
        return cast("TestCaseStarted | None", self._get_scenario_state("test_case_started", None))

    @current_test_case_start.setter
    def current_test_case_start(self, value: TestCaseStarted | None) -> None:
        self._set_scenario_state("test_case_started", value)

    def __attrs_post_init__(self) -> None:
        messages_path = self._configured_output("cuke_messages_ndjson")
        html_path = self._configured_output("cuke_html")
        allure_path = self._configured_output("cuke_allure")
        self.allure_output_path = Path(allure_path) if allure_path is not None else None
        self.is_disabled = all(
            [
                messages_path is None,
                html_path is None,
                allure_path is None,
            ]
        )

        if self.is_disabled:
            return

        self.is_messages_file_temp = messages_path is None
        if self.is_messages_file_temp:
            handle, messages_file_path_raw = tempfile.mkstemp()
            os.close(handle)
            self.messages_file_path = Path(messages_file_path_raw)
        else:
            if messages_path is None:
                raise RuntimeError("A configured Messages output path is missing.")
            self.messages_file_path = Path(messages_path)

        if html_path is not None:
            self.check_npm_and_cucumber_packages()

    def start_process_messages_thread(self) -> None:
        self.process_messages_io_queue: Queue[str] = Queue()
        self.process_messages_stop_event = Event()
        self.process_messages_thread = Thread(
            target=type(self).process_messages,
            args=(
                self.process_messages_io_queue,
                self.process_messages_stop_event,
                self.messages_file_path,
            ),
            daemon=True,
        )
        self.process_messages_thread.start()
        sleep(0)

    def finish_process_messages_thread(self) -> None:
        self.process_messages_io_queue.join()
        self.process_messages_stop_event.set()
        self.process_messages_thread.join()

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
                            Message.model_validate(validation_payload)
                        except (ValidationError, ValueError):
                            logging.exception("Failed to parse:\n%s\n", pformat(message_json), exc_info=True)
                        else:
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
            dest="cuke_allure",
            metavar="dir",
            default=None,
            help="Allure result directory; write native results while pytest executes scenarios.",
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

                if is_set(feature) and feature.uri not in feature_registry:
                    feature_registry.add(feature.uri)
                    if feature.source_content is not None:
                        config.hook.pytest_cuke_message(
                            config=config,
                            message=Message(
                                source=Source(
                                    uri=feature.uri or feature.filename or "",
                                    data=feature.source_content,
                                    media_type=feature.source_media_type or "text/x.cucumber.gherkin+plain",
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
                if is_set(scenario) and id(scenario) not in pickle_registry:
                    pickle_registry.add(id(scenario))
                    feature_uri = feature.uri or feature.filename or feature.name if is_set(feature) else ""
                    config.hook.pytest_cuke_message(
                        config=config,
                        message=Message(
                            pickle=scenario_to_pickle(
                                scenario,
                                uri=feature_uri,
                                default_id=f"{feature_uri}#{call.id}",
                                feature=feature if is_set(feature) else None,
                            )
                        ),
                    )

    def pytest_cuke_message(self, config: Config, message: Message) -> None:
        if self.is_disabled:
            return
        message_data = message.model_dump(mode="json", exclude_none=True, by_alias=True)
        if message.test_step_finished is not None:
            step_id = message.test_step_finished.test_step_id
            stack_trace = self.current_test_step_exception_traces.get(step_id)
            if stack_trace:
                result = message_data["testStepFinished"]["testStepResult"]
                exception = result.get("exception")
                if isinstance(exception, dict):
                    exception["stackTrace"] = stack_trace
        message_json = json.dumps(message_data, ensure_ascii=False)
        self.process_messages_io_queue.put_nowait(message_json)

    def _get_current_test_case(self) -> TestCase:
        if self.current_test_case is None:
            raise RuntimeError("There is no active pytest-cuke test case.")
        return self.current_test_case

    def _get_current_test_case_start(self) -> TestCaseStarted:
        if self.current_test_case_start is None:
            raise RuntimeError("There is no active pytest-cuke test case start event.")
        return self.current_test_case_start

    def pytest_runtestloop(self, session: Session) -> None:
        if self.is_disabled:
            return
        config = session.config
        hook_handler = config.hook

        hook_handler.pytest_cuke_message(
            config=config,
            message=Message(test_run_started=TestRunStarted(timestamp=self.get_timestamp())),
        )

    def pytest_sessionstart(self, session: Session) -> None:
        if self.is_disabled:
            return

        self.start_process_messages_thread()

        config = session.config
        hook_handler = config.hook

        hook_handler.pytest_cuke_message(
            config=config,
            message=Message(
                meta=Meta(
                    protocol_version="24.0.0",
                    implementation=Product(name="pytest-cuke", version=str(get_distribution_version("pytest-cuke"))),
                    runtime=Product(name="Python", version=sys.version),
                    os=Product(name=system(), version=version()),
                    cpu=Product(name=machine(), version=processor()),
                    ci=Ci.model_validate(obj) if (obj := detect_ci_environment(os.environ)) is not None else None,
                ),
            ),
        )

    def pytest_sessionfinish(self, session: Session, exitstatus: int | ExitCode) -> None:
        if self.is_disabled:
            return
        config = session.config
        hook_handler = config.hook

        is_testrun_success = (isinstance(exitstatus, int) and exitstatus == 0) or exitstatus is ExitCode.OK
        hook_handler.pytest_cuke_message(
            config=config,
            message=Message(
                test_run_finished=TestRunFinished(
                    timestamp=self.get_timestamp(),
                    success=is_testrun_success,
                )
            ),
        )

        self.finish_process_messages_thread()
        try:
            if self._configured_output("cuke_html") is not None:
                self.generate_html_report()
            if self.allure_output_path is not None:
                try:
                    convert_allure_messages(self.messages_file_path, self.allure_output_path)
                except AllureConversionError as error:
                    print(f"pytest-cuke Allure conversion failed: {error}", file=sys.stderr)
                    session.exitstatus = ExitCode.USAGE_ERROR
        finally:
            if self.is_messages_file_temp and self.messages_file_path.exists():
                os.unlink(self.messages_file_path)

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
                            uri=relpath(
                                getfile(func),
                                str(get_config_root_path(config)),
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
        while step_registry is not None:
            for step_definition in step_registry:
                if id(step_definition) not in seen_steps:
                    seen_steps.add(id(step_definition))
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
                        break

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

        test_steps = []
        previous_step = None

        self.current_test_case_step_id_to_step_mapping = {}
        self.current_test_case_step_order = []
        self.current_finished_test_step_ids = set()
        self.current_test_step_start_timestamps = {}
        self.current_active_test_step_id = None
        self.current_test_step_exception_traces = {}
        feature_uri = feature.uri or feature.filename or feature.name
        callspec_id = getattr(getattr(request.node, "callspec", None), "id", "")
        fallback_id = f"{feature_uri}#{callspec_id}" if callspec_id else ""
        scenario_id = scenario_message_id(scenario, uri=feature_uri, default_id=fallback_id)

        for step_index, step in enumerate(execution_steps(feature, scenario)):
            try:
                step_definition = hook_handler.pytest_cuke_match_step_definition_to_step(
                    request=request,
                    feature=feature,
                    scenario=scenario,
                    step=step,
                    previous_step=previous_step,
                )
            except Matcher.MatchNotFoundError:
                step_definition_ids = []
            else:
                step_definition_ids = [step_definition.as_message(config).id]
            finally:
                previous_step = step

            test_step = TestStep(
                id=cast("PytestBDDIdGeneratorHandler", config).pytest_cuke_id_generator.get_next_id(),
                pickle_step_id=(
                    f"{scenario_id}-step-{step_index}"
                    if scenario.source_ast_node_ids
                    else step.id or f"{scenario_id}-step-{step_index}"
                ),
                step_definition_ids=step_definition_ids,
            )
            test_steps.append(test_step)
            self.current_test_case_step_order.append(test_step)
            self.current_test_case_step_id_to_step_mapping[id(step)] = test_step

        current_test_case = TestCase(
            id=cast("PytestBDDIdGeneratorHandler", config).pytest_cuke_id_generator.get_next_id(),
            pickle_id=scenario_id,
            test_steps=test_steps,
        )
        self.current_test_case = current_test_case
        run_context = get_run_context(config)
        if run_context is not None:
            active_run = run_context.active_scenario_run
            if active_run is not None and active_run.nodeid == request.node.nodeid:
                run_context.set_test_case(
                    test_case_id=current_test_case.id,
                    test_step_ids=[test_step.id for test_step in test_steps],
                    test_steps=test_steps,
                )

        hook_handler.pytest_cuke_message(
            config=config,
            message=Message(test_case=current_test_case),
        )

    def pytest_cuke_before_scenario(self, request: FixtureRequest, feature: Feature, scenario: Any) -> None:
        if self.is_disabled:
            return
        config = request.config
        hook_handler = config.hook
        current_test_case = self._get_current_test_case()

        self.current_test_case_start = TestCaseStarted(
            attempt=getattr(request.node, "execution_count", 0),
            id=cast("PytestBDDIdGeneratorHandler", config).pytest_cuke_id_generator.get_next_id(),
            test_case_id=current_test_case.id,
            worker_id=os.environ.get("PYTEST_XDIST_WORKER", "master"),
            timestamp=self.get_timestamp(),
        )
        run_context = get_run_context(config)
        if run_context is not None:
            active_run = run_context.active_scenario_run
            if active_run is not None and active_run.nodeid == request.node.nodeid:
                run_context.set_attempt_id(self.current_test_case_start.id)

        hook_handler.pytest_cuke_message(
            config=config,
            message=Message(test_case_started=self.current_test_case_start),
        )

    def pytest_cuke_after_scenario(self, request: FixtureRequest, feature: Feature, scenario: Any) -> None:
        if self.is_disabled:
            return
        config = request.config

        current_test_case_start = self.current_test_case_start
        if current_test_case_start is None:
            self._reset_current_test_case()
            return

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

            config.hook.pytest_cuke_message(
                config=config,
                message=Message(
                    test_case_finished=TestCaseFinished(
                        test_case_started_id=current_test_case_start.id,
                        timestamp=self.get_timestamp(),
                        will_be_retried=False,
                    )
                ),
            )
        finally:
            self._reset_current_test_case()

    def _reset_current_test_case(self) -> None:
        self.current_test_case = None
        self.current_test_case_start = None
        self.current_test_case_step_id_to_step_mapping = {}
        self.current_test_case_step_order = []
        self.current_finished_test_step_ids = set()
        self.current_test_step_start_timestamps = {}
        self.current_active_test_step_id = None
        self.current_test_step_exception_traces = {}

    def pytest_cuke_before_step(
        self, request: FixtureRequest, feature: Feature, scenario: Any, step: Step, step_func: Any
    ) -> None:
        if self.is_disabled:
            return
        config = request.config
        current_test_case_start = self._get_current_test_case_start()

        step_definition = self.current_test_case_step_id_to_step_mapping[id(step)]

        self._start_test_step(
            config=config,
            test_case_started=current_test_case_start,
            test_step=step_definition,
        )

    def pytest_cuke_after_step(
        self, request: FixtureRequest, feature: Feature, scenario: Any, step: Step, step_func: Any
    ) -> None:
        if self.is_disabled:
            return
        config = request.config
        current_test_case_start = self._get_current_test_case_start()

        step_definition = self.current_test_case_step_id_to_step_mapping[id(step)]
        self._finish_test_step(
            config=config,
            test_case_started=current_test_case_start,
            test_step=step_definition,
            start_timestamp=self.current_test_step_start_timestamps[step_definition.id],
            status=Status.passed,
        )

    def pytest_cuke_step_error(
        self,
        request: FixtureRequest,
        feature: Feature,
        scenario: Any,
        step: Step,
        step_func: Any,
        step_func_args: dict[str, Any],
        exception: BaseException,
        step_definition: Any,
        tolerated: bool = False,
    ) -> None:
        if self.is_disabled:
            return
        config = request.config
        current_test_case_start = self._get_current_test_case_start()

        step_definition = self.current_test_case_step_id_to_step_mapping[id(step)]
        status = (
            Status.skipped if isinstance(exception, (pytest.skip.Exception, pytest.xfail.Exception)) else Status.failed
        )
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
        feature: Feature,
        scenario: Any,
        step: Step,
        exception: Exception,
    ) -> None:
        if self.is_disabled:
            return
        config = request.config
        current_test_case_start = self._get_current_test_case_start()
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
    ) -> None:
        if exception_stack_trace is not None:
            self.current_test_step_exception_traces[test_step.id] = exception_stack_trace
        finish_timestamp = self.get_timestamp()
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
            self.current_test_step_exception_traces.pop(test_step.id, None)
        self.current_test_step_start_timestamps.pop(test_step.id, None)
        if self.current_active_test_step_id == test_step.id:
            self.current_active_test_step_id = None
        self.current_finished_test_step_ids.add(test_step.id)

    def pytest_cuke_attach(
        self,
        request: FixtureRequest,
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
        active_test_step_id = self.current_active_test_step_id
        if active_test_step_id not in self.current_test_step_start_timestamps:
            active_test_step_id = None

        if isinstance(attachment, str | TextIOBase):
            content_encoding = ContentEncoding.identity
            _media_type = "text/plain;charset=UTF-8" if media_type is None else media_type
        elif isinstance(attachment, bytes | bytearray | BufferedIOBase):
            content_encoding = ContentEncoding.base64
            _media_type = "application/octet-stream" if media_type is None else media_type
        else:
            content_encoding = ContentEncoding.identity
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
                    **({"file_name": str(file_name)} if file_name is not None else {}),
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
