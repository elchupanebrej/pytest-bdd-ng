from __future__ import annotations

from pathlib import Path

import pytest
from attrs.exceptions import FrozenInstanceError

from pytest_cuke.model.doc_string import DocString
from pytest_cuke.model.examples import ExternalExampleRowSource
from pytest_cuke.model.feature import Feature
from pytest_cuke.model.feature_binding import FeatureRuntimeBinding, normalize_feature_uri
from pytest_cuke.model.scenario import Scenario
from pytest_cuke.model.session_run import RunContext
from pytest_cuke.model.step import Step
from pytest_cuke.model.table import DataTable, TableCell, TableRow

pytestmark = pytest.mark.unit


def test_feature_binding_indexes_source_tree_and_outline_row(tmp_path: Path) -> None:
    data_table = DataTable(
        id="table-1",
        rows=(
            TableRow(id="row-1", cells=(TableCell(id="cell-1", value="name"),)),
            TableRow(id="row-2", cells=(TableCell(id="cell-2", value="Ada"),)),
        ),
    )
    doc_string = DocString(content="payload", id="doc-1")
    step = Step(name="consume data", keyword="Given ", id="step-1", doc_string=doc_string, data_table=data_table)
    source_ids = ("scenario-ast-1", "examples-row-1")
    scenario = Scenario(
        name="Outline row Ada",
        id="pickle-1",
        steps=(step,),
        source_ast_node_ids=source_ids,
        external_example_source=ExternalExampleRowSource(
            path="examples.csv",
            marker_line=4,
            section_index=0,
            row_index=1,
            source_line=7,
            row_id="examples-row-1",
        ),
    )
    uri = str(tmp_path / "runtime.feature")
    feature = Feature(
        name="Runtime binding",
        uri=uri,
        scenarios=(scenario,),
        source_content="Feature: Runtime binding",
        source_media_type="text/x.cucumber.gherkin+plain",
    )

    binding = FeatureRuntimeBinding.from_feature(feature)

    assert binding.uri == Path(uri).resolve().as_uri()
    assert normalize_feature_uri(feature) == binding.uri
    assert binding.document is not None and binding.document.feature is feature
    assert binding.source == feature.source_content
    assert binding.source_media_type == feature.source_media_type
    assert binding.pickles_by_id["pickle-1"] is scenario
    assert binding.resolve_scenario(source_ids) is scenario
    assert binding.resolve_step(step) is step
    assert binding.ast_nodes_by_id["table-1"] is data_table
    assert binding.ast_nodes_by_id["row-2"] is data_table.rows[1]
    assert binding.ast_nodes_by_id["cell-2"] is data_table.rows[1].cells[0]
    assert binding.ast_nodes_by_id["doc-1"] is doc_string
    assert binding.ast_nodes_by_id["examples-row-1"] is scenario

    with pytest.raises(FrozenInstanceError):
        step.name = "mutated"


def test_feature_binding_normalizes_windows_drive_paths_as_file_uris() -> None:
    feature = Feature(name="Windows path", uri=r"C:\workspace\feature file.feature")

    assert normalize_feature_uri(feature) == "file:///C:/workspace/feature%20file.feature"


def test_run_context_exposes_only_the_scoped_step_and_previous_step() -> None:
    first_step = Step(name="first", keyword="Given ", id="step-1")
    second_step = Step(name="second", keyword="When ", id="step-2")
    feature = Feature(name="Inspection", uri="inspection.feature")
    scenario = Scenario(name="Inspection scenario", steps=(first_step, second_step))
    context = RunContext()
    scenario_run = context.start_scenario(
        nodeid="inspection.feature::Inspection scenario",
        feature=feature,
        scenario=scenario,
    )

    with context.inspect_step(
        feature=feature,
        scenario=scenario,
        step=first_step,
        previous_step=None,
    ) as run:
        assert run is context
        assert run.feature is feature
        assert run.scenario is scenario
        assert run.step is first_step
        assert run.previous_step is None
        with pytest.raises(RuntimeError, match=r"pytest_cuke_before_step.*previous step"):
            run.require_previous_step("pytest_cuke_before_step")

    assert context.step is None
    assert context.previous_step is None
    assert scenario_run.current_step_run is None

    with context.inspect_step(
        feature=feature,
        scenario=scenario,
        step=second_step,
        previous_step=first_step,
    ) as run:
        assert run.step is second_step
        assert run.previous_step is first_step
        assert run.require_previous_step("pytest_cuke_before_step") is first_step

    inactive = RunContext()
    assert inactive.feature is inactive.scenario is inactive.step is inactive.previous_step is None
    with pytest.raises(RuntimeError, match=r"pytest_cuke_match_step_definition_to_step.*current step"):
        inactive.require_step("pytest_cuke_match_step_definition_to_step")


def test_run_context_tracks_step_transitions_attempt_and_teardown_snapshot() -> None:
    first_step = Step(name="first", keyword="Given ", id="step-1")
    second_step = Step(name="second", keyword="Then ", id="step-2")
    feature = Feature(name="Lifecycle", uri="lifecycle.feature", scenarios=())
    scenario = Scenario(name="Lifecycle scenario", id="pickle-1", steps=(first_step, second_step))
    context = RunContext()
    context.begin_collection()
    binding = context.bind_feature(feature)
    assert context.stage == "collection"
    assert context.hook_phase == "pytest_collection"

    scenario_run = context.start_scenario(
        nodeid="lifecycle.feature::Lifecycle scenario",
        feature=feature,
        scenario=scenario,
        attempt=2,
    )
    assert context.stage == "setup"
    assert context.hook_phase == "pytest_runtest_setup"
    context.set_test_case(
        test_case_id="test-case-1",
        test_step_ids=["message-step-1", "message-step-2"],
        test_steps=["message-test-step"],
        test_case_started_id="attempt-1",
    )
    first_run = context.start_step(first_step)
    assert context.stage == "step-running"
    assert context.hook_phase == "pytest_cuke_before_step"
    context.finish_step(first_run)
    second_run = context.start_step(second_step)
    context.finish_step(second_run)
    assert second_run.previous_step_run is first_run
    assert context.stage == "running"
    assert context.hook_phase == "pytest_cuke_after_step"
    context.finish_active(status="passed")
    assert context.stage == "finished"
    context.enter_teardown()
    assert context.stage == "teardown"
    context.record_teardown_error(RuntimeError("fixture teardown failed"))
    final_snapshot_transition = scenario_run.transition_index

    context.clear_active()

    assert context.feature_bindings_by_uri[binding.uri] is binding
    assert context.get_scenario_run(scenario_run.nodeid, attempt=2) is scenario_run
    assert scenario_run.test_case_id == "test-case-1"
    assert scenario_run.test_case_started_id == "attempt-1"
    assert scenario_run.attempt_id == "attempt-1"
    assert scenario_run.message_state.test_steps == ["message-test-step"]
    assert first_run.test_step_id == "message-step-1"
    assert second_run.test_step_id == "message-step-2"
    assert second_run.previous_step_run is first_run
    assert first_run.children == [second_run]
    assert scenario_run.current_step_run is None
    assert scenario_run.status == "failed"
    assert scenario_run.exception is not None
    assert context.active_feature_binding is None
    assert context.active_scenario_run is None
    assert context.last_error is scenario_run.exception
    assert context.stage == "inactive"
    assert context.status == "inactive"
    assert context.transition_index > final_snapshot_transition


def test_run_context_retains_interrupted_outcome_after_clearing_active_references() -> None:
    feature = Feature(name="Interrupted", uri="interrupted.feature")
    scenario = Scenario(name="Interrupted scenario")
    context = RunContext()
    scenario_run = context.start_scenario(
        nodeid="interrupted.feature::Interrupted scenario",
        feature=feature,
        scenario=scenario,
    )
    interruption = KeyboardInterrupt("interrupt sentinel")

    context.finish_active(status="interrupted", exception=interruption)
    context.clear_active()

    assert context.active_feature_binding is None
    assert context.active_scenario_run is None
    assert context.status == "inactive"
    assert context.last_error is interruption
    assert scenario_run.status == "interrupted"
    assert scenario_run.exception is interruption


def test_runtime_attempt_ids_exist_without_messages_and_are_isolated() -> None:
    context = RunContext()
    feature = Feature(name="Runtime attempts", uri="attempts.feature")
    first = Scenario(name="First row", id="pickle-first")
    second = Scenario(name="Second row", id="pickle-second")

    first_run = context.start_scenario(
        nodeid="attempts.feature::First row",
        feature=feature,
        scenario=first,
    )
    first_attempt_id = first_run.attempt_id
    assert first_attempt_id
    assert not first_run.test_case_started_id
    context.finish_active(status="passed")
    context.clear_active()

    second_run = context.start_scenario(
        nodeid="attempts.feature::Second row",
        feature=feature,
        scenario=second,
    )

    assert second_run.attempt_id
    assert second_run.attempt_id != first_attempt_id
    assert not second_run.test_case_started_id
    assert second_run.steps == []
    assert second_run.current_step_run is None
    assert second_run.previous_step_run is None
    assert first_run.attempt_id == first_attempt_id
    assert context.get_scenario_run(first_run.nodeid, attempt=0) is first_run
    assert context.get_scenario_run(second_run.nodeid, attempt=0) is second_run


def test_mock_run_finish_phase_does_not_claim_bdd_after_scenario_hook() -> None:
    feature = Feature(name="Validation", uri="validation.feature")
    scenario = Scenario(name="Binding validation")
    context = RunContext()
    scenario_run = context.start_scenario(
        nodeid="validation.feature::Binding validation",
        feature=feature,
        scenario=scenario,
    )

    context.finish_active(status="passed", hook_phase="pytest_runtest_call")

    assert context.hook_phase == "pytest_runtest_call"
    assert scenario_run.hook_phase == "pytest_runtest_call"
    assert scenario_run.status == "passed"
