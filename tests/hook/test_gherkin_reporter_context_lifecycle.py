from __future__ import annotations

import json
from dataclasses import dataclass
from queue import Queue
from types import SimpleNamespace

from cucumber_messages import Envelope as Message  # type:ignore[attr-defined, import-untyped]
from cucumber_messages import (
    HookType,
    JavaMethod,
    JavaStackTraceElement,
    Location,
    SourceReference,
    StepDefinition,
    Timestamp,
)
from cucumber_messages import StepDefinitionPattern as CucumberStepDefinitionPattern
from cucumber_messages import TestRunStarted as CucumberTestRunStarted  # type:ignore[attr-defined, import-untyped]

from pytest_bdd.model.message_extension import StepDefinitionPatternType
from pytest_bdd.model.message_registry import EnvelopeRegistry
from pytest_bdd.model.scenario_run import (
    ActiveObjectSet,
    HookPhase,
    LifecycleObjectRef,
    Run,
    RunStage,
    RunStatus,
    ScenarioRun,
)
from pytest_bdd.plugin.gherkin_message_reporter.plugin import GherkinMessageReporter


def _build_reporter() -> GherkinMessageReporter:
    return GherkinMessageReporter(
        config=SimpleNamespace(
            option=SimpleNamespace(messages_ndjson_path=None, cucumber_html_path=None),
        )
    )


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


@dataclass
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


def test_reporter_resolves_test_step_id_from_scenario_run_mapping() -> None:
    reporter = _build_reporter()
    scenario_run = _build_scenario_run()
    request = _build_request_with_context(scenario_run)
    runtime_step = object()

    scenario_run.run.map_runtime_step_to_test_step_id(
        pickle_step=runtime_step,
        test_step_id="test-step-42",
    )

    assert reporter._resolve_test_step_id_for_runtime_step(request=request, step=runtime_step) == "test-step-42"


def test_reporter_resolves_test_step_id_from_context_active_fallback() -> None:
    reporter = _build_reporter()
    scenario_run = _build_scenario_run()
    request = _build_request_with_context(scenario_run)
    scenario_run.run.reporting_state.active_test_step_id = "active-step-5"

    assert reporter._resolve_test_step_id_for_runtime_step(request=request, step=object()) == "active-step-5"


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

    reporter.pytest_bdd_message(config=config, message=envelope)

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

    reporter.pytest_bdd_message(config=config, message=envelope)

    queued_message = json.loads(reporter.process_messages_io_queue.get_nowait())
    assert queued_message["stepDefinition"]["pattern"]["type"] == "REGULAR_EXPRESSION"

    envelope_registry = EnvelopeRegistry.from_stash(config.stash)
    assert envelope_registry.envelopes == [envelope]
    assert envelope_registry.envelopes[0].step_definition.pattern.type == StepDefinitionPatternType.pytest_bdd_parse_expression


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

    reporter._emit_envelope = lambda _config, message: emitted_messages.append(message)  # type: ignore[method-assign]
    request = SimpleNamespace(
        getfixturevalue=lambda name: _FakeStepDefinitionRegistry(items=[_FakeDefinition()]) if name == "step_registry" else None
    )
    config = SimpleNamespace()

    reporter._report_step_definitions(config, request)
    reporter._report_step_definitions(config, request)

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

    rendered = GherkinMessageReporter._render_html_report_content(
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
    assert '\\x3C!-- hidden -->' in rendered
    assert '<!-- hidden -->' not in rendered.split("window.CUCUMBER_MESSAGES = [", 1)[1].split("];", 1)[0]


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

    monkeypatch.setattr(reporter, "start_process_messages_thread", lambda: None)
    reporter._emit_envelope = lambda _config, message: emitted_messages.append(message)  # type: ignore[method-assign]

    reporter.pytest_sessionstart(SimpleNamespace(config=config))

    hook_messages = [message.hook for message in emitted_messages if message.hook is not None]

    assert [hook.id for hook in hook_messages] == [
        GherkinMessageReporter.BEFORE_TEST_RUN_HOOK_ID,
        GherkinMessageReporter.AFTER_TEST_RUN_HOOK_ID,
    ]
    assert [hook.type for hook in hook_messages] == [HookType.before_test_run, HookType.after_test_run]
