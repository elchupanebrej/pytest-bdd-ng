from __future__ import annotations

from queue import Queue
from types import SimpleNamespace

from cucumber_messages import Envelope as Message  # type:ignore[attr-defined, import-untyped]
from cucumber_messages import TestRunStarted as CucumberTestRunStarted  # type:ignore[attr-defined, import-untyped]
from cucumber_messages import Timestamp

from pytest_bdd.model.scenario_run import (
    ActiveObjectSet,
    RunStage,
    RunStatus,
    HookPhase,
    LifecycleObjectRef,
    Run,
    ScenarioRun,
)
from pytest_bdd.plugin.gherkin_message_reporter.plugin import GherkinMessageReporter
from pytest_bdd.plugin.scenario_runner.run_access import (
    map_runtime_step_to_test_step_id,
    resolve_request_scenario_run,
)
from pytest_bdd.plugin.scenario_runner.run_store import RunStore


def _build_reporter() -> GherkinMessageReporter:
    return GherkinMessageReporter(
        config=SimpleNamespace(
            option=SimpleNamespace(messages_ndjson_path=None, cucumber_html_path=None),
        )
    )


def _build_scenario_run() -> ScenarioRun:
    run_ref = LifecycleObjectRef(kind="run", object_id="run-1", is_active=True)
    session = Run(
        run_context_id="run-1",
        run_ref=run_ref,
        status=RunStatus.ok,
    )
    return ScenarioRun(
        context_id="ctx-1",
        run_ref=run_ref,
        active_hook=HookPhase.run_step,
        stage=RunStage.step_running,
        status=RunStatus.ok,
        active_set=ActiveObjectSet(run=run_ref, captured_at_stage=RunStage.step_running),
        run=session,
    )


def _build_request_with_context(scenario_run: ScenarioRun) -> SimpleNamespace:
    request = SimpleNamespace(
        node=SimpleNamespace(nodeid="node::scenario"),
        config=SimpleNamespace(stash={}),
    )
    setattr(request.node, RunStore.SCENARIO_RUN_ATTR, scenario_run)
    request.config.stash[RunStore.SCENARIO_RUNS_STASH_KEY] = {"node::scenario": scenario_run}
    return request


def test_reporter_has_no_current_prefixed_state_annotations() -> None:
    annotated_state_fields = getattr(GherkinMessageReporter, "__annotations__", {})
    current_prefixed = sorted(name for name in annotated_state_fields if name.startswith("current_"))
    assert current_prefixed == []


def test_reporter_has_no_context_store_state_annotation() -> None:
    annotated_state_fields = getattr(GherkinMessageReporter, "__annotations__", {})
    assert "_context_store" not in annotated_state_fields
    assert "_run_id" not in annotated_state_fields


def test_resolve_request_scenario_run_is_read_only_lookup() -> None:
    request = SimpleNamespace(node=SimpleNamespace(nodeid="node::scenario"), config=SimpleNamespace(stash={}))
    assert resolve_request_scenario_run(request) is None


def test_resolve_request_scenario_run_from_config_stash_registry() -> None:
    scenario_run = _build_scenario_run()
    request = SimpleNamespace(
        node=SimpleNamespace(nodeid="node::scenario"),
        config=SimpleNamespace(
            stash={RunStore.SCENARIO_RUNS_STASH_KEY: {"node::scenario": scenario_run}}
        ),
    )

    assert resolve_request_scenario_run(request) is scenario_run


def test_reporter_resolves_test_step_id_from_scenario_run_mapping() -> None:
    reporter = _build_reporter()
    scenario_run = _build_scenario_run()
    request = _build_request_with_context(scenario_run)
    runtime_step = object()

    map_runtime_step_to_test_step_id(
        run=scenario_run.run,
        runtime_step=runtime_step,
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
    reporter = GherkinMessageReporter(config=config)
    reporter.process_messages_io_queue = Queue()
    envelope = Message(
        test_run_started=CucumberTestRunStarted(id="run-started-1", timestamp=Timestamp(seconds=0, nanos=0))
    )

    reporter.pytest_bdd_message(config=config, message=envelope)

    envelope_registry = RunStore.get_envelope_registry_from_config(config)
    assert envelope_registry is not None
    assert envelope_registry.envelopes == [envelope]
    assert envelope_registry.resolve("run-started-1") is envelope.test_run_started
