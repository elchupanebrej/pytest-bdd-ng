from __future__ import annotations

import json
import sys
from importlib import import_module
from io import StringIO
from queue import Queue
from types import SimpleNamespace

import pytest
from attrs import define
from cucumber_messages import Envelope as Message  # type:ignore[attr-defined, import-untyped]
from cucumber_messages import (
    Hook as CucumberHook,
)
from cucumber_messages import (
    HookType,
    JavaMethod,
    JavaStackTraceElement,
    Location,
    SourceReference,
    StepDefinition,
    Timestamp,
)
from cucumber_messages import (
    ParameterType as CucumberParameterType,
)
from cucumber_messages import StepDefinitionPattern as CucumberStepDefinitionPattern
from cucumber_messages import TestRunStarted as CucumberTestRunStarted  # type:ignore[attr-defined, import-untyped]

from pytest_bdd.model.message_extension import StepDefinitionPatternType
from pytest_bdd.model.message_registry import EnvelopeRegistry
from pytest_bdd.model.message_transport import ReportingTransportSession
from pytest_bdd.model.scenario_run import (
    ActiveObjectSet,
    HookPhase,
    LifecycleObjectRef,
    Run,
    RunStage,
    RunStatus,
    ScenarioRun,
)
from pytest_bdd.plugin.gherkin_message_reporter import entrypoint, lifecycle_runtime, message_stream
from pytest_bdd.plugin.gherkin_message_reporter.html_report import render_html_report_content
from pytest_bdd.plugin.gherkin_message_reporter.plugin import GherkinMessageReporter
from pytest_bdd.util import inspect_extra
from pytest_bdd.util.other import IdGenerator
from tests.support.cucumber_formatters import install_formatter_hook_registry


def _build_reporter() -> GherkinMessageReporter:
    return GherkinMessageReporter(
        config=SimpleNamespace(
            option=SimpleNamespace(messages_ndjson_path=None, cucumber_html_path=None),
        )
    )


def _build_formatter_reporter(tmp_path, **option_overrides) -> GherkinMessageReporter:
    option_values = {
        "messages_ndjson_path": str(tmp_path / "messages.ndjson"),
        "cucumber_html_path": None,
        "cucumber_summary": False,
        "cucumber_progress": False,
        "cucumber_progress_bar": False,
        "cucumber_js_json_path": None,
        "cucumber_junit_path": None,
        "cucumber_usage_output": None,
        "cucumber_usage_json_path": None,
        "cucumber_snippets": False,
        "cucumber_pretty": False,
    }
    option_values.update(option_overrides)
    config = SimpleNamespace(option=SimpleNamespace(**option_values), rootpath=tmp_path)
    install_formatter_hook_registry(config)
    return GherkinMessageReporter(config=config)


def _build_scenario_run() -> ScenarioRun:
    run_ref = LifecycleObjectRef(kind="run", object_id="run-1", is_active=True)
    session = Run(
        id="run-1",
        run_ref=run_ref,
        status=RunStatus.ok,
    )
    return ScenarioRun(
        id="ctx-1",
        run_ref=run_ref,
        active_hook=HookPhase.run_step,
        stage=RunStage.step_running,
        status=RunStatus.ok,
        active_set=ActiveObjectSet(run=run_ref, captured_at_stage=RunStage.step_running),
        run=session,
    )


def _build_request_with_context(scenario_run: ScenarioRun) -> SimpleNamespace:
    config = SimpleNamespace(stash={})
    scenario_run.run.set_in_stash(config.stash)
    request = SimpleNamespace(
        node=SimpleNamespace(nodeid="node::scenario"),
        config=config,
    )
    scenario_run.run.scenario_runs_by_request["node::scenario"] = scenario_run
    scenario_run.run.active_scenario_run = scenario_run
    return request


@define
class _FakeStepDefinitionRegistry:
    items: list[object]
    parent: _FakeStepDefinitionRegistry | None = None

    def __iter__(self):
        return iter(self.items)


def test_reporter_has_no_current_prefixed_state_annotations() -> None:
    annotated_state_fields = getattr(GherkinMessageReporter, "__annotations__", {})
    current_prefixed = sorted(name for name in annotated_state_fields if name.startswith("current_"))
    assert current_prefixed == []


def test_reporter_has_no_context_store_state_annotation() -> None:
    annotated_state_fields = getattr(GherkinMessageReporter, "__annotations__", {})
    assert "_context_store" not in annotated_state_fields
    assert "_run_id" not in annotated_state_fields


def test_reporter_has_no_mutable_class_level_registries() -> None:
    assert not isinstance(getattr(GherkinMessageReporter, "parameter_type_registry", None), set)
    assert not isinstance(getattr(GherkinMessageReporter, "hook_registry", None), set)
    assert not isinstance(getattr(GherkinMessageReporter, "hook_registration_registry", None), dict)


def test_reporting_entrypoint_and_message_stream_do_not_store_runtime_flags_as_module_globals() -> None:
    assert not hasattr(entrypoint, "_REPORTING_REMOTE_MODULE_REQUIRED")
    assert not hasattr(message_stream, "_XDIST_CONTROLLER_PATCHED")


def test_reporter_resolves_test_step_id_from_scenario_run_mapping() -> None:
    reporter = _build_reporter()
    scenario_run = _build_scenario_run()
    request = _build_request_with_context(scenario_run)
    runtime_step = object()

    scenario_run.run.map_runtime_step_to_test_step_id(
        pickle_step=runtime_step,
        test_step_id="test-step-42",
    )

    assert reporter.lifecycle_service.resolve_test_step_id_for_runtime_step(request=request, step=runtime_step) == (
        "test-step-42"
    )


def test_reporter_resolves_test_step_id_from_context_active_fallback() -> None:
    reporter = _build_reporter()
    scenario_run = _build_scenario_run()
    request = _build_request_with_context(scenario_run)
    scenario_run.run.reporting_state.active_test_step_id = "active-step-5"

    assert reporter.lifecycle_service.resolve_test_step_id_for_runtime_step(request=request, step=object()) == (
        "active-step-5"
    )


def test_reporter_registers_envelope_in_config_stash_registry(tmp_path) -> None:
    config = SimpleNamespace(
        option=SimpleNamespace(messages_ndjson_path=str(tmp_path / "messages.ndjson"), cucumber_html_path=None),
        stash={},
    )
    Run.initialize_for_config(stash=config.stash, config=config)
    reporter = GherkinMessageReporter(config=config)
    reporter.process_messages_io_queue = Queue()
    envelope = Message(
        test_run_started=CucumberTestRunStarted(id="run-started-1", timestamp=Timestamp(seconds=0, nanos=0))
    )

    reporter.lifecycle_service.pytest_bdd_message(config=config, message=envelope)

    envelope_registry = EnvelopeRegistry.from_stash(config.stash)
    assert envelope_registry.envelopes == [envelope]
    assert envelope_registry.resolve("run-started-1") is envelope.test_run_started


def test_reporter_emits_schema_compatible_step_definition_json(tmp_path) -> None:
    config = SimpleNamespace(
        option=SimpleNamespace(messages_ndjson_path=str(tmp_path / "messages.ndjson"), cucumber_html_path=None),
        stash={},
    )
    Run.initialize_for_config(stash=config.stash, config=config)
    reporter = GherkinMessageReporter(config=config)
    reporter.process_messages_io_queue = Queue()
    envelope = Message(
        step_definition=StepDefinition(
            id="step-definition-1",
            pattern=CucumberStepDefinitionPattern(
                source="I have {count:d} cucumbers",
                type=StepDefinitionPatternType.pytest_bdd_parse_expression,
            ),
            source_reference=SourceReference(
                uri="steps.py",
                location=Location(line=1, column=1),
                java_method=JavaMethod(class_name="steps", method_name="step", method_parameter_types=[]),
                java_stack_trace_element=JavaStackTraceElement(
                    class_name="steps",
                    file_name="steps.py",
                    method_name="step",
                ),
            ),
        )
    )

    reporter.lifecycle_service.pytest_bdd_message(config=config, message=envelope)

    queued_message = json.loads(reporter.process_messages_io_queue.get_nowait())
    assert queued_message["stepDefinition"]["pattern"]["type"] == "REGULAR_EXPRESSION"

    envelope_registry = EnvelopeRegistry.from_stash(config.stash)
    assert envelope_registry.envelopes == [envelope]
    assert (
        envelope_registry.envelopes[0].step_definition.pattern.type
        == StepDefinitionPatternType.pytest_bdd_parse_expression
    )


def test_reporter_reports_each_step_definition_only_once() -> None:
    reporter = _build_reporter()
    emitted_messages: list[Message] = []
    step_definition_message = StepDefinition(
        id="step-definition-1",
        pattern=CucumberStepDefinitionPattern(
            source="I have {count:d} cucumbers",
            type=StepDefinitionPatternType.pytest_bdd_parse_expression,
        ),
        source_reference=SourceReference(
            uri="steps.py",
            location=Location(line=1, column=1),
            java_method=JavaMethod(class_name="steps", method_name="step", method_parameter_types=[]),
            java_stack_trace_element=JavaStackTraceElement(
                class_name="steps",
                file_name="steps.py",
                method_name="step",
            ),
        ),
    )

    class _FakeDefinition:
        def as_message(self, config):  # noqa: ARG002
            return step_definition_message

    reporter.lifecycle_service._emit_envelope = lambda _config, message: emitted_messages.append(message)  # type: ignore[method-assign]
    request = SimpleNamespace(
        getfixturevalue=lambda name: (
            _FakeStepDefinitionRegistry(items=[_FakeDefinition()]) if name == "step_registry" else None
        )
    )
    config = SimpleNamespace()

    reporter.step_catalog_service.report_step_definitions(config, request)
    reporter.step_catalog_service.report_step_definitions(config, request)

    assert [message.step_definition.id for message in emitted_messages] == ["step-definition-1"]


def test_reporter_renders_html_report_content_with_formatter_safe_message_embedding() -> None:
    template = """<!DOCTYPE html>
<html lang="en">
<head>
<title>{{title}}</title>
<link rel="icon" href="{{icon}}">
<style>
{{css}}
</style>
<style>
{{custom_css}}
</style>
</head>
<body>
<div id="content"></div>
<script>
window.CUCUMBER_MESSAGES = [{{messages}}];
</script>
<script>
{{script}}
</script>
<script>
{{custom_script}}
</script>
</body>
</html>
"""

    rendered = render_html_report_content(
        template=template,
        title="Cucumber",
        icon="data:image/x-icon;base64,abc",
        css="body{}",
        custom_css="",
        messages=('{"source":{"data":"<!-- hidden -->"}}',),
        script="console.log(window.CUCUMBER_MESSAGES.length)",
        custom_script="",
    )

    assert "<title>Cucumber</title>" in rendered
    assert 'href="data:image/x-icon;base64,abc"' in rendered
    assert "\\x3C!-- hidden -->" in rendered
    assert "<!-- hidden -->" not in rendered.split("window.CUCUMBER_MESSAGES = [", 1)[1].split("];", 1)[0]


def test_reporter_renders_html_report_content_for_current_html_formatter_template_shape() -> None:
    template = """<!DOCTYPE html>
<html lang="en">
<head>
<title>Cucumber</title>
<style>{{css}}</style>
</head>
<body>
<script>window.CUCUMBER_MESSAGES=[{{messages}}]</script>
<script>{{script}}</script>
</body>
</html>
"""

    rendered = render_html_report_content(
        template=template,
        title="ignored title",
        icon="ignored icon",
        css="body{color:black;}",
        custom_css="ignored custom css",
        messages=('{"source":{"data":"<tag>"}}',),
        script="console.log('ok')",
        custom_script="ignored custom script",
    )

    assert "<title>Cucumber</title>" in rendered
    assert "body{color:black;}" in rendered
    assert "\\x3Ctag>" in rendered
    assert "console.log('ok')" in rendered


def test_reporter_emits_run_hook_definitions_during_session_start(monkeypatch, tmp_path) -> None:
    reporter = GherkinMessageReporter(
        config=SimpleNamespace(
            option=SimpleNamespace(messages_ndjson_path=str(tmp_path / "messages.ndjson"), cucumber_html_path=None),
            rootpath=tmp_path,
        )
    )
    emitted_messages: list[Message] = []
    config = reporter.config
    config.stash = {}
    Run.initialize_for_config(stash=config.stash, config=config).reporting_state.run_started_id = "run-started-1"
    IdGenerator().initialize_in_stash(config.stash)

    def capture_message(config, message) -> None:
        _ = config
        emitted_messages.append(message)

    config.hook = SimpleNamespace(pytest_bdd_message=capture_message)

    monkeypatch.setattr(reporter.transport_service, "start_process_messages_thread", lambda: None)

    reporter.lifecycle_service.pytest_sessionstart(SimpleNamespace(config=config))

    hook_messages = [message.hook for message in emitted_messages if message.hook is not None]

    assert [hook.id for hook in hook_messages] == [
        GherkinMessageReporter.BEFORE_TEST_RUN_HOOK_ID,
        GherkinMessageReporter.AFTER_TEST_RUN_HOOK_ID,
    ]
    assert [hook.type for hook in hook_messages] == [HookType.before_test_run, HookType.after_test_run]


def test_reporter_uses_code_line_fallback_when_hook_source_lines_are_unavailable(monkeypatch, tmp_path) -> None:
    reporter = GherkinMessageReporter(
        config=SimpleNamespace(
            option=SimpleNamespace(messages_ndjson_path=str(tmp_path / "messages.ndjson"), cucumber_html_path=None),
            rootpath=tmp_path,
        )
    )
    emitted_messages: list[Message] = []
    config = reporter.config
    config.stash = {}
    Run.initialize_for_config(stash=config.stash, config=config).reporting_state.run_started_id = "run-started-1"
    IdGenerator().initialize_in_stash(config.stash)

    def capture_message(config, message) -> None:
        _ = config
        emitted_messages.append(message)

    config.hook = SimpleNamespace(pytest_bdd_message=capture_message)

    monkeypatch.setattr(reporter.transport_service, "start_process_messages_thread", lambda: None)
    monkeypatch.setattr(lifecycle_runtime, "get_first_source_line", lambda method: method.__code__.co_firstlineno)

    reporter.lifecycle_service.pytest_sessionstart(SimpleNamespace(config=config))

    before_hook = next(
        message.hook
        for message in emitted_messages
        if message.hook is not None and message.hook.type == HookType.before_test_run
    )
    assert (
        before_hook.source_reference.location.line
        == type(reporter.lifecycle_service).pytest_sessionstart.__code__.co_firstlineno
    )


def test_get_first_source_line_falls_back_to_code_line(monkeypatch) -> None:
    def function_with_unavailable_source() -> None:
        return None

    monkeypatch.setattr(inspect_extra, "getsourcelines", lambda _method: (_ for _ in ()).throw(OSError))

    assert inspect_extra.get_first_source_line(function_with_unavailable_source) == (
        function_with_unavailable_source.__code__.co_firstlineno
    )


def test_reporter_ignores_inherited_xdist_worker_environment_without_workerinput(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("PYTEST_XDIST_WORKER", "gw0")

    reporter = GherkinMessageReporter(
        config=SimpleNamespace(
            option=SimpleNamespace(messages_ndjson_path=str(tmp_path / "messages.ndjson"), cucumber_html_path=None),
            rootpath=tmp_path,
        )
    )

    assert reporter.is_xdist_worker is False
    assert reporter._xdist_worker_temp_messages_path is None
    assert reporter.messages_file_path == reporter.final_messages_file_path


def test_reporter_truncates_existing_explicit_messages_file_on_startup(tmp_path) -> None:
    messages_path = tmp_path / "messages.ndjson"
    messages_path.write_text('{"old":"envelope"}\n', encoding="utf-8")

    GherkinMessageReporter(
        config=SimpleNamespace(
            option=SimpleNamespace(messages_ndjson_path=str(messages_path), cucumber_html_path=None),
            rootpath=tmp_path,
        )
    )

    assert messages_path.read_text(encoding="utf-8") == ""


def test_reporter_detects_xdist_worker_from_workerinput(tmp_path) -> None:
    reporter = GherkinMessageReporter(
        config=SimpleNamespace(
            option=SimpleNamespace(messages_ndjson_path=str(tmp_path / "messages.ndjson"), cucumber_html_path=None),
            rootpath=tmp_path,
            workerinput={"workerid": "gw0"},
        )
    )

    assert reporter.is_xdist_worker is True
    assert reporter._xdist_worker_temp_messages_path is not None
    assert reporter.messages_file_path == reporter._xdist_worker_temp_messages_path


def test_entrypoint_uses_custom_remote_module_when_reporting_disabled() -> None:
    pytest.importorskip("xdist.remote")

    class _PluginManager:
        def register(self, *_args, **_kwargs) -> None:
            return None

        def unregister(self, *_args, **_kwargs) -> None:
            return None

    config = SimpleNamespace(
        option=SimpleNamespace(messages_ndjson_path=None, cucumber_html_path=None),
        pluginmanager=_PluginManager(),
    )

    entrypoint.pytest_configure(config)

    try:
        remote_module = entrypoint.pytest_xdist_getremotemodule()
    finally:
        entrypoint.pytest_unconfigure(config)

    assert remote_module.__name__ == "pytest_bdd_worker_bootstrap.xdist_remote"


def test_entrypoint_uses_custom_remote_module_when_reporting_enabled(tmp_path) -> None:
    pytest.importorskip("xdist.remote")

    class _PluginManager:
        def register(self, *_args, **_kwargs) -> None:
            return None

        def unregister(self, *_args, **_kwargs) -> None:
            return None

    config = SimpleNamespace(
        option=SimpleNamespace(messages_ndjson_path=str(tmp_path / "messages.ndjson"), cucumber_html_path=None),
        pluginmanager=_PluginManager(),
        rootpath=tmp_path,
    )

    entrypoint.pytest_configure(config)

    try:
        remote_module = entrypoint.pytest_xdist_getremotemodule()
    finally:
        entrypoint.pytest_unconfigure(config)

    assert remote_module.__name__ == "pytest_bdd_worker_bootstrap.xdist_remote"


def test_entrypoint_remote_module_selection_ignores_inherited_worker_environment(monkeypatch, tmp_path) -> None:
    pytest.importorskip("xdist.remote")

    class _PluginManager:
        def register(self, *_args, **_kwargs) -> None:
            return None

        def unregister(self, *_args, **_kwargs) -> None:
            return None

    monkeypatch.setenv("PYTEST_XDIST_WORKER", "gw0")
    config = SimpleNamespace(
        option=SimpleNamespace(messages_ndjson_path=str(tmp_path / "messages.ndjson"), cucumber_html_path=None),
        pluginmanager=_PluginManager(),
        rootpath=tmp_path,
    )

    entrypoint.pytest_configure(config)

    try:
        remote_module = entrypoint.pytest_xdist_getremotemodule()
    finally:
        entrypoint.pytest_unconfigure(config)

    assert remote_module.__name__ == "pytest_bdd_worker_bootstrap.xdist_remote"


def test_entrypoint_detects_cucumber_formatter_flags_as_reporting_request() -> None:
    config = SimpleNamespace(
        option=SimpleNamespace(
            messages_ndjson_path=None,
            cucumber_html_path=None,
            cucumber_summary=True,
            cucumber_progress=False,
            cucumber_progress_bar=False,
            cucumber_js_json_path=None,
            cucumber_junit_path=None,
            cucumber_usage_output=None,
            cucumber_usage_json_path=None,
            cucumber_snippets=False,
            cucumber_pretty=False,
        )
    )

    assert entrypoint._reporting_requested(config) is True


def test_entrypoint_stores_reporter_state_in_config_stash(tmp_path) -> None:
    class _PluginManager:
        def register(self, *_args, **_kwargs) -> None:
            return None

        def unregister(self, *_args, **_kwargs) -> None:
            return None

    config = SimpleNamespace(
        option=SimpleNamespace(messages_ndjson_path=None, cucumber_html_path=None),
        pluginmanager=_PluginManager(),
        stash={},
        rootpath=tmp_path,
    )

    entrypoint.pytest_configure(config)

    try:
        assert entrypoint._resolve_reporter_state(config) is not None
        assert entrypoint._REPORTER_STATE_ATTR in config.stash
        assert getattr(config, entrypoint._REPORTER_STATE_ATTR, None) is None
    finally:
        entrypoint.pytest_unconfigure(config)

    assert entrypoint._REPORTER_STATE_ATTR not in config.stash


def test_entrypoint_detects_terminal_formatter_flags_in_raw_args() -> None:
    assert entrypoint._terminal_formatter_flags_requested(["--cucumber-summary"]) is True
    assert entrypoint._terminal_formatter_flags_requested(["--cucumber-usage"]) is True
    assert entrypoint._terminal_formatter_flags_requested(["--cucumber-usage=-"]) is True
    assert entrypoint._terminal_formatter_flags_requested(["--cucumber-usage=usage.txt"]) is False
    assert entrypoint._terminal_formatter_flags_requested(["--cucumber-json=report.json"]) is False


def test_cucumber_formatter_util_import_does_not_eagerly_load_formatter_registry() -> None:
    sys.modules.pop("pytest_bdd.util.cucumber_formatters", None)
    sys.modules.pop("pytest_bdd.plugin.cucumber_formatter_support.registry", None)

    import_module("pytest_bdd.util.cucumber_formatters")

    assert "pytest_bdd.plugin.cucumber_formatter_support.registry" not in sys.modules


def test_entrypoint_auto_disables_capture_for_terminal_formatter_args(monkeypatch) -> None:
    monkeypatch.delenv("PYTEST_BDD_KEEP_PYTEST_CAPTURE", raising=False)
    args = ["tests/e2e/test_report_doc_cucumber_formatters.py", "--cucumber-summary"]

    entrypoint.pytest_load_initial_conftests(None, None, args)

    assert args[:2] == ["--capture=no", "tests/e2e/test_report_doc_cucumber_formatters.py"]
    assert "--cucumber-summary" in args


def test_entrypoint_preserves_explicit_capture_configuration(monkeypatch) -> None:
    monkeypatch.delenv("PYTEST_BDD_KEEP_PYTEST_CAPTURE", raising=False)
    args = ["--capture=fd", "tests/e2e/test_report_doc_cucumber_formatters.py", "--cucumber-summary"]

    entrypoint.pytest_load_initial_conftests(None, None, args)

    assert args == ["--capture=fd", "tests/e2e/test_report_doc_cucumber_formatters.py", "--cucumber-summary"]


def test_entrypoint_disables_cacheprovider_for_windows_remote_xdist_reporting(monkeypatch) -> None:
    monkeypatch.setattr(entrypoint, "_running_on_windows", lambda: True)
    args = [
        "--tx",
        "socket=127.0.0.1:8888//chdir=C:/tmp/run",
        "--messages-ndjson",
        "C:/tmp/run/report.ndjson",
    ]

    entrypoint.pytest_load_initial_conftests(None, None, args)

    assert args[:2] == ["-p", "no:cacheprovider"]


def test_entrypoint_preserves_explicit_cache_configuration_for_windows_remote_xdist_reporting(monkeypatch) -> None:
    monkeypatch.setattr(entrypoint, "_running_on_windows", lambda: True)
    args = [
        "-o",
        "cache_dir=C:/tmp/custom-cache",
        "--tx",
        "socket=127.0.0.1:8888//chdir=C:/tmp/run",
        "--messages-ndjson",
        "C:/tmp/run/report.ndjson",
    ]

    entrypoint.pytest_load_initial_conftests(None, None, args)

    assert args == [
        "-o",
        "cache_dir=C:/tmp/custom-cache",
        "--tx",
        "socket=127.0.0.1:8888//chdir=C:/tmp/run",
        "--messages-ndjson",
        "C:/tmp/run/report.ndjson",
    ]


def test_entrypoint_preserves_split_override_ini_cache_configuration_for_windows_remote_xdist_reporting(
    monkeypatch,
) -> None:
    monkeypatch.setattr(entrypoint, "_running_on_windows", lambda: True)
    args = [
        "--override-ini",
        "cache_dir=C:/tmp/custom-cache",
        "--tx",
        "socket=127.0.0.1:8888//chdir=C:/tmp/run",
        "--messages-ndjson",
        "C:/tmp/run/report.ndjson",
    ]

    entrypoint.pytest_load_initial_conftests(None, None, args)

    assert args == [
        "--override-ini",
        "cache_dir=C:/tmp/custom-cache",
        "--tx",
        "socket=127.0.0.1:8888//chdir=C:/tmp/run",
        "--messages-ndjson",
        "C:/tmp/run/report.ndjson",
    ]


def test_entrypoint_does_not_quiet_terminal_reporter_before_live_formatter_startup(monkeypatch) -> None:
    quiet_replacement_calls: list[object] = []
    configure_calls: list[tuple[object, object]] = []
    unconfigure_calls: list[object] = []

    class _PluginManager:
        def __init__(self) -> None:
            self.registered: list[tuple[object, str | None]] = []

        def register(self, plugin, name=None) -> None:
            self.registered.append((plugin, name))

        def unregister(self, *_args, **_kwargs) -> None:
            return None

        def getplugin(self, _name):
            return None

    class _FakeReporter:
        plugin_name = "fake-gherkin-message-reporter"

        def __init__(self, config) -> None:
            self.config = config
            self.configure_called = False

        def configure(self, *, pluginmanager, quiet_terminal_replacer) -> None:
            configure_calls.append((pluginmanager, quiet_terminal_replacer))
            self.configure_called = True

        def unconfigure(self, *, pluginmanager) -> None:
            unconfigure_calls.append(pluginmanager)

    config = SimpleNamespace(
        option=SimpleNamespace(
            messages_ndjson_path=None,
            cucumber_html_path=None,
            cucumber_summary=True,
            cucumber_progress=False,
            cucumber_progress_bar=False,
            cucumber_js_json_path=None,
            cucumber_junit_path=None,
            cucumber_usage_output=None,
            cucumber_usage_json_path=None,
            cucumber_snippets=False,
            cucumber_pretty=False,
        ),
        pluginmanager=_PluginManager(),
    )

    monkeypatch.setattr(entrypoint, "GherkinMessageReporter", _FakeReporter)
    monkeypatch.setattr(
        entrypoint,
        "_replace_terminal_reporter_with_quiet_variant",
        lambda replacement_config: quiet_replacement_calls.append(replacement_config),
    )

    entrypoint.pytest_configure(config)

    assert quiet_replacement_calls == []
    assert len(configure_calls) == 1
    assert unconfigure_calls == []


def test_reporter_collects_requested_cucumber_formatters_and_resolves_paths(tmp_path) -> None:
    output_path = tmp_path / "reports" / "cucumber.json"
    usage_path = tmp_path / "reports" / "usage.txt"
    output_path.parent.mkdir()
    reporter = _build_formatter_reporter(
        tmp_path,
        messages_ndjson_path=None,
        cucumber_summary=True,
        cucumber_js_json_path=str(output_path),
        cucumber_usage_output=str(usage_path),
    )

    assert reporter.is_disabled is False
    assert [request.formatter for request in reporter.requested_cucumber_formatters] == ["summary", "json", "usage"]
    assert reporter.live_formatters == reporter.requested_cucumber_formatters
    assert reporter.deferred_formatters == ()
    assert reporter.requested_cucumber_formatters[0].output_path is None
    assert reporter.requested_cucumber_formatters[1].output_path == output_path.resolve()
    assert reporter.requested_cucumber_formatters[2].output_path == usage_path.resolve()
    assert reporter.config.option.cucumber_js_json_path == str(output_path.resolve())
    assert reporter.config.option.cucumber_usage_output == str(usage_path.resolve())
    assert reporter.final_messages_file_path.exists() is True


def test_reporter_builds_support_code_payload_for_cucumber_formatters() -> None:
    reporter = _build_reporter()
    source_reference = SourceReference(
        uri="steps.py",
        location=Location(line=7, column=1),
        java_method=JavaMethod(class_name="steps", method_name="step_impl", method_parameter_types=[]),
        java_stack_trace_element=JavaStackTraceElement(
            class_name="steps",
            file_name="steps.py",
            method_name="step_impl",
        ),
    )
    payload = reporter.live_formatter_service.build_cucumber_formatter_support_code_payload(
        [
            Message(
                step_definition=StepDefinition(
                    id="step-definition-1",
                    pattern=CucumberStepDefinitionPattern(
                        source="I have {count:d} cucumbers",
                        type=StepDefinitionPatternType.pytest_bdd_parse_expression,
                    ),
                    source_reference=source_reference,
                )
            ),
            Message(
                hook=CucumberHook(
                    id="hook-1",
                    name="before-tag",
                    type=HookType.before_test_case,
                    source_reference=source_reference,
                    tag_expression="@tag",
                )
            ),
            Message(
                parameter_type=CucumberParameterType(
                    id="parameter-type-1",
                    name="count",
                    regular_expressions=["\\d+"],
                    prefer_for_regular_expression_match=True,
                    use_for_snippets=True,
                    source_reference=source_reference,
                )
            ),
        ]
    )

    assert payload["stepDefinitions"] == [
        {
            "id": "step-definition-1",
            "uri": "steps.py",
            "line": 7,
            "pattern": "I have {count:d} cucumbers",
            "expressionConstructorName": "CucumberExpression",
            "code": "steps.step_impl",
        }
    ]
    assert payload["hooks"] == [
        {
            "id": "hook-1",
            "name": "before-tag",
            "uri": "steps.py",
            "line": 7,
            "type": "before_test_case",
            "tagExpression": "@tag",
        }
    ]
    assert payload["parameterTypes"] == [
        {
            "name": "count",
            "regularExpressions": ["\\d+"],
            "preferForRegularExpressionMatch": True,
            "useForSnippets": True,
        }
    ]


def test_reporter_warns_when_node_is_missing_for_requested_cucumber_formatter(
    caplog: pytest.LogCaptureFixture,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    reporter = _build_formatter_reporter(tmp_path, cucumber_summary=True)

    monkeypatch.setattr(
        "pytest_bdd.plugin.gherkin_message_reporter.live_formatter_runtime.shutil.which", lambda _name: None
    )

    with caplog.at_level("WARNING"):
        reporter.render_requested_cucumber_formatters(envelopes=[])

    assert "Node.js was not found in PATH" in caplog.text


def test_reporter_records_live_formatter_delivery_failures(capsys, tmp_path) -> None:
    class _BrokenStream:
        def write(self, _value: str) -> int:
            msg = "broken pipe"
            raise OSError(msg)

        def flush(self) -> None:
            return None

    config = _build_formatter_reporter(tmp_path, cucumber_summary=True).config
    config.stash = {}
    Run.initialize_for_config(stash=config.stash, config=config)
    reporter = GherkinMessageReporter(config=config)
    reporter.process_messages_io_queue = Queue()
    reporter._live_formatter_process = SimpleNamespace(stdin=_BrokenStream(), poll=lambda: None, returncode=None)

    reporter.lifecycle_service.pytest_bdd_message(
        config=config,
        message=Message(test_run_started=CucumberTestRunStarted(id="run-1", timestamp=Timestamp(seconds=0, nanos=0))),
    )

    captured = capsys.readouterr()
    assert reporter._live_formatter_failure_message is not None
    assert "broken pipe" in reporter._live_formatter_failure_message
    assert "Live cucumber formatter delivery from local envelope emission failed" in captured.err


def test_controller_forwards_worker_batches_into_live_formatter_session(tmp_path) -> None:
    reporter = _build_formatter_reporter(tmp_path, cucumber_summary=True)
    config = reporter.config
    forwarded = StringIO()
    reporter.is_xdist_controller = True
    reporter.xdist_transport_session = ReportingTransportSession()
    reporter._live_formatter_process = SimpleNamespace(stdin=forwarded, poll=lambda: None, returncode=None)
    batch = {
        "worker_id": "gw0",
        "batch_sequence": 0,
        "envelopes": [
            {
                "testRunStarted": {
                    "id": "run-1",
                    "workerId": "gw0",
                    "timestamp": {"seconds": 0, "nanos": 0},
                }
            }
        ],
    }

    reporter.transport_service.pytest_bdd_xdist_message_batch(config=config, node=SimpleNamespace(), batch=batch)

    snapshot = reporter.xdist_transport_session.snapshot()
    assert snapshot.batches_by_worker["gw0"][0].batch_sequence == 0
    assert snapshot.batches_by_worker["gw0"][0].envelopes == tuple(batch["envelopes"])
    assert [json.loads(line) for line in forwarded.getvalue().splitlines() if line.strip()] == batch["envelopes"]


@define
class _RecordingStdin:
    writes: list[str]
    flush_count: int = 0

    def write(self, value: str) -> int:
        self.writes.append(value)
        return len(value)

    def flush(self) -> None:
        self.flush_count += 1

    def close(self) -> None:
        return None


def test_reporter_forwards_xdist_batches_into_live_formatter_stdin(tmp_path) -> None:
    reporter = _build_formatter_reporter(tmp_path, cucumber_summary=True)
    stdin = _RecordingStdin(writes=[])
    reporter.is_xdist_controller = True
    reporter.xdist_transport_session = ReportingTransportSession()
    reporter._live_formatter_process = SimpleNamespace(stdin=stdin, poll=lambda: None, returncode=None)

    reporter.transport_service.pytest_bdd_xdist_message_batch(
        config=SimpleNamespace(),
        node=SimpleNamespace(),
        batch={
            "worker_id": "gw0",
            "batch_sequence": 0,
            "envelopes": [{"testRunStarted": {"id": "run-1", "workerId": "gw0"}}],
        },
    )

    assert "".join(stdin.writes) == '{"testRunStarted": {"id": "run-1", "workerId": "gw0"}}\n'
    assert stdin.flush_count == 1
    snapshot = reporter.xdist_transport_session.snapshot()
    assert snapshot.batches_by_worker["gw0"][0].batch_sequence == 0


def test_reporter_records_live_formatter_failure_when_process_exits_early(tmp_path, capsys) -> None:
    reporter = _build_formatter_reporter(tmp_path, cucumber_summary=True)
    reporter._live_formatter_process = SimpleNamespace(
        stdin=_RecordingStdin(writes=[]),
        poll=lambda: 7,
        returncode=7,
    )

    reporter.live_formatter_service.emit_live_formatter_json_lines(
        ['{"meta": {"protocolVersion": "1.0.0"}}'],
        source="unit-test",
    )

    captured = capsys.readouterr()
    assert reporter._live_formatter_failure_message == (
        "Live cucumber formatter session exited early with code 7 while handling unit-test."
    )
    assert "Live cucumber formatter session exited early with code 7 while handling unit-test." in captured.err
