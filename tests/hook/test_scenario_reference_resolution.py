from __future__ import annotations

from types import SimpleNamespace

from cucumber_messages import DataTable, DocString, Location, PickleStep, Step, TableCell, TableRow

from pytest_bdd.model.execution_context import (
    ActiveObjectSet,
    ExecutionContext,
    ExecutionStage,
    ExecutionStatus,
    HookPhase,
    LifecycleObjectRef,
    SessionExecutionContext,
)
from pytest_bdd.plugin.scenario_runner.context_access import resolve_step_runtime_enrichment
from pytest_bdd.plugin.scenario_runner.context_store import ExecutionContextStore
from pytest_bdd.plugin.scenario_runner.plugin import ScenarioRunner


def _build_execution_context() -> ExecutionContext:
    run_ref = LifecycleObjectRef(kind="run", object_id="run-1", is_active=True)
    session = SessionExecutionContext(
        session_context_id="session-1",
        run_ref=run_ref,
        status=ExecutionStatus.ok,
    )
    active_set = ActiveObjectSet(run=run_ref, captured_at_stage=ExecutionStage.scenario_running)
    return ExecutionContext(
        context_id="ctx-1",
        run_ref=run_ref,
        active_hook=HookPhase.run_scenario,
        stage=ExecutionStage.scenario_running,
        status=ExecutionStatus.ok,
        active_set=active_set,
        session_context=session,
    )


def _build_config_with_registry(entries: dict[str, object]) -> SimpleNamespace:
    config = SimpleNamespace(stash={})
    envelope_registry = ExecutionContextStore.ensure_envelope_registry_in_config(config)
    envelope_registry.identifiable.objects_by_id.update(entries)
    return config


def test_extended_step_context_resolves_scenario_description_from_context_registry() -> None:
    runner = ScenarioRunner()
    execution_context = _build_execution_context()
    config = _build_config_with_registry({"scenario-1": SimpleNamespace(id="scenario-1", description="Scenario from context")})
    feature = SimpleNamespace(_pytest_bdd_config=config)
    scenario = SimpleNamespace(ast_node_ids=["scenario-1"])
    execution_context.feature_object = feature
    execution_context.scenario_object = scenario

    with runner.extended_step_context(execution_context):
        assert scenario.description == "Scenario from context"


def test_extended_step_context_prefers_first_ast_node_id_for_nested_links() -> None:
    runner = ScenarioRunner()
    execution_context = _build_execution_context()
    config = _build_config_with_registry(
        {
            "rule-scenario-id": SimpleNamespace(id="rule-scenario-id", description="Nested scenario description"),
            "fallback-id": SimpleNamespace(id="fallback-id", description="Fallback description"),
        }
    )
    feature = SimpleNamespace(_pytest_bdd_config=config)
    scenario = SimpleNamespace(ast_node_ids=["rule-scenario-id", "fallback-id"])
    execution_context.feature_object = feature
    execution_context.scenario_object = scenario

    with runner.extended_step_context(execution_context):
        assert scenario.description == "Nested scenario description"


def test_extended_step_context_records_missing_scenario_reference_in_context_diagnostics() -> None:
    runner = ScenarioRunner()
    execution_context = _build_execution_context()
    config = _build_config_with_registry({})
    feature = SimpleNamespace(_pytest_bdd_config=config)
    scenario = SimpleNamespace(ast_node_ids=["missing-scenario-id"])
    execution_context.feature_object = feature
    execution_context.scenario_object = scenario

    with runner.extended_step_context(execution_context):
        assert scenario.description is None

    assert execution_context.reference_resolver.missing_reference_diagnostics == [
        "Missing AST node id: missing-scenario-id"
    ]


def test_resolve_step_runtime_enrichment_for_nested_rule_background_link() -> None:
    model_step = Step(
        id="rule-background-step-id",
        keyword="Given ",
        location=Location(line=11, column=5),
        text="a rule background step",
        doc_string=DocString(
            content="doc payload",
            delimiter='"""',
            location=Location(line=12, column=7),
            media_type="text/plain",
        ),
        data_table=DataTable(
            location=Location(line=13, column=7),
            rows=[
                TableRow(
                    id="row-1",
                    location=Location(line=13, column=7),
                    cells=[TableCell(location=Location(line=13, column=9), value="cell-value")],
                )
            ],
        ),
    )
    execution_context = _build_execution_context()
    config = _build_config_with_registry({"rule-background-step-id": model_step})
    feature = SimpleNamespace(_pytest_bdd_config=config)
    pickle_step = PickleStep(ast_node_ids=["rule-background-step-id"], id="pickle-step-id", text="a rule background step")

    payload = resolve_step_runtime_enrichment(
        feature=feature,
        execution_context=execution_context,
        step=pickle_step,
        config=config,
    )

    assert payload["keyword"] == "Given"
    assert payload["prefix"] == "given"
    assert payload["line_number"] == 11
    assert payload["doc_string"] is model_step.doc_string
    assert payload["data_table"] is model_step.data_table
    assert execution_context.reference_resolver.missing_reference_diagnostics == []


def test_resolve_step_runtime_enrichment_records_missing_link_diagnostics() -> None:
    execution_context = _build_execution_context()
    config = _build_config_with_registry({})
    feature = SimpleNamespace(_pytest_bdd_config=config)
    pickle_step = PickleStep(ast_node_ids=["missing-step-id"], id="pickle-step-id", text="missing")

    payload = resolve_step_runtime_enrichment(
        feature=feature,
        execution_context=execution_context,
        step=pickle_step,
        config=config,
    )

    assert payload == {
        "keyword": None,
        "prefix": None,
        "line_number": None,
        "doc_string": None,
        "data_table": None,
    }
    assert execution_context.reference_resolver.missing_reference_diagnostics == [
        "Missing pickle step mapping: pickle-step-id"
    ]
