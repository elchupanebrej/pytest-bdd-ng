import json
import logging
import os
import re
import sys
import tempfile
from base64 import b64encode
from contextlib import suppress
from dataclasses import dataclass
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
from _pytest.mark import Mark
from attr import attrib, attrs
from ci_environment import detect_ci_environment
from cucumber_messages import (  # type:ignore[attr-defined, import-untyped]
    Attachment,
    AttachmentContentEncoding,
    Ci,
    Duration,
    Group,
    Hook,
    Location,
    Meta,
    ParameterType,
    Product,
    Source,
    SourceReference,
    StepMatchArgument,
    StepMatchArgumentsList,
    TestCase,
    TestCaseFinished,
    TestCaseStarted,
    TestRunFinished,
    TestRunStarted,
    TestStep,
    TestStepFinished,
    TestStepResult,
    TestStepResultStatus,
    TestStepStarted,
    Timestamp,
)
from cucumber_messages import Envelope as Message  # type:ignore[attr-defined]
from filelock import FileLock

from pytest_bdd.compatibility.path import relpath
from pytest_bdd.compatibility.pytest import (
    PYTEST7,
    Config,
    FixtureDef,
    FixtureLookupError,
    FixtureRequest,
    get_config_root_path,
    get_metafunc_call_arg,
    is_set,
    is_testrun_success,
)
from pytest_bdd.model.message_converter import envelope_from_dict, envelope_to_dict, message_converter
from pytest_bdd.model.message_extension import get_payload_kind, has_single_payload
from pytest_bdd.model.message_outcome_mapping import OutcomeMappingRule, resolve_outcome_mapping
from pytest_bdd.model.message_validation import (
    default_outcome_mapping_rules,
    observed_outcome_from_envelope,
    validate_message_stream,
)
from pytest_bdd.steps import StepDefinitionManager
from pytest_bdd.tag_expression import GherkinTagExpression, MarksTagExpression
from pytest_bdd.types.protocol import HasPytestBDDIdGenerator
from pytest_bdd.util.npm_resource import check_npm, check_npm_package, find_resource
from pytest_bdd.util.packaging import get_distribution_version
from pytest_bdd.util.toolz_extra import deepattrgetter

if TYPE_CHECKING:
    from collections.abc import Callable

    from cucumber_expressions.parameter_type_registry import ParameterTypeRegistry

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class HookRegistration:
    hook_message_id: str
    expression: str
    kind: str


@attrs(eq=False)
class GherkinMessageReporter:
    config: Config = attrib()
    current_test_case: TestCase | None = attrib(default=None)
    current_test_case_step_id_to_step_mapping: dict[int, TestStep] | None = attrib(default=None)
    parameter_type_registry: ClassVar[set[int]] = set()
    hook_registry: ClassVar[set[int]] = set()
    hook_registration_registry: ClassVar[dict[int, HookRegistration]] = {}
    npm_formatter_package = "@cucumber/html-formatter"
    plugin_name = "pytest-bdd-internal-gherkin-message-reporter"

    process_messages_io_queue: Queue[str]
    process_messages_stop_event: Event
    process_messages_thread: Thread
    messages_file_path: Path
    is_messages_file_temp: bool
    current_test_case_start: TestCaseStarted | None
    current_active_test_step_id: str | None
    current_step_started_ids: dict[str, str]
    current_attempt_context: dict[str, str | int] | None
    current_test_case_step_start_timestamp: Timestamp
    current_test_case_step_finish_timestamp: Timestamp
    _disabled_warning_emitted: bool
    _run_id: str | None
    _outcome_mapping_rules: list[OutcomeMappingRule]
    _mapping_diagnostics_count: int

    def __attrs_post_init__(self):
        self._disabled_warning_emitted = False
        self._run_id = None
        self.current_test_case_start = None
        self.current_active_test_step_id = None
        self.current_step_started_ids = {}
        self.current_attempt_context = None
        self.current_test_case_step_id_to_step_mapping = None
        self._outcome_mapping_rules = default_outcome_mapping_rules()
        self._mapping_diagnostics_count = 0

        self.is_disabled = all(
            [
                self.config.option.messages_ndjson_path is None,
                self.config.option.cucumber_html_path is None,
            ],
        )

        if self.is_disabled:
            return

        self.is_messages_file_temp = self.config.option.messages_ndjson_path is None
        if self.is_messages_file_temp:
            handle, messages_file_path_raw = tempfile.mkstemp()
            os.close(handle)
            self.messages_file_path = Path(messages_file_path_raw)
        else:
            self.messages_file_path = self._resolve_output_path(self.config.option.messages_ndjson_path)
            self.messages_file_path.parent.mkdir(parents=True, exist_ok=True)

        if self.config.option.cucumber_html_path is not None:
            html_report_path = self._resolve_output_path(self.config.option.cucumber_html_path)
            html_report_path.parent.mkdir(parents=True, exist_ok=True)
            self.config.option.cucumber_html_path = str(html_report_path)
            self.check_npm_and_cucumber_packages()

    def _resolve_output_path(self, output_path: str) -> Path:
        path = Path(output_path)
        if not path.is_absolute():
            path = get_config_root_path(self.config) / path
        return path.resolve()

    def start_process_messages_thread(self):
        self.process_messages_io_queue = Queue()
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

    def finish_process_messages_thread(self):
        self.process_messages_io_queue.join()
        self.process_messages_stop_event.set()
        self.process_messages_thread.join()

    def _emit_disabled_warning_once(self) -> None:
        if self._disabled_warning_emitted:
            return
        self._disabled_warning_emitted = True
        logger.warning("Message reporting disabled; message-output guarantees were skipped for this run.")

    def _emit_envelope(self, config: Config, message: Message) -> None:
        if self.is_disabled:
            return
        if not has_single_payload(message):
            message_text = "Envelope must include exactly one payload"
            raise TypeError(message_text)
        observed_outcome = observed_outcome_from_envelope(message)
        if observed_outcome is not None:
            selected_rule, is_ambiguous = resolve_outcome_mapping(
                self._outcome_mapping_rules,
                outcome_scope=observed_outcome.outcome_scope,
                outcome_status=observed_outcome.outcome_status,
            )
            if is_ambiguous:
                self._mapping_diagnostics_count += 1
                logger.warning(
                    "Ambiguous outcome mapping for %s:%s",
                    observed_outcome.outcome_scope,
                    observed_outcome.outcome_status,
                )
            elif selected_rule is None:
                self._mapping_diagnostics_count += 1
                logger.warning(
                    "No outcome mapping rule for %s:%s",
                    observed_outcome.outcome_scope,
                    observed_outcome.outcome_status,
                )
        config.hook.pytest_bdd_message(config=config, message=message)

    def _emit_lifecycle(self, config: Config, payload_kind: str, payload: object) -> None:
        self._emit_envelope(config, Message(**{payload_kind: payload}))

    @staticmethod
    def _check_derived_output_consistency(envelopes: list[Message]) -> bool:
        payload_kinds = [get_payload_kind(envelope) for envelope in envelopes]
        return "test_run_started" in payload_kinds and "test_run_finished" in payload_kinds

    @staticmethod
    def process_messages(queue: Queue, stop_event: Event, messages_file_path: str | Path):
        messages_path = Path(messages_file_path)
        with tempfile.TemporaryDirectory() as tmpdirname:
            last_enter = False
            while not (stop_event.is_set() and last_enter):  # give one more enter to take all left messages
                if stop_event.is_set():
                    last_enter = True

                lines = []
                while not queue.empty():
                    try:
                        message_json = queue.get(timeout=1)
                    except Empty:
                        sleep(0)
                        continue

                    try:
                        envelope_from_dict(json.loads(message_json))
                    except (TypeError, ValueError):
                        logger.exception("Failed to parse:\n%s\n", pformat(message_json))
                    else:
                        lines.append(f"{message_json}\n")
                    finally:
                        queue.task_done()
                    sleep(0)

                if not lines:
                    sleep(0)
                    continue

                lock_file = str(Path(tmpdirname, f"{messages_path}.lock"))
                try:
                    messages_path.parent.mkdir(parents=True, exist_ok=True)
                    with FileLock(lock_file), messages_path.open(mode="at+", buffering=1, encoding="utf-8") as f:
                        f.writelines(lines)
                        f.flush()
                except OSError:
                    logger.exception("Unable to write messages to '%s'", messages_path)

    @staticmethod
    def get_timestamp():
        timestamp = time_ns()
        test_run_started_seconds = timestamp // 10**9
        test_run_started_nanos = timestamp - test_run_started_seconds * 10**9
        return Timestamp(seconds=test_run_started_seconds, nanos=test_run_started_nanos)

    def generate_html_report(self):
        if self.is_disabled:
            return
        script_path = Path(next(find_resource(self.npm_formatter_package, Path("dist") / "main.js")))
        css_path = Path(next(find_resource(self.npm_formatter_package, Path("dist") / "main.css")))
        template_path = Path(next(find_resource(self.npm_formatter_package, Path("src") / "index.mustache.html")))

        template_raw = template_path.read_text(encoding="utf-8")
        template = re.sub(r"\{\{", "{{&", template_raw)  # It is not completely in agree with documentation

        with self.messages_file_path.open(mode="r", encoding="utf-8") as f:
            messages = ",".join(f.readlines())

        html_report_path = Path(self.config.option.cucumber_html_path)
        html_report_path.parent.mkdir(parents=True, exist_ok=True)
        html_report_path.write_text(
            chevron.render(
                template,
                {
                    "css": css_path.read_text(encoding="utf-8"),
                    "script": script_path.read_text(encoding="utf-8"),
                    "messages": messages,
                },
            ),
            encoding="utf-8",
        )

    @pytest.hookimpl(hookwrapper=True)
    def pytest_generate_tests(self, metafunc):
        yield
        if self.is_disabled:
            return

        if all(
            [
                "feature" in metafunc.fixturenames,
                "scenario" in metafunc.fixturenames,
                "feature_source" in metafunc.fixturenames,
                metafunc._calls,
            ],
        ):
            config = metafunc.config

            feature_registry = set()
            pickle_registry = set()
            for call in metafunc._calls:
                feature = get_metafunc_call_arg(call, "feature")
                pickle = get_metafunc_call_arg(call, "scenario")
                feature_source: Source = get_metafunc_call_arg(call, "feature_source")

                if is_set(feature) and hasattr(feature_source, "uri") and feature_source.uri not in feature_registry:
                    feature_registry.add(feature_source.uri)
                    self._emit_envelope(cast(Config, config), Message(source=feature_source))

                    self._emit_envelope(cast(Config, config), Message(gherkin_document=feature.gherkin_document))
                if is_set(pickle) and id(pickle) not in pickle_registry:
                    self._emit_envelope(cast(Config, config), Message(pickle=pickle))

    def pytest_bdd_message(
        self,
        config: Config,  # noqa: ARG002 hookspec
        message: Message,
    ):
        if self.is_disabled:
            return

        if not has_single_payload(message):
            message_text = "Cannot emit envelope with zero or multiple payloads"
            raise TypeError(message_text)

        try:
            message_json = json.dumps(envelope_to_dict(message))
        except Exception as exc:
            message_text = "Message emission failed while serializing envelope"
            raise RuntimeError(message_text) from exc

        self.process_messages_io_queue.put_nowait(message_json)

    def pytest_runtestloop(self, session: pytest.Session):
        if self.is_disabled:
            return
        config = session.config
        self._run_id = str(time_ns())
        self._emit_lifecycle(config, "test_run_started", TestRunStarted(timestamp=self.get_timestamp()))

    def pytest_sessionstart(self, session):
        if self.is_disabled:
            self._emit_disabled_warning_once()
            return

        self.start_process_messages_thread()

        config = session.config

        ci = message_converter.from_dict(obj, Ci) if (obj := detect_ci_environment(os.environ)) is not None else None

        self._emit_envelope(
            config,
            Message(
                meta=Meta(
                    protocol_version=str(get_distribution_version("cucumber-messages")),
                    implementation=Product(
                        name="pytest-bdd-ng",
                        version=str(get_distribution_version("pytest-bdd-ng")),
                    ),
                    runtime=Product(name="Python", version=sys.version),
                    os=Product(name=system(), version=version()),
                    cpu=Product(name=machine(), version=processor()),
                    ci=ci,
                ),
            ),
        )

    def pytest_sessionfinish(self, session, exitstatus):
        if self.is_disabled:
            return
        config = session.config
        self._emit_lifecycle(
            config,
            "test_run_finished",
            TestRunFinished(
                timestamp=self.get_timestamp(),
                success=is_testrun_success(exitstatus),
            ),
        )

        self.finish_process_messages_thread()

        envelopes: list[Message] = []
        if self.messages_file_path.exists():
            for line in self.messages_file_path.read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                envelopes.append(envelope_from_dict(json.loads(line)))
        validation_result = validate_message_stream(
            envelopes,
            latest_protocol_version=str(get_distribution_version("cucumber-messages")),
            track_coverage=getattr(self.config.option, "messages_coverage", False),
        )
        if not validation_result.is_valid:
            logger.error(
                "Canonical message stream validation failed with %s violation(s).",
                len(validation_result.violations),
            )
        if self._mapping_diagnostics_count:
            logger.error(
                "Detected %s mapping diagnostic warning(s) in message emission flow.", self._mapping_diagnostics_count
            )
        if not self._check_derived_output_consistency(envelopes):
            logger.error("Derived-output consistency check failed: required run lifecycle envelopes are incomplete.")

        if self.config.option.cucumber_html_path is not None:
            self.generate_html_report()
        if self.is_messages_file_temp:
            Path(self.messages_file_path).unlink()

    @pytest.hookimpl(hookwrapper=True)
    def pytest_fixture_setup(self, fixturedef: FixtureDef, request):
        if self.is_disabled:
            yield
            return
        func = fixturedef.func
        func_id = id(func)

        if func_id in self.hook_registry:
            yield
            return

        config = request.config

        if hasattr(func, "__pytest_bdd_is_hook__"):
            self.hook_registry.add(func_id)

            hook_name = getattr(func, "__pytest_bdd_hook_name__", None)
            hook_expression = getattr(func, "__pytest_bdd_hook_expression__", None)
            hook_kind = getattr(func, "__pytest_bdd_hook_kind__", "tag")

            hook_message_id = cast(HasPytestBDDIdGenerator, config).pytest_bdd_id_generator.get_next_id()
            hook_message = Hook(
                id=hook_message_id,
                **({"name": hook_name} if hook_name is not None else {}),
                source_reference=SourceReference(
                    uri=relpath(
                        getfile(func),
                        str(get_config_root_path(cast(Config, config))),
                    ),
                    location=Location(line=getsourcelines(func)[1]),
                ),
                **({"tag_expression": hook_expression} if hook_expression is not None else {}),
            )
            type(self).hook_registration_registry[func_id] = HookRegistration(
                hook_message_id=hook_message_id,
                expression="" if hook_expression is None else str(hook_expression),
                kind=str(hook_kind),
            )

            self._emit_envelope(
                config,
                Message(
                    hook=hook_message,
                ),
            )

        yield

    @pytest.hookimpl(hookwrapper=True)
    def pytest_runtest_setup(self, item):
        yield
        if self.is_disabled:
            return

        session = item.session
        config: Config | HasPytestBDDIdGenerator = session.config  # https://github.com/python/typing/issues/213

        hook_handler = cast(Config, config).hook

        request = item._request
        try:
            scenario = request.getfixturevalue("scenario")
            feature = request.getfixturevalue("feature")
        except FixtureLookupError:
            return

        self._report_step_definitions(config, request)
        self._register_parameter_types(config, request)

        test_steps = []
        previous_step = None

        self.current_test_case_step_id_to_step_mapping = {}

        test_steps.extend(
            [
                TestStep(
                    id=cast(HasPytestBDDIdGenerator, config).pytest_bdd_id_generator.get_next_id(),
                    hook_id=hook_registration.hook_message_id,
                )
                for hook_registration in self._iter_matching_hook_registrations(request=request, scenario=scenario)
            ]
        )

        for step in scenario.steps:
            try:
                step_definition = hook_handler.pytest_bdd_match_step_definition_to_step(
                    request=request,
                    feature=feature,
                    scenario=scenario,
                    step=step,
                    previous_step=previous_step,
                )
            except StepDefinitionManager.Matcher.MatchNotFoundError:  # noqa:PERF203
                pass
            else:
                step_match_arguments_lists = self._build_step_match_arguments_lists(
                    request=request,
                    step_definition=step_definition,
                    step_text=step.text,
                )
                test_step = TestStep(
                    id=cast(HasPytestBDDIdGenerator, config).pytest_bdd_id_generator.get_next_id(),
                    pickle_step_id=step.id,
                    step_definition_ids=[step_definition.as_message(config).id],
                    **(
                        {"step_match_arguments_lists": step_match_arguments_lists} if step_match_arguments_lists else {}
                    ),
                )
                test_steps.append(test_step)
                self.current_test_case_step_id_to_step_mapping[id(step)] = test_step
            finally:
                previous_step = step

        self.current_test_case = TestCase(
            id=cast(HasPytestBDDIdGenerator, config).pytest_bdd_id_generator.get_next_id(),
            pickle_id=scenario.id,
            test_steps=test_steps,
        )

        self._emit_lifecycle(cast(Config, config), "test_case", self.current_test_case)

    def _report_step_definitions(self, config, request):
        step_registry = request.getfixturevalue("step_registry")
        seen_steps = set()
        while step_registry is not None:
            for step_definition in step_registry:
                if id(step_definition) not in seen_steps:
                    seen_steps.add(id(step_definition))
                    self._emit_envelope(config, Message(step_definition=step_definition.as_message(config=config)))
            step_registry = step_registry.parent

    def _iter_matching_hook_registrations(self, request: FixtureRequest, scenario: Any):
        for hook_registration in type(self).hook_registration_registry.values():
            if self._hook_expression_matches(
                request=request,
                scenario=scenario,
                expression=hook_registration.expression,
                kind=hook_registration.kind,
            ):
                yield hook_registration

    def _hook_expression_matches(
        self,
        *,
        request: FixtureRequest,
        scenario: Any,
        expression: str,
        kind: str,
    ) -> bool:
        if not expression.strip():
            return True

        try:
            if kind == "mark":
                parsed_expression = MarksTagExpression.parse(expression)
                return bool(parsed_expression.evaluate(list(request.node.iter_markers())))
            if kind == "tag":
                parsed_expression = GherkinTagExpression.parse(expression)
                scenario_tags = []
                for tag in scenario.tags:
                    mark = Mark(tag.name, args=(), kwargs={})
                    if PYTEST7:
                        mark._ispytest = True
                    scenario_tags.append(mark)
                return bool(parsed_expression.evaluate(scenario_tags))
        except Exception:  # noqa: BLE001
            return False

        return False

    def _build_step_match_arguments_lists(
        self,
        *,
        request: FixtureRequest,
        step_definition: StepDefinitionManager.Definition,
        step_text: str,
    ) -> list[StepMatchArgumentsList]:
        from pytest_bdd.parsers import _CucumberExpression

        parser = step_definition.parser

        if isinstance(parser, _CucumberExpression):
            matches = parser.rebuild_expression_in_test_context(request).match(step_text)
            if matches:

                def build_group(g) -> Group:
                    return Group(
                        **({"start": g.start} if getattr(g, "start", None) is not None else {}),
                        **({"value": g.value} if getattr(g, "value", None) is not None else {}),
                        children=[build_group(c) for c in (getattr(g, "children", []) or [])],
                    )

                step_match_arguments = []
                for i, match in enumerate(matches):
                    anon_groups = (
                        list(step_definition.anonymous_group_names) if step_definition.anonymous_group_names else []
                    )
                    parameter_name = anon_groups[i] if i < len(anon_groups) else None
                    step_match_arguments.append(
                        StepMatchArgument(
                            group=build_group(match.group),
                            **({"parameter_type_name": str(parameter_name)} if parameter_name is not None else {}),
                        )
                    )
                return [StepMatchArgumentsList(step_match_arguments=step_match_arguments)]

        parsed_arguments = (
            step_definition.parser.parse_arguments(
                request,
                step_text,
                anonymous_group_names=step_definition.anonymous_group_names,
            )
            or {}
        )
        if not parsed_arguments:
            return []

        parsed_step_match_arguments: list[StepMatchArgument] = []
        for parameter_name, parameter_value in parsed_arguments.items():
            parameter_value_text = "" if parameter_value is None else str(parameter_value)
            parameter_start_index = step_text.find(parameter_value_text) if parameter_value_text else -1
            group = Group(
                **({"start": parameter_start_index} if parameter_start_index >= 0 else {}),
                **({"value": parameter_value_text} if parameter_value_text else {}),
            )
            parsed_step_match_arguments.append(
                StepMatchArgument(
                    group=group,
                    **({"parameter_type_name": str(parameter_name)} if parameter_name is not None else {}),
                )
            )
        return [StepMatchArgumentsList(step_match_arguments=parsed_step_match_arguments)]

    def _build_parameter_type_source_reference(self, config: Config, parameter_type: Any):
        transformer = getattr(parameter_type, "transformer", None)
        if transformer is None:
            return None

        with suppress(OSError, TypeError):
            source_file = getfile(transformer)
            source_line = getsourcelines(transformer)[1]
            return SourceReference(
                uri=relpath(
                    source_file,
                    str(get_config_root_path(cast(Config, config))),
                ),
                location=Location(line=source_line),
            )
        return None

    def _register_parameter_types(self, config, request):
        step_registry = request.getfixturevalue("step_registry")
        seen_steps = set()
        while step_registry is not None:
            for step_definition in step_registry:
                if id(step_definition) not in seen_steps:
                    parameter_type_registry_getter: Callable[[FixtureRequest], ParameterTypeRegistry] = deepattrgetter(
                        "_get_parameter_type_registry",
                        default=None,
                    )(step_definition.parser)[0]

                    if parameter_type_registry_getter is None:
                        continue

                    parameter_type_registry = parameter_type_registry_getter(request)

                    parameter_types = {
                        id(parameter_type): parameter_type for parameter_type in parameter_type_registry.parameter_types
                    }

                    not_yet_registered_parameter_types = {
                        key: parameter_type
                        for key, parameter_type in parameter_types.items()
                        if key not in self.parameter_type_registry
                    }

                    for parameter_type in not_yet_registered_parameter_types.values():
                        parameter_type_source_reference = self._build_parameter_type_source_reference(
                            cast(Config, config),
                            parameter_type,
                        )
                        self._emit_envelope(
                            config,
                            Message(
                                parameter_type=ParameterType(
                                    name=parameter_type.name,
                                    regular_expressions=parameter_type.regexps,
                                    prefer_for_regular_expression_match=parameter_type._prefer_for_regexp_match,
                                    use_for_snippets=parameter_type._use_for_snippets,
                                    id=cast(HasPytestBDDIdGenerator, config).pytest_bdd_id_generator.get_next_id(),
                                    **(
                                        {"source_reference": parameter_type_source_reference}
                                        if parameter_type_source_reference is not None
                                        else {}
                                    ),
                                ),
                            ),
                        )
                    type(self).parameter_type_registry |= not_yet_registered_parameter_types.keys()
            step_registry = step_registry.parent

    def pytest_bdd_before_scenario(
        self,
        request,
        feature,  # noqa: ARG002 hookspec
        scenario,  # noqa: ARG002 hookspec
    ):
        if self.is_disabled:
            return
        config = request.config
        if self.current_test_case is None:
            return
        attempt_index = getattr(request.node, "execution_count", 0)
        worker_id = os.environ.get("PYTEST_XDIST_WORKER", "master")
        self.current_test_case_start = TestCaseStarted(
            attempt=attempt_index,
            id=cast(HasPytestBDDIdGenerator, config).pytest_bdd_id_generator.get_next_id(),
            test_case_id=self.current_test_case.id,
            worker_id=worker_id,
            timestamp=self.get_timestamp(),
        )
        self.current_attempt_context = {
            "scenario_attempt_id": self.current_test_case_start.id,
            "attempt_index": attempt_index,
            "worker_id": worker_id,
        }
        self._emit_lifecycle(config, "test_case_started", self.current_test_case_start)

    def pytest_bdd_after_scenario(
        self,
        request,
        feature,  # noqa: ARG002 hookspec
        scenario,  # noqa: ARG002 hookspec
    ):
        if self.is_disabled:
            return
        if self.current_test_case_start is None:
            return
        config = request.config
        test_case_start = self.current_test_case_start
        self._emit_lifecycle(
            config,
            "test_case_finished",
            TestCaseFinished(
                test_case_started_id=test_case_start.id,
                timestamp=self.get_timestamp(),
                will_be_retried=False,
            ),
        )
        self.current_test_case = None
        self.current_test_case_start = None
        self.current_active_test_step_id = None
        self.current_step_started_ids = {}

    def pytest_bdd_before_step(
        self,
        request,
        feature,  # noqa: ARG002 hookspec
        scenario,  # noqa: ARG002 hookspec
        step,
        step_func,  # noqa: ARG002 hookspec
    ):
        if self.is_disabled:
            return
        if self.current_test_case_step_id_to_step_mapping is None or self.current_test_case_start is None:
            return
        config = request.config

        # TODO check behaviour if missing
        step_definition = self.current_test_case_step_id_to_step_mapping[id(step)]
        test_case_start = self.current_test_case_start

        self.current_test_case_step_start_timestamp = self.get_timestamp()
        test_step_started = TestStepStarted(
            test_case_started_id=test_case_start.id,
            timestamp=self.current_test_case_step_start_timestamp,
            test_step_id=step_definition.id,
        )
        self.current_step_started_ids[step_definition.id] = step_definition.id
        self.current_active_test_step_id = step_definition.id

        self._emit_lifecycle(config, "test_step_started", test_step_started)

    def pytest_bdd_after_step(
        self,
        request,
        feature,  # noqa: ARG002 hookspec
        scenario,  # noqa: ARG002 hookspec
        step,
        step_func,  # noqa: ARG002 hookspec
    ):
        if self.is_disabled:
            return
        if self.current_test_case_step_id_to_step_mapping is None or self.current_test_case_start is None:
            return
        config = request.config

        # TODO check behaviour if missing
        step_definition = self.current_test_case_step_id_to_step_mapping[id(step)]
        test_case_start = self.current_test_case_start
        self.current_test_case_step_finish_timestamp = self.get_timestamp()

        current_test_case_step_duration_total_nanos = (
            self.current_test_case_step_finish_timestamp.seconds * 10**9
            + self.current_test_case_step_finish_timestamp.nanos
        ) - (
            self.current_test_case_step_start_timestamp.seconds * 10**9
            + self.current_test_case_step_start_timestamp.nanos
        )
        current_test_case_step_duration_seconds = current_test_case_step_duration_total_nanos // 10**9
        current_test_case_step_duration_nanos = (
            current_test_case_step_duration_total_nanos - current_test_case_step_duration_seconds * 10**9
        )
        current_test_case_step_duration = Duration(
            seconds=current_test_case_step_duration_seconds,
            nanos=current_test_case_step_duration_nanos,
        )

        self._emit_lifecycle(
            config,
            "test_step_finished",
            TestStepFinished(
                test_case_started_id=test_case_start.id,
                timestamp=self.current_test_case_step_finish_timestamp,
                test_step_id=step_definition.id,
                test_step_result=TestStepResult(
                    duration=current_test_case_step_duration, status=TestStepResultStatus.passed
                ),
            ),
        )
        self.current_active_test_step_id = None

    def pytest_bdd_step_error(
        self,
        request,
        feature,  # noqa: ARG002 hookspec
        scenario,  # noqa: ARG002 hookspec
        step,
        step_func,  # noqa: ARG002 hookspec
        step_func_args,  # noqa: ARG002 hookspec
        exception,  # noqa: ARG002 hookspec
        step_definition,
    ):
        if self.is_disabled:
            return
        if self.current_test_case_step_id_to_step_mapping is None or self.current_test_case_start is None:
            return
        config = request.config

        # TODO check behaviour if missing
        step_definition = self.current_test_case_step_id_to_step_mapping[id(step)]
        test_case_start = self.current_test_case_start
        self.current_test_case_step_finish_timestamp = self.get_timestamp()

        current_test_case_step_duration_total_nanos = (
            self.current_test_case_step_finish_timestamp.seconds * 10**9
            + self.current_test_case_step_finish_timestamp.nanos
        ) - (
            self.current_test_case_step_start_timestamp.seconds * 10**9
            + self.current_test_case_step_start_timestamp.nanos
        )
        current_test_case_step_duration_seconds = current_test_case_step_duration_total_nanos // 10**9
        current_test_case_step_duration_nanos = (
            current_test_case_step_duration_total_nanos - current_test_case_step_duration_seconds * 10**9
        )
        current_test_case_step_duration = Duration(
            seconds=current_test_case_step_duration_seconds,
            nanos=current_test_case_step_duration_nanos,
        )

        self._emit_lifecycle(
            config,
            "test_step_finished",
            TestStepFinished(
                test_case_started_id=test_case_start.id,
                timestamp=self.current_test_case_step_finish_timestamp,
                test_step_id=step_definition.id,
                test_step_result=TestStepResult(
                    duration=current_test_case_step_duration, status=TestStepResultStatus.failed
                ),
            ),
        )
        self.current_active_test_step_id = None

    def pytest_bdd_attach(self, request, attachment, media_type, file_name):
        if self.is_disabled:
            return
        config = request.config
        test_case_start = self.current_test_case_start

        if isinstance(attachment, (str, TextIOBase)):
            content_encoding = AttachmentContentEncoding.identity
            media_type_ = "text/plain;charset=UTF-8" if media_type is None else media_type
        elif isinstance(attachment, (bytes, bytearray, BufferedIOBase)):
            content_encoding = AttachmentContentEncoding.base64
            media_type_ = "application/octet-stream" if media_type is None else media_type
        else:
            content_encoding = AttachmentContentEncoding.identity
            media_type_ = "text/plain;charset=UTF-8" if media_type is None else media_type

        if isinstance(attachment, str):
            body = attachment
        elif isinstance(attachment, TextIOBase):
            body = attachment.read()
        elif isinstance(attachment, (bytes, bytearray, BufferedIOBase)):
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

        self._emit_lifecycle(
            config,
            "attachment",
            Attachment(
                **(
                    {"test_step_id": self.current_active_test_step_id}
                    if self.current_active_test_step_id is not None
                    else {}
                ),
                **({"test_case_started_id": test_case_start.id} if test_case_start is not None else {}),
                media_type=media_type_,
                **({"file_name": str(file_name)} if file_name is not None else {}),
                content_encoding=content_encoding,
                body=body,
            ),
        )

    def check_npm_and_cucumber_packages(self):
        if not check_npm():
            pytest.exit("Npm wasn't found in the environment so unable generate html report")

        if not any(
            [
                check_npm_package(self.npm_formatter_package, global_install=True),
                check_npm_package(self.npm_formatter_package),
            ],
        ):
            pytest.exit(f"Npm package '{self.npm_formatter_package}' wasn't found so unable generate html report")
