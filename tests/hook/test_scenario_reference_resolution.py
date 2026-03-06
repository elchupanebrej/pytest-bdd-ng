from __future__ import annotations

from types import SimpleNamespace

from cucumber_messages import DataTable, DocString, Location, PickleStep, Step, TableCell, TableRow

from pytest_bdd.model.scenario_run import (
    ActiveObjectSet,
    RunStage,
    RunStatus,
    HookPhase,
    LifecycleObjectRef,
    Run,
    ScenarioRun,
)
from pytest_bdd.plugin.pickle_runner.run_access import resolve_step_runtime_enrichment
from pytest_bdd.plugin.pickle_runner.plugin import PickleRunner


def _build_scenario_run() -> ScenarioRun:
    run_ref = LifecycleObjectRef(kind="run", object_id="run-1", is_active=True)
    session = Run(
        id="run-1",
        run_ref=run_ref,
        status=RunStatus.ok,
    )
    active_set = ActiveObjectSet(run=run_ref, captured_at_stage=RunStage.scenario_running)
    return ScenarioRun(
        id="ctx-1",
        run_ref=run_ref,
        active_hook=HookPhase.run_scenario,
        stage=RunStage.scenario_running,
        status=RunStatus.ok,
        active_set=active_set,
        run=session,
    )


def _build_config_with_registry(entries: dict[str, object]) -> SimpleNamespace:
    config = SimpleNamespace(stash={})
    envelope_registry = Run.ensure_envelope_registry_in_pytest_stash(config)
    envelope_registry.identifiable.objects_by_id.update(entries)
    return config


def test_extended_step_context_resolves_scenario_description_from_context_registry() -> None:
    runner = PickleRunner()
    scenario_run = _build_scenario_run()
    scenario_run.run.active_scenario_run = scenario_run
    config = _build_config_with_registry({"scenario-1": SimpleNamespace(id="scenario-1", description="Scenario from context")})
    feature = SimpleNamespace(_pytest_bdd_config=config)
    scenario = SimpleNamespace(ast_node_ids=["scenario-1"])
    scenario_run.feature_object = feature
    scenario_run.scenario_object = scenario

    with runner.extended_step_context(scenario_run.run):
        assert scenario.description == "Scenario from context"


def test_extended_step_context_prefers_first_ast_node_id_for_nested_links() -> None:
    runner = PickleRunner()
    scenario_run = _build_scenario_run()
    scenario_run.run.active_scenario_run = scenario_run
    config = _build_config_with_registry(
        {
            "rule-scenario-id": SimpleNamespace(id="rule-scenario-id", description="Nested scenario description"),
            "fallback-id": SimpleNamespace(id="fallback-id", description="Fallback description"),
        }
    )
    feature = SimpleNamespace(_pytest_bdd_config=config)
    scenario = SimpleNamespace(ast_node_ids=["rule-scenario-id", "fallback-id"])
    scenario_run.feature_object = feature
    scenario_run.scenario_object = scenario

    with runner.extended_step_context(scenario_run.run):
        assert scenario.description == "Nested scenario description"


def test_extended_step_context_records_missing_scenario_reference_in_context_diagnostics() -> None:
    runner = PickleRunner()
    scenario_run = _build_scenario_run()
    scenario_run.run.active_scenario_run = scenario_run
    config = _build_config_with_registry({})
    feature = SimpleNamespace(_pytest_bdd_config=config)
    scenario = SimpleNamespace(ast_node_ids=["missing-scenario-id"])
    scenario_run.feature_object = feature
    scenario_run.scenario_object = scenario

    with runner.extended_step_context(scenario_run.run):
        assert scenario.description is None

    assert scenario_run.reference_resolver.missing_reference_diagnostics == [
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
    scenario_run = _build_scenario_run()
    config = _build_config_with_registry({"rule-background-step-id": model_step})
    feature = SimpleNamespace(_pytest_bdd_config=config)
    pickle_step = PickleStep(ast_node_ids=["rule-background-step-id"], id="pickle-step-id", text="a rule background step")

    payload = resolve_step_runtime_enrichment(
        feature=feature,
        scenario_run=scenario_run,
        step=pickle_step,
        config=config,
    )

    assert payload["keyword"] == "Given"
    assert payload["prefix"] == "given"
    assert payload["line_number"] == 11
    assert payload["doc_string"] is model_step.doc_string
    assert payload["data_table"] is model_step.data_table
    assert scenario_run.reference_resolver.missing_reference_diagnostics == []


def test_resolve_step_runtime_enrichment_records_missing_link_diagnostics() -> None:
    scenario_run = _build_scenario_run()
    config = _build_config_with_registry({})
    feature = SimpleNamespace(_pytest_bdd_config=config)
    pickle_step = PickleStep(ast_node_ids=["missing-step-id"], id="pickle-step-id", text="missing")

    payload = resolve_step_runtime_enrichment(
        feature=feature,
        scenario_run=scenario_run,
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
    assert scenario_run.reference_resolver.missing_reference_diagnostics == [
        "Missing pickle step mapping: pickle-step-id"
    ]
