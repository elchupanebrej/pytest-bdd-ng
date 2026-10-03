from __future__ import annotations

import pytest

import messages
from pytest_cuke.exceptions import FeatureConcreteParseError
from pytest_cuke.model import message_converter as mc
from pytest_cuke.model.background import Background
from pytest_cuke.model.doc_string import DocString
from pytest_cuke.model.feature import Feature
from pytest_cuke.model.rule import Rule
from pytest_cuke.model.scenario import Scenario
from pytest_cuke.model.step import Step
from pytest_cuke.model.table import DataTable, TableCell, TableRow
from pytest_cuke.model.tag import Tag

pytestmark = pytest.mark.unit


def test_feature_to_gherkin_document_conversion() -> None:
    step1 = Step(name="an item exists", keyword="Given ", line=5)
    doc_str = DocString(content="hello world", media_type="text/plain", line=8)
    table = DataTable(rows=(TableRow(cells=(TableCell(value="v1", line=10),), line=10),), line=10)
    step2 = Step(name="details are provided", keyword="When ", line=7, doc_string=doc_str, data_table=table)

    bg = Background(name="Setup", keyword="Background", line=4, steps=(step1,))
    sc = Scenario(name="Scenario 1", keyword="Scenario", line=6, steps=(step2,), tags=(Tag(name="@unit", line=6),))
    rule = Rule(name="Rule 1", keyword="Rule", line=12, scenarios=(sc,))

    feature = Feature(
        name="Cart Feature",
        description="Handles user carts",
        uri="features/cart.feature",
        line=1,
        tags=(Tag(name="@feature_tag", line=1),),
        background=bg,
        scenarios=(sc,),
        rules=(rule,),
    )

    doc = mc.feature_to_gherkin_document(feature)
    assert doc.uri == "features/cart.feature"
    assert doc.feature is not None
    assert doc.feature.name == "Cart Feature"
    assert len(doc.feature.tags) == 1
    assert doc.feature.tags[0].name == "@feature_tag"
    assert len(doc.feature.children) == 3  # bg, sc, rule

    env = mc.feature_to_envelope(feature)
    assert env.gherkin_document is not None
    assert env.gherkin_document.feature is not None
    assert env.gherkin_document.feature.name == "Cart Feature"
    mc.validate_envelope_shape(env)


def test_validate_envelope_shape_error() -> None:
    empty_env = cucumber_messages.Envelope()
    with pytest.raises(TypeError, match="exactly one payload"):
        mc.validate_envelope_shape(empty_env)


def test_parse_error_envelope_preserves_source_and_uses_one_based_location() -> None:
    error = FeatureConcreteParseError("invalid syntax", 6, "  open", "features/broken.feature.md", column=0)

    envelope = mc.parse_error_to_envelope(error)

    assert envelope.parse_error is not None
    assert envelope.parse_error.message == "invalid syntax"
    assert envelope.parse_error.source.uri == "features/broken.feature.md"
    assert envelope.parse_error.source.location is not None
    assert envelope.parse_error.source.location.line == 6
    assert envelope.parse_error.source.location.column == 1
    mc.validate_envelope_shape(envelope)
    assert messages.Envelope.model_validate(envelope.model_dump(exclude_none=True, by_alias=True)) == envelope

    missing_source = FeatureConcreteParseError("invalid syntax", 0, "", "")
    with pytest.raises(ValueError, match="positive source line and non-empty URI"):
        mc.parse_error_to_envelope(missing_source)


def test_scenario_to_pickle_and_test_case() -> None:
    step = Step(name="user logs in", keyword="Given ", line=4, id="step-1")
    sc = Scenario(name="Login", keyword="Scenario", line=3, id="sc-1", steps=(step,), tags=(Tag(name="@auth", line=3),))

    pickle = mc.scenario_to_pickle(sc, uri="auth.feature")
    assert pickle.name == "Login"
    assert pickle.uri == "auth.feature"
    assert len(pickle.steps) == 1
    assert pickle.steps[0].text == "user logs in"
    assert len(pickle.tags) == 1
    assert pickle.tags[0].name == "@auth"
    assert pickle.ast_node_ids == ["sc-1"]

    outline_row = Scenario(
        name="Outline row",
        id="expanded-row-id",
        source_ast_node_ids=("outline-source-id", "examples-row-source-id"),
        steps=(step,),
    )
    outline_pickle = mc.scenario_to_pickle(outline_row)
    assert outline_pickle.ast_node_ids == ["outline-source-id", "examples-row-source-id"]
    assert outline_pickle.steps[0].id == "expanded-row-id-step-0"
    outline_test_case = mc.scenario_to_test_case(outline_row, pickle_id=outline_pickle.id)
    assert outline_test_case.test_steps[0].pickle_step_id == "expanded-row-id-step-0"

    struct_scenario = Scenario(name="Struct route", line=0)
    struct_pickle = mc.scenario_to_pickle(
        struct_scenario,
        uri="file:routes.bdd.yaml",
        default_id="file:routes.bdd.yaml#route-case-1",
    )
    struct_document = mc.feature_to_gherkin_document(
        Feature(name="Routes", uri="file:routes.bdd.yaml", scenarios=(struct_scenario,))
    )
    struct_test_case = mc.scenario_to_test_case(struct_scenario, pickle_id=struct_pickle.id)
    assert struct_pickle.id == "file:routes.bdd.yaml#route-case-1"
    assert struct_document.feature is not None
    struct_document_scenario = struct_document.feature.children[0].scenario
    assert struct_document_scenario is not None
    assert struct_pickle.ast_node_ids == [struct_document_scenario.id]
    assert struct_test_case.pickle_id == struct_pickle.id

    p_env = mc.pickle_to_envelope(pickle)
    assert p_env.pickle is not None
    mc.validate_envelope_shape(p_env)

    tc = mc.scenario_to_test_case(sc, pickle_id=pickle.id)
    assert tc.pickle_id == pickle.id
    assert len(tc.test_steps) == 1
    assert tc.test_steps[0].pickle_step_id == "step-1"

    tc_env = mc.test_case_to_envelope(tc)
    assert tc_env.test_case is not None
    mc.validate_envelope_shape(tc_env)


def test_scenario_execution_metadata_includes_feature_and_rule_backgrounds_in_order() -> None:
    feature_step = Step(name="the repeated setup step", keyword="Given ", id="feature-step")
    rule_step = Step(name="the repeated setup step", keyword="Given ", id="rule-step")
    scenario_step = Step(name="the repeated setup step", keyword="When ", id="scenario-step")
    feature_background = Background(id="feature-background", steps=(feature_step,))
    rule_background = Background(id="rule-background", steps=(rule_step,))
    feature = Feature(name="Layered backgrounds", background=feature_background)
    scenario = Scenario(
        name="An outline row",
        id="expanded-row",
        background=rule_background,
        steps=(scenario_step,),
        source_ast_node_ids=("outline-id", "row-id"),
    )

    pickle = mc.scenario_to_pickle(scenario, feature=feature)
    test_case = mc.scenario_to_test_case(scenario, pickle_id=pickle.id, feature=feature)

    assert [step.text for step in pickle.steps] == [
        "the repeated setup step",
        "the repeated setup step",
        "the repeated setup step",
    ]
    assert [step.id for step in pickle.steps] == [
        "expanded-row-step-0",
        "expanded-row-step-1",
        "expanded-row-step-2",
    ]
    assert [step.pickle_step_id for step in test_case.test_steps] == [step.id for step in pickle.steps]
    assert [step.ast_node_ids for step in pickle.steps] == [["feature-step"], ["rule-step"], ["scenario-step"]]


def test_scenario_pickle_uses_feature_background_when_scenario_has_no_background() -> None:
    background_step = Step(name="feature setup", keyword="Given ", id="feature-step")
    scenario_step = Step(name="scenario action", keyword="When ", id="scenario-step")
    feature = Feature(name="Feature background", background=Background(steps=(background_step,)))
    scenario = Scenario(name="Scenario without copied background", steps=(scenario_step,))

    pickle = mc.scenario_to_pickle(scenario, feature=feature)

    assert [step.text for step in pickle.steps] == ["feature setup", "scenario action"]


def test_execution_message_helpers_and_dict_roundtrip() -> None:
    env_run_start = mc.make_test_run_started(100.0)
    assert env_run_start.test_run_started is not None
    assert env_run_start.test_run_started.timestamp.seconds == 100

    env_tc_start = mc.make_test_case_started(test_case_id="tc-1", id="tcs-1", attempt=0, timestamp=101.0)
    assert env_tc_start.test_case_started is not None
    assert env_tc_start.test_case_started.test_case_id == "tc-1"

    env_ts_start = mc.make_test_step_started(test_case_started_id="tcs-1", test_step_id="ts-1", timestamp=102.0)
    assert env_ts_start.test_step_started is not None

    env_ts_finish = mc.make_test_step_finished(
        test_case_started_id="tcs-1", test_step_id="ts-1", status="passed", duration=0.5, timestamp=102.5
    )
    assert env_ts_finish.test_step_finished is not None
    assert env_ts_finish.test_step_finished.test_step_result.status == cucumber_messages.TestStepResultStatus.passed

    env_tc_finish = mc.make_test_case_finished(test_case_started_id="tcs-1", timestamp=103.0)
    assert env_tc_finish.test_case_finished is not None

    env_run_finish = mc.make_test_run_finished(timestamp=104.0, success=True)
    assert env_run_finish.test_run_finished is not None

    d = mc.envelope_to_dict(env_run_finish)
    assert "testRunFinished" in d
    reloaded = mc.envelope_from_dict(d)
    assert reloaded.test_run_finished is not None
    assert reloaded.test_run_finished.success is True
