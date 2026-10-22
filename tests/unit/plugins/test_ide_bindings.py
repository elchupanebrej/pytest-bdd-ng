from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from pytest_cuke.ide_bindings import IdeBindingCollection, match_arguments, source_identity
from pytest_cuke.model.examples import Examples
from pytest_cuke.model.feature import Feature
from pytest_cuke.model.feature_binding import FeatureRuntimeBinding
from pytest_cuke.model.scenario import Scenario
from pytest_cuke.model.step import Step
from pytest_cuke.model.table import TableCell, TableRow
from pytest_cuke.scenario_locator import ScenarioLocatorFilterMixin


def test_outline_source_identities_point_to_distinct_examples_rows(tmp_path: Path) -> None:
    first_row = TableRow(cells=(TableCell("one"),), line=8, id="row-one")
    second_row = TableRow(cells=(TableCell("two"),), line=9, id="row-two")
    examples = Examples(
        header=TableRow(cells=(TableCell("value"),), line=7, id="header"),
        rows=(first_row, second_row),
        line=6,
        id="examples",
    )
    outline = Scenario(
        name="use <value>",
        line=3,
        id="outline",
        examples=(examples,),
        steps=(Step(name="use <value>", keyword="Given ", line=4, id="step"),),
    )
    feature = Feature(
        name="Example row identity",
        uri=(tmp_path / "row-identities.feature").as_uri(),
        scenarios=(outline,),
    )
    binding = FeatureRuntimeBinding.from_feature(feature)
    expanded = [scenario for _, scenario in ScenarioLocatorFilterMixin().filter_scenarios(feature)]

    first = source_identity(feature, expanded[0], binding)
    second = source_identity(feature, expanded[1], binding)

    assert first["uri"] == feature.uri
    assert first["line"] == first_row.line
    assert first["scenarioLine"] == outline.line
    assert first["rowId"] == first_row.id
    assert second["line"] == second_row.line
    assert second["rowId"] == second_row.id
    assert first != second


def test_scenario_source_identity_uses_scenario_location(tmp_path: Path) -> None:
    scenario = Scenario(name="regular", line=4, id="scenario")
    feature = Feature(
        name="Regular scenario identity",
        uri=(tmp_path / "regular.feature.md").as_uri(),
        scenarios=(scenario,),
    )

    identity = source_identity(feature, scenario)

    assert identity["uri"] == feature.uri
    assert identity["line"] == scenario.line
    assert identity["scenarioLine"] == scenario.line
    assert identity["scenarioId"] == scenario.id


def test_relative_parser_uri_resolves_through_feature_filename(tmp_path: Path) -> None:
    feature_path = tmp_path / "features" / "parser.feature"
    feature_path.parent.mkdir()
    feature_path.touch()
    feature = Feature(
        name="Parser source identity",
        uri="parser.feature",
        filename=str(feature_path),
        scenarios=(Scenario(name="regular", line=4, id="scenario"),),
    )

    identity = source_identity(feature, feature.scenarios[0])

    assert identity["uri"] == feature_path.as_uri()
    assert identity["scenarioUri"] == feature_path.as_uri()


def test_relative_file_uri_resolves_through_feature_filename(tmp_path: Path) -> None:
    feature_path = tmp_path / "features" / "parser.feature"
    feature_path.parent.mkdir()
    feature_path.touch()
    feature = Feature(
        name="Parser source identity",
        uri="file:parser.feature",
        filename=str(feature_path),
        scenarios=(Scenario(name="regular", line=4, id="scenario"),),
    )

    identity = source_identity(feature, feature.scenarios[0])

    assert identity["uri"] == feature_path.as_uri()
    assert identity["scenarioUri"] == feature_path.as_uri()


def test_match_arguments_preserves_one_shot_parameter_names() -> None:
    class Parser:
        def parse_arguments(self, request: object, name: str, anonymous_group_names: object) -> dict[str, str]:
            return {parameter_name: name for parameter_name in anonymous_group_names}

    definition = SimpleNamespace(parser=Parser(), anonymous_group_names=iter(["value"]))
    step = Step(name="the source row is 11", keyword="Given ")

    arguments = match_arguments(definition, object(), step)

    assert arguments == [{"name": "value", "value": "the source row is 11"}]
    assert tuple(definition.anonymous_group_names) == ("value",)


def test_match_arguments_swallows_normalization_errors() -> None:
    recursive_value: dict[str, object] = {}
    recursive_value["self"] = recursive_value

    class Parser:
        def parse_arguments(self, request: object, name: str, anonymous_group_names: object) -> dict[str, object]:
            return {"value": recursive_value}

    definition = SimpleNamespace(parser=Parser(), anonymous_group_names=None)
    step = Step(name="the recursive value", keyword="Given ")

    assert match_arguments(definition, object(), step) == []


def test_worker_output_merges_split_duplicate_bindings_with_case_ids() -> None:
    identity = {"uri": "file:///features/account.feature", "line": 7}
    first_worker = IdeBindingCollection()
    first_worker.register_source(identity, "tests/test_account.py::test_scenario")
    first_worker.record_test_case("tests/test_account.py::test_scenario", "case-1")

    second_worker = IdeBindingCollection()
    second_worker.register_source(identity, "tests/test_account_alias.py::test_scenario")
    second_worker.record_test_case("tests/test_account_alias.py::test_scenario", "case-2")

    controller = IdeBindingCollection()
    controller.merge_worker_output(first_worker.to_worker_output())
    controller.merge_worker_output(second_worker.to_worker_output())

    assert controller.diagnostics() == [
        {
            "kind": "duplicate-bindings",
            "severity": "warning",
            "sourceIdentity": identity,
            "bindings": [
                {"nodeid": "tests/test_account.py::test_scenario", "testCaseId": "case-1"},
                {"nodeid": "tests/test_account_alias.py::test_scenario", "testCaseId": "case-2"},
            ],
        }
    ]


def test_worker_output_keeps_worker_identity_for_duplicate_case_ids() -> None:
    identity = {"uri": "file:///features/account.feature", "line": 7}
    first_worker = IdeBindingCollection()
    first_worker.register_source(identity, "tests/test_account.py::test_scenario")
    first_worker.record_test_case("tests/test_account.py::test_scenario", "case-1")

    second_worker = IdeBindingCollection()
    second_worker.register_source(identity, "tests/test_account_alias.py::test_scenario")
    second_worker.record_test_case("tests/test_account_alias.py::test_scenario", "case-2")

    controller = IdeBindingCollection()
    controller.merge_worker_output(first_worker.to_worker_output(), worker_id="gw0")
    controller.merge_worker_output(second_worker.to_worker_output(), worker_id="gw1")

    assert controller.diagnostics() == [
        {
            "kind": "duplicate-bindings",
            "severity": "warning",
            "sourceIdentity": identity,
            "bindings": [
                {"nodeid": "tests/test_account.py::test_scenario", "testCaseId": "case-1", "workerId": "gw0"},
                {
                    "nodeid": "tests/test_account_alias.py::test_scenario",
                    "testCaseId": "case-2",
                    "workerId": "gw1",
                },
            ],
        }
    ]


def test_worker_output_keeps_repeated_case_ids_for_same_nodeid() -> None:
    identity = {"uri": "file:///features/account.feature", "line": 7}
    first_worker = IdeBindingCollection()
    first_worker.register_source(identity, "tests/test_account.py::test_scenario")
    first_worker.record_test_case("tests/test_account.py::test_scenario", "case-1")

    second_worker = IdeBindingCollection()
    second_worker.register_source(identity, "tests/test_account.py::test_scenario")
    second_worker.record_test_case("tests/test_account.py::test_scenario", "case-2")

    controller = IdeBindingCollection()
    controller.merge_worker_output(first_worker.to_worker_output())
    controller.merge_worker_output(second_worker.to_worker_output())

    assert controller.diagnostics() == []


def test_diagnostics_report_unbound_sources_after_worker_merge() -> None:
    identity = {"uri": "file:///features/unbound.feature", "line": 11}
    worker = IdeBindingCollection()
    worker.register_source(identity)

    controller = IdeBindingCollection()
    controller.merge_worker_output(worker.to_worker_output())

    assert controller.diagnostics() == [
        {
            "kind": "unbound-scenario",
            "severity": "warning",
            "sourceIdentity": identity,
        }
    ]
