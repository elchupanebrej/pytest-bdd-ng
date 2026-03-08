import json
import logging
import os
import re
import sys
import tempfile
from base64 import b64encode
from collections.abc import Mapping
from contextlib import suppress
from dataclasses import dataclass
from inspect import getfile, getsourcelines, signature
from io import BufferedIOBase, TextIOBase
from pathlib import Path
from platform import machine, processor, system, version
from pprint import pformat
from queue import Empty, Queue
from threading import Event, Thread
from time import sleep, time_ns
from typing import TYPE_CHECKING, Any, ClassVar, cast

import pytest
from _pytest.mark import Mark
from attr import attrib, attrs
from ci_environment import detect_ci_environment
from cucumber_messages import (  # type:ignore[attr-defined, import-untyped]
    Attachment,
    AttachmentContentEncoding,
    Ci,
    Duration,
    ExternalAttachment,
    GherkinDocument,
    Group,
    Hook,
    HookType,
    JavaMethod,
    JavaStackTraceElement,
    Location,
    Meta,
    ParameterType,
    Pickle,
    Product,
    Snippet,
    Source,
    SourceReference,
    StepMatchArgument,
    StepMatchArgumentsList,
    Suggestion,
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
    TestStepResultStatus,
    TestStepStarted,
    Timestamp,
    UndefinedParameterType,
)
from cucumber_messages import Envelope as Message  # type:ignore[attr-defined]
from cucumber_messages import (
    Exception as CucumberException,
)
from filelock import FileLock

from pytest_bdd.compatibility.path import relpath
from pytest_bdd.compatibility.pytest import (
    Config,
    FixtureDef,
    FixtureLookupError,
    FixtureRequest,
    get_config_root_path,
    is_testrun_success,
)
from pytest_bdd.model.execution_message_adapter import ExecutionMessageAdapter
from pytest_bdd.model.message_converter import envelope_from_dict, message_converter
from pytest_bdd.model.message_extension import get_payload_kind, has_single_payload
from pytest_bdd.model.message_outcome_mapping import OutcomeMappingRule, resolve_outcome_mapping
from pytest_bdd.model.message_registry import EnvelopeRegistry
from pytest_bdd.model.message_serialization import MessageSerializationProfile
from pytest_bdd.model.message_validation import (
    default_outcome_mapping_rules,
    observed_outcome_from_envelope,
    validate_envelope_dict_against_schema,
    validate_message_stream,
)
from pytest_bdd.model.scenario_run import Run
from pytest_bdd.plugin.pickle_runner.run_access import (
    resolve_step_object,
)
from pytest_bdd.steps import StepDefinitionManager
from pytest_bdd.tag_expression import GherkinTagExpression, MarksTagExpression
from pytest_bdd.types.exception import MessageSchemaValidationError
from pytest_bdd.util.npm_resource import check_npm, check_npm_package, find_resource
from pytest_bdd.util.other import IdGenerator
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
    BEFORE_TEST_RUN_HOOK_ID: ClassVar[str] = "pytest-bdd-ng.before-test-run"
    AFTER_TEST_RUN_HOOK_ID: ClassVar[str] = "pytest-bdd-ng.after-test-run"
    config: Config = attrib()
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
    _disabled_warning_emitted: bool
    _outcome_mapping_rules: list[OutcomeMappingRule]
    _mapping_diagnostics_count: int
    _emitted_step_definition_ids: set[str]
    _emitted_run_hook_definition_ids: set[str]

    def __attrs_post_init__(self):
        self._disabled_warning_emitted = False
        self._outcome_mapping_rules = default_outcome_mapping_rules()
        self._mapping_diagnostics_count = 0
        self._emitted_step_definition_ids = set()
        self._emitted_run_hook_definition_ids = set()

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
        icon_path = Path(next(find_resource(self.npm_formatter_package, Path("src") / "icon.url")))
        template_path = Path(next(find_resource(self.npm_formatter_package, Path("src") / "index.mustache.html")))
        template = template_path.read_text(encoding="utf-8")

        with self.messages_file_path.open(mode="r", encoding="utf-8") as f:
            messages = tuple(line.strip() for line in f if line.strip())

        html_report_path = Path(self.config.option.cucumber_html_path)
        html_report_path.parent.mkdir(parents=True, exist_ok=True)
        html_report_path.write_text(
            self._render_html_report_content(
                template=template,
                title="Cucumber",
                icon=icon_path.read_text(encoding="utf-8").strip(),
                css=css_path.read_text(encoding="utf-8"),
                custom_css="",
                messages=messages,
                script=script_path.read_text(encoding="utf-8"),
                custom_script="",
            ),
            encoding="utf-8",
        )

    @staticmethod
    def _html_formatter_template_between(template: str, begin: str | None, end: str | None) -> str:
        begin_index = 0 if begin is None else template.index(begin) + len(begin)
        end_index = len(template) if end is None else template.index(end)
        return template[begin_index:end_index]

    @staticmethod
    def _escape_html_formatter_message_json(message_json: str) -> str:
        return message_json.replace("<", "\\x3C")

    @classmethod
    def _render_html_report_content(
        cls,
        *,
        template: str,
        title: str,
        icon: str,
        css: str,
        custom_css: str,
        messages: tuple[str, ...],
        script: str,
        custom_script: str,
    ) -> str:
        escaped_messages = ",".join(cls._escape_html_formatter_message_json(message_json) for message_json in messages)
        parts = (
            cls._html_formatter_template_between(template, None, "{{title}}"),
            title,
            cls._html_formatter_template_between(template, "{{title}}", "{{icon}}"),
            icon,
            cls._html_formatter_template_between(template, "{{icon}}", "{{css}}"),
            css,
            cls._html_formatter_template_between(template, "{{css}}", "{{custom_css}}"),
            custom_css,
            cls._html_formatter_template_between(template, "{{custom_css}}", "{{messages}}"),
            escaped_messages,
            cls._html_formatter_template_between(template, "{{messages}}", "{{script}}"),
            script,
            cls._html_formatter_template_between(template, "{{script}}", "{{custom_script}}"),
            custom_script,
            cls._html_formatter_template_between(template, "{{custom_script}}", None),
        )
        return "".join(parts)

    def pytest_bdd_message(
        self,
        config: Config,
        message: Message,
    ):
        message = ExecutionMessageAdapter.serialize(message)
        if not has_single_payload(message):
            message_text = "Cannot emit envelope with zero or multiple payloads"
            raise TypeError(message_text)

        if self.is_disabled:
            EnvelopeRegistry.register_envelope_in_pytest_stash(config.stash, message)
            return

        schema_compatible_message = ExecutionMessageAdapter.serialize_to_dict(
            message,
            profile=MessageSerializationProfile.schema_compatible,
        )
        schema_violations = validate_envelope_dict_against_schema(schema_compatible_message)
        if schema_violations:
            details = "; ".join(violation.message for violation in schema_violations)
            raise MessageSchemaValidationError(details)

        EnvelopeRegistry.register_envelope_in_pytest_stash(config.stash, message)
        try:
            message_json = json.dumps(schema_compatible_message)
        except Exception as exc:
            message_text = "Message emission failed while serializing envelope"
            raise RuntimeError(message_text) from exc

        self.process_messages_io_queue.put_nowait(message_json)

    def pytest_bdd_source_read(self, config: Config, gherkin_document: GherkinDocument, source: Source) -> None:
        _ = gherkin_document
        self._emit_envelope(config, Message(source=source))

    def pytest_bdd_feature_read(self, config: Config, gherkin_document: GherkinDocument) -> None:
        self._emit_envelope(config, Message(gherkin_document=gherkin_document))

    def pytest_bdd_pickle_read(self, config: Config, gherkin_document: GherkinDocument, pickle: Pickle) -> None:
        _ = gherkin_document
        self._emit_envelope(config, Message(pickle=pickle))

    @pytest.hookimpl(hookwrapper=True)
    def pytest_runtestloop(self, session: pytest.Session):
        if self.is_disabled:
            yield
            return
        config: Config = session.config
        run_started_id = self._require_run_started_id(config=config)
        self._emit_envelope(
            config,
            Message(test_run_started=TestRunStarted(id=run_started_id, timestamp=self.get_timestamp())),
        )

        before_test_run_hook_started_id = next(IdGenerator.from_stash(config.stash))
        run_root = Run.from_stash(config.stash)
        run_root.reporting_state.test_run_hook_started_id = before_test_run_hook_started_id
        self._emit_run_hook_definition(
            config,
            hook_id=self.BEFORE_TEST_RUN_HOOK_ID,
            hook_type=HookType.before_test_run,
            hook_name="before-test-run",
        )
        self._emit_envelope(
            config,
            Message(
                test_run_hook_started=TestRunHookStarted(
                    hook_id=self.BEFORE_TEST_RUN_HOOK_ID,
                    id=before_test_run_hook_started_id,
                    test_run_started_id=run_started_id,
                    timestamp=self.get_timestamp(),
                    worker_id=os.environ.get("PYTEST_XDIST_WORKER", "master"),
                )
            ),
        )
        yield
        self._emit_envelope(
            config,
            Message(
                test_run_hook_finished=TestRunHookFinished(
                    test_run_hook_started_id=before_test_run_hook_started_id,
                    timestamp=self.get_timestamp(),
                    result=TestStepResult(
                        duration=Duration(seconds=0, nanos=0),
                        status=TestStepResultStatus.passed,
                        message="before-test-run hook completed",
                    ),
                )
            ),
        )

    def pytest_sessionstart(self, session):
        if self.is_disabled:
            self._emit_disabled_warning_once()
            return

        self.start_process_messages_thread()

        config = session.config

        ci = self._build_ci_message(os.environ)

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
                )
            ),
        )
        self._emit_run_hook_definition(
            cast(Config, config),
            hook_id=self.BEFORE_TEST_RUN_HOOK_ID,
            hook_type=HookType.before_test_run,
            hook_name="before-test-run",
        )
        self._emit_run_hook_definition(
            cast(Config, config),
            hook_id=self.AFTER_TEST_RUN_HOOK_ID,
            hook_type=HookType.after_test_run,
            hook_name="after-test-run",
        )

    @staticmethod
    def _build_ci_message(env: Mapping[str, str]) -> Ci | None:
        ci_payload = detect_ci_environment(env)
        if ci_payload is None:
            return None
        enriched_payload = GherkinMessageReporter._enrich_ci_payload(ci_payload, env)
        return message_converter.from_dict(enriched_payload, Ci)

    @staticmethod
    def _enrich_ci_payload(ci_payload: dict[str, Any], env: Mapping[str, str]) -> dict[str, Any]:
        """Patch CI payload with branch when detector omits it for PR-style builds.

        `ci_environment` provides a solid baseline payload, but some providers
        expose branch only via platform-specific env vars in merge-request
        pipelines. We enrich only the missing branch field to keep emitted
        metadata stable without overriding detector-provided values.
        """
        payload = dict(ci_payload)
        git_payload_raw = payload.get("git")
        git_payload = dict(git_payload_raw) if isinstance(git_payload_raw, dict) else {}
        if not git_payload.get("branch"):
            branch = GherkinMessageReporter._resolve_ci_branch(env)
            if branch:
                git_payload["branch"] = branch
        if git_payload:
            payload["git"] = git_payload
        return payload

    @staticmethod
    def _resolve_ci_branch(env: Mapping[str, str]) -> str | None:
        """Resolve VCS branch name from common CI env var conventions."""
        github_ref_type = (env.get("GITHUB_REF_TYPE") or "").strip().lower()
        github_ref = (env.get("GITHUB_REF") or "").strip()
        github_ref_name = (env.get("GITHUB_REF_NAME") or "").strip()
        github_head_ref = (env.get("GITHUB_HEAD_REF") or "").strip()
        if github_ref_type == "branch" and github_ref_name:
            return github_ref_name
        if github_ref.startswith("refs/heads/"):
            return github_ref.removeprefix("refs/heads/")
        if github_head_ref:
            return github_head_ref

        for name in (
            "CI_COMMIT_BRANCH",
            "CI_COMMIT_REF_NAME",
            "GIT_BRANCH",
            "BRANCH_NAME",
            "BUILD_SOURCEBRANCHNAME",
        ):
            value = (env.get(name) or "").strip()
            if value:
                return value.removeprefix("refs/heads/")
        return None

    def _require_run_started_id(self, *, config: Config) -> str:
        run_started_id = Run.from_stash(config.stash).reporting_state.run_started_id
        if run_started_id is None:
            msg = (
                "Execution context run_started_id is unavailable in config.stash. "
                "Execution plugins must initialize session root state before reporter lifecycle emission."
            )
            raise RuntimeError(msg)
        return run_started_id

    @staticmethod
    def _resolve_gherkin_document_and_pickle(*, run: Run) -> tuple[Any | None, Any | None]:
        scenario_run = run.active_scenario_run
        return scenario_run.gherkin_document, scenario_run.pickle

    def _emit_run_hook_definition(self, config: Config, *, hook_id: str, hook_type: HookType, hook_name: str) -> None:
        if hook_id in self._emitted_run_hook_definition_ids:
            return
        self._emitted_run_hook_definition_ids.add(hook_id)
        hook_method = type(self).pytest_sessionstart if hook_type == HookType.before_test_run else type(self).pytest_sessionfinish
        source_file = getfile(hook_method)
        source_line = getsourcelines(hook_method)[1]
        self._emit_envelope(
            config,
            Message(
                hook=Hook(
                    id=hook_id,
                    name=hook_name,
                    type=hook_type,
                    source_reference=SourceReference(
                        uri=relpath(source_file, str(get_config_root_path(config))),
                        location=Location(line=source_line, column=1),
                        java_method=JavaMethod(
                            class_name=type(self).__module__,
                            method_name=hook_method.__name__,
                            method_parameter_types=[],
                        ),
                        java_stack_trace_element=JavaStackTraceElement(
                            class_name=type(self).__module__,
                            file_name=Path(source_file).name,
                            method_name=hook_method.__name__,
                        ),
                    ),
                )
            ),
        )

    def _resolve_test_step_id_for_runtime_step(self, *, request: FixtureRequest, step: object) -> str | None:
        run = Run.from_stash(request.config.stash)
        test_step_id = run.resolve_test_step_id_for_runtime_step(pickle_step=step)
        if test_step_id is None:
            logger.warning("Unable to resolve cucumber TestStep id for runtime step object: %r", step)
        return test_step_id

    def pytest_sessionfinish(self, session, exitstatus):
        if self.is_disabled:
            return
        config = session.config
        run_started_id = self._require_run_started_id(config=cast(Config, config))
        run_success = is_testrun_success(exitstatus)
        run_exception = (
            CucumberException(type="PytestExitCode", message=str(exitstatus), stack_trace=str(exitstatus))
            if not run_success
            else None
        )
        after_test_run_hook_started_id = next(IdGenerator.from_stash(cast(Config, config).stash))
        self._emit_run_hook_definition(
            cast(Config, config),
            hook_id=self.AFTER_TEST_RUN_HOOK_ID,
            hook_type=HookType.after_test_run,
            hook_name="after-test-run",
        )
        self._emit_envelope(
            config,
            Message(
                test_run_hook_started=TestRunHookStarted(
                    hook_id=self.AFTER_TEST_RUN_HOOK_ID,
                    id=after_test_run_hook_started_id,
                    test_run_started_id=run_started_id,
                    timestamp=self.get_timestamp(),
                    worker_id=os.environ.get("PYTEST_XDIST_WORKER", "master"),
                )
            ),
        )
        self._emit_envelope(
            config,
            Message(
                test_run_hook_finished=TestRunHookFinished(
                    test_run_hook_started_id=after_test_run_hook_started_id,
                    timestamp=self.get_timestamp(),
                    result=TestStepResult(
                        duration=Duration(seconds=0, nanos=0),
                        status=TestStepResultStatus.passed if run_success else TestStepResultStatus.failed,
                        message="after-test-run hook completed",
                        **({"exception": run_exception} if run_exception is not None else {}),
                    ),
                )
            ),
        )
        self._emit_envelope(
            config,
            Message(
                test_run_finished=TestRunFinished(
                    timestamp=self.get_timestamp(),
                    success=run_success,
                    test_run_started_id=run_started_id,
                    message=f"pytest session exit status: {exitstatus}",
                    **({"exception": run_exception} if run_exception is not None else {}),
                )
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
            track_coverage=False,
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
            hook_conjunction = getattr(func, "__pytest_bdd_hook_conjunction__", "before")
            hook_type = {
                "before": HookType.before_test_case,
                "after": HookType.after_test_case,
                "around": HookType.before_test_case,
            }.get(str(hook_conjunction))
            parameter_types = list(signature(func).parameters.keys())
            source_file = getfile(func)
            source_line = getsourcelines(func)[1]

            hook_message_id = next(IdGenerator.from_stash(cast(Config, config).stash))
            hook_message = Hook(
                id=hook_message_id,
                **({"name": hook_name} if hook_name is not None else {}),
                source_reference=SourceReference(
                    uri=relpath(
                        source_file,
                        str(get_config_root_path(cast(Config, config))),
                    ),
                    location=Location(line=source_line, column=1),
                    java_method=JavaMethod(
                        class_name=str(getattr(func, "__module__", "pytest_bdd.hook")),
                        method_name=str(getattr(func, "__name__", "hook")),
                        method_parameter_types=parameter_types,
                    ),
                    java_stack_trace_element=JavaStackTraceElement(
                        class_name=str(getattr(func, "__module__", "pytest_bdd.hook")),
                        file_name=Path(source_file).name,
                        method_name=str(getattr(func, "__name__", "hook")),
                    ),
                ),
                **({"tag_expression": hook_expression} if hook_expression is not None else {}),
                **({"type": hook_type} if hook_type is not None else {}),
            )
            type(self).hook_registration_registry[func_id] = HookRegistration(
                hook_message_id=hook_message_id,
                expression="" if hook_expression is None else str(hook_expression),
                kind=str(hook_kind),
            )

            self._emit_envelope(config, Message(hook=hook_message))

        yield

    @pytest.hookimpl(hookwrapper=True)
    def pytest_runtest_setup(self, item):
        yield
        if self.is_disabled:
            return

        session = item.session
        config: Config = cast(Config, session.config)

        hook_handler = cast(Config, config).hook

        request = item._request
        run = Run.from_stash(request.config.stash)
        scenario_run = run.active_scenario_run
        if scenario_run is None:
            logger.warning(
                "Execution context unavailable during pytest_runtest_setup; skipping context-backed correlation writes."
            )
            return
        gherkin_document, pickle = self._resolve_gherkin_document_and_pickle(run=run)
        if gherkin_document is None or pickle is None:
            logger.warning("Execution context does not carry runtime feature/pickle during pytest_runtest_setup.")
            return

        self._report_step_definitions(config, request)
        self._register_parameter_types(config, request)
        reporting_state = run.reporting_state

        test_steps = []
        previous_step = None
        reporting_state.runtime_step_to_pickle_step_id.clear()

        test_steps.extend(
            [
                TestStep(
                    id=next(IdGenerator.from_stash(cast(Config, config).stash)),
                    hook_id=hook_registration.hook_message_id,
                )
                for hook_registration in self._iter_matching_hook_registrations(request=request, pickle=pickle)
            ]
        )

        for step in pickle.steps:
            try:
                scenario_run.step_object = step
                scenario_run.previous_step_object = previous_step
                step_definition = hook_handler.pytest_bdd_match_step_definition_to_step(
                    request=request,
                    run=run,
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
                    id=next(IdGenerator.from_stash(cast(Config, config).stash)),
                    pickle_step_id=step.id,
                    step_definition_ids=[step_definition.as_message(config).id],
                    **(
                        {"step_match_arguments_lists": step_match_arguments_lists} if step_match_arguments_lists else {}
                    ),
                )
                test_steps.append(test_step)
                run.map_runtime_step_to_test_step_id(
                    pickle_step=step,
                    test_step_id=test_step.id,
                )
            finally:
                previous_step = step

        resolved_run_started_id = Run.from_stash(cast(Config, config).stash).reporting_state.run_started_id
        test_case = TestCase(
            id=next(IdGenerator.from_stash(cast(Config, config).stash)),
            pickle_id=pickle.id,
            test_steps=test_steps,
            **({"test_run_started_id": resolved_run_started_id} if resolved_run_started_id is not None else {}),
        )
        reporting_state.active_test_case_id = test_case.id

        self._emit_envelope(
            cast(Config, config),
            Message(test_case=test_case),
        )

    def _report_step_definitions(self, config, request):
        try:
            step_registry = request.getfixturevalue("step_registry")
        except (FixtureLookupError, AssertionError):
            return
        seen_steps = set()
        while step_registry is not None:
            for step_definition in step_registry:
                if id(step_definition) not in seen_steps:
                    seen_steps.add(id(step_definition))
                    step_definition_message = step_definition.as_message(config=config)
                    if step_definition_message.id in self._emitted_step_definition_ids:
                        continue
                    self._emitted_step_definition_ids.add(step_definition_message.id)
                    self._emit_envelope(
                        config,
                        Message(step_definition=step_definition_message),
                    )
            step_registry = step_registry.parent

    def _iter_matching_hook_registrations(self, request: FixtureRequest, pickle: Any):
        for hook_registration in type(self).hook_registration_registry.values():
            if self._hook_expression_matches(
                request=request,
                pickle=pickle,
                expression=hook_registration.expression,
                kind=hook_registration.kind,
            ):
                yield hook_registration

    def _hook_expression_matches(
        self,
        *,
        request: FixtureRequest,
        pickle: Any,
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
                for tag in pickle.tags:
                    mark = Mark(tag.name, args=(), kwargs={}, _ispytest=True)
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

        with suppress(OSError, TypeError, ValueError):
            source_file = getfile(transformer)
            source_line = getsourcelines(transformer)[1]
            parameter_types = list(signature(transformer).parameters.keys())
            return SourceReference(
                uri=relpath(
                    source_file,
                    str(get_config_root_path(cast(Config, config))),
                ),
                location=Location(line=source_line, column=1),
                java_method=JavaMethod(
                    class_name=str(getattr(transformer, "__module__", "pytest_bdd.parameter_type")),
                    method_name=str(getattr(transformer, "__name__", "transformer")),
                    method_parameter_types=parameter_types,
                ),
                java_stack_trace_element=JavaStackTraceElement(
                    class_name=str(getattr(transformer, "__module__", "pytest_bdd.parameter_type")),
                    file_name=Path(source_file).name,
                    method_name=str(getattr(transformer, "__name__", "transformer")),
                ),
            )
        return None

    def _register_parameter_types(self, config, request):
        try:
            step_registry = request.getfixturevalue("step_registry")
        except (FixtureLookupError, AssertionError):
            return
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
                                    id=next(IdGenerator.from_stash(cast(Config, config).stash)),
                                    **(
                                        {"source_reference": parameter_type_source_reference}
                                        if parameter_type_source_reference is not None
                                        else {}
                                    ),
                                )
                            ),
                        )
                    type(self).parameter_type_registry |= not_yet_registered_parameter_types.keys()
            step_registry = step_registry.parent

    @staticmethod
    def _step_keyword_to_decorator(keyword: str | None) -> str:
        normalized = (keyword or "").strip().lower()
        if normalized.startswith("when"):
            return "when"
        if normalized.startswith("then"):
            return "then"
        return "given"

    def _build_suggestion_snippet(self, step: Any) -> str:
        decorator = self._step_keyword_to_decorator(getattr(step, "keyword", None))
        step_text = str(getattr(step, "text", "")).replace('"', '\\"')
        return f'@{decorator}("{step_text}")\ndef step_impl():\n    raise NotImplementedError\n'

    @staticmethod
    def _extract_undefined_parameter_type(
        *,
        exception: Exception,
        fallback_expression: str,
    ) -> tuple[str, str] | None:
        from cucumber_expressions.errors import UndefinedParameterTypeError

        explicit = getattr(exception, "undefined_parameter_type", None)
        if isinstance(explicit, tuple) and len(explicit) == 2:
            return str(explicit[0]), str(explicit[1])

        for candidate in (exception, getattr(exception, "__cause__", None)):
            if isinstance(candidate, UndefinedParameterTypeError):
                expression = str(candidate.args[1]) if len(candidate.args) > 1 else fallback_expression
                parameter_name = str(candidate.args[2]) if len(candidate.args) > 2 else ""
                if parameter_name:
                    return expression, parameter_name

            message = str(candidate or "")
            matched_name = re.search(r"Undefined parameter type \\{([^}]+)\\}", message)
            if matched_name:
                return fallback_expression, matched_name.group(1)

        return None

    def pytest_bdd_step_func_lookup_error(
        self,
        request,
        run: Run,
        exception,
    ):
        if self.is_disabled:
            return
        step = resolve_step_object(run)
        if step is None:
            return
        config = request.config
        pickle_step_id = getattr(step, "id", None)
        if pickle_step_id is None:
            return

        suggestion_id = next(IdGenerator.from_stash(cast(Config, config).stash))
        suggestion = Suggestion(
            id=suggestion_id,
            pickle_step_id=str(pickle_step_id),
            snippets=[Snippet(code=self._build_suggestion_snippet(step), language="python")],
        )
        self._emit_envelope(config, Message(suggestion=suggestion))

        undefined_parameter = self._extract_undefined_parameter_type(
            exception=exception,
            fallback_expression=str(getattr(step, "text", "")),
        )
        if undefined_parameter is not None:
            expression, parameter_name = undefined_parameter
            self._emit_envelope(
                config,
                Message(
                    undefined_parameter_type=UndefinedParameterType(
                        expression=expression,
                        name=parameter_name,
                    )
                ),
            )

    def pytest_bdd_before_scenario(
        self,
        request,
        run: Run,
    ):
        if self.is_disabled:
            return
        config = request.config
        reporting_state = run.reporting_state
        test_case_id = reporting_state.active_test_case_id
        if test_case_id is None:
            return
        attempt_index = getattr(request.node, "execution_count", 0)
        worker_id = os.environ.get("PYTEST_XDIST_WORKER", "master")
        test_case_start = TestCaseStarted(
            attempt=attempt_index,
            id=next(IdGenerator.from_stash(cast(Config, config).stash)),
            test_case_id=test_case_id,
            worker_id=worker_id,
            timestamp=self.get_timestamp(),
        )
        reporting_state.active_test_case_started_id = test_case_start.id
        reporting_state.scenario_attempt_context = {
            "scenario_attempt_id": test_case_start.id,
            "attempt_index": attempt_index,
            "worker_id": worker_id,
        }
        self._emit_envelope(
            config,
            Message(test_case_started=test_case_start),
        )

    def pytest_bdd_after_scenario(
        self,
        request,
        run: Run,
    ):
        if self.is_disabled:
            return
        reporting_state = run.reporting_state
        test_case_started_id = reporting_state.active_test_case_started_id
        if test_case_started_id is None:
            return
        config = request.config
        self._emit_envelope(
            config,
            Message(
                test_case_finished=TestCaseFinished(
                    test_case_started_id=test_case_started_id,
                    timestamp=self.get_timestamp(),
                    will_be_retried=False,
                )
            ),
        )
        reporting_state.reset_scenario_scope()

    @staticmethod
    def _duration_between(start_timestamp: Timestamp | None, finish_timestamp: Timestamp) -> Duration:
        if start_timestamp is None:
            return Duration(seconds=0, nanos=0)

        duration_total_nanos = (finish_timestamp.seconds * 10**9 + finish_timestamp.nanos) - (
            start_timestamp.seconds * 10**9 + start_timestamp.nanos
        )
        duration_seconds = duration_total_nanos // 10**9
        duration_nanos = duration_total_nanos - duration_seconds * 10**9
        return Duration(seconds=duration_seconds, nanos=duration_nanos)

    def pytest_bdd_before_step(
        self,
        request,
        run: Run,
        step_func,  # noqa: ARG002 hookspec
    ):
        if self.is_disabled:
            return
        step = resolve_step_object(run)
        if step is None:
            return
        reporting_state = run.reporting_state
        test_case_started_id = reporting_state.active_test_case_started_id
        if test_case_started_id is None:
            return
        config = request.config

        test_step_id = self._resolve_test_step_id_for_runtime_step(request=request, step=step)
        if test_step_id is None:
            return

        step_start_timestamp = self.get_timestamp()
        reporting_state.step_started_timestamp = step_start_timestamp
        reporting_state.active_test_step_id = test_step_id
        test_step_started = TestStepStarted(
            test_case_started_id=test_case_started_id,
            timestamp=step_start_timestamp,
            test_step_id=test_step_id,
        )

        self._emit_envelope(
            config,
            Message(test_step_started=test_step_started),
        )

    def pytest_bdd_after_step(
        self,
        request,
        run: Run,
        step_func,  # noqa: ARG002 hookspec
    ):
        if self.is_disabled:
            return
        step = resolve_step_object(run)
        if step is None:
            return
        reporting_state = run.reporting_state
        test_case_started_id = reporting_state.active_test_case_started_id
        if test_case_started_id is None:
            return
        config = request.config

        test_step_id = self._resolve_test_step_id_for_runtime_step(request=request, step=step)
        if test_step_id is None:
            return
        step_finish_timestamp = self.get_timestamp()
        reporting_state.step_finished_timestamp = step_finish_timestamp
        step_duration = self._duration_between(
            start_timestamp=cast(Timestamp | None, reporting_state.step_started_timestamp),
            finish_timestamp=step_finish_timestamp,
        )

        self._emit_envelope(
            config,
            Message(
                test_step_finished=TestStepFinished(
                    test_case_started_id=test_case_started_id,
                    timestamp=step_finish_timestamp,
                    test_step_id=test_step_id,
                    test_step_result=TestStepResult(duration=step_duration, status=TestStepResultStatus.passed),
                )
            ),
        )
        reporting_state.active_test_step_id = None

    def pytest_bdd_step_error(
        self,
        request,
        run: Run,
        step_func,  # noqa: ARG002 hookspec
        step_func_args,  # noqa: ARG002 hookspec
        exception,
        step_definition,  # noqa: ARG002 hookspec
    ):
        if self.is_disabled:
            return
        step = resolve_step_object(run)
        if step is None:
            return
        reporting_state = run.reporting_state
        test_case_started_id = reporting_state.active_test_case_started_id
        if test_case_started_id is None:
            return
        config = request.config

        test_step_id = self._resolve_test_step_id_for_runtime_step(request=request, step=step)
        if test_step_id is None:
            return
        step_finish_timestamp = self.get_timestamp()
        reporting_state.step_finished_timestamp = step_finish_timestamp
        step_duration = self._duration_between(
            start_timestamp=cast(Timestamp | None, reporting_state.step_started_timestamp),
            finish_timestamp=step_finish_timestamp,
        )

        self._emit_envelope(
            config,
            Message(
                test_step_finished=TestStepFinished(
                    test_case_started_id=test_case_started_id,
                    timestamp=step_finish_timestamp,
                    test_step_id=test_step_id,
                    test_step_result=TestStepResult(
                        duration=step_duration,
                        status=TestStepResultStatus.failed,
                        message=str(exception),
                        exception=CucumberException(
                            type=type(exception).__name__,
                            message=str(exception),
                            stack_trace=repr(exception),
                        ),
                    ),
                )
            ),
        )
        reporting_state.active_test_step_id = None

    def pytest_bdd_attach(  # noqa: C901
        self,
        request,
        attachment,
        media_type,
        file_name,
        source_data,
        source_media_type,
        source_uri,
        url,
        as_external,
        test_run_hook_started_id,
        test_run_started_id,
    ):
        if self.is_disabled:
            return
        config = request.config
        run = Run.find_in_stash(config.stash)
        reporting_state = run.reporting_state if run is not None else None
        test_case_started_id = reporting_state.active_test_case_started_id if reporting_state is not None else None
        active_test_step_id = reporting_state.active_test_step_id if reporting_state is not None else None
        attachment_timestamp = self.get_timestamp()
        effective_test_run_hook_started_id = test_run_hook_started_id or (
            run.reporting_state.test_run_hook_started_id if run is not None else None
        )
        effective_test_run_started_id = test_run_started_id or (
            run.reporting_state.run_started_id if run is not None else None
        )

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

        source = None
        if source_data is not None and source_media_type is not None and source_uri is not None:
            source = Source(
                data=str(source_data),
                media_type=source_media_type,
                uri=source_uri,
            )
        attachment_url = url

        self._emit_envelope(
            config,
            Message(
                attachment=Attachment(
                    **({"test_step_id": active_test_step_id} if active_test_step_id is not None else {}),
                    **({"test_case_started_id": test_case_started_id} if test_case_started_id is not None else {}),
                    **(
                        {"test_run_hook_started_id": effective_test_run_hook_started_id}
                        if effective_test_run_hook_started_id is not None
                        else {}
                    ),
                    **(
                        {"test_run_started_id": effective_test_run_started_id}
                        if effective_test_run_started_id is not None
                        else {}
                    ),
                    media_type=media_type_,
                    **({"file_name": str(file_name)} if file_name is not None else {}),
                    **({"source": source} if source is not None else {}),
                    **({"url": attachment_url} if attachment_url is not None else {}),
                    timestamp=attachment_timestamp,
                    content_encoding=content_encoding,
                    body=body,
                )
            ),
        )

        if as_external and attachment_url is not None:
            external_media_type = media_type_ or "application/octet-stream"
            self._emit_envelope(
                config,
                Message(
                    external_attachment=ExternalAttachment(
                        media_type=external_media_type,
                        url=attachment_url,
                        **({"test_case_started_id": test_case_started_id} if test_case_started_id is not None else {}),
                        **({"test_step_id": active_test_step_id} if active_test_step_id is not None else {}),
                        **(
                            {"test_run_hook_started_id": effective_test_run_hook_started_id}
                            if effective_test_run_hook_started_id is not None
                            else {}
                        ),
                        timestamp=attachment_timestamp,
                    )
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
