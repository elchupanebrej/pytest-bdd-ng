from pathlib import Path

from attrs import evolve
from gherkin.parser import Parser

from pytest_cuke.gherkin_builder import build_feature_from_dict
from pytest_cuke.model.feature import Feature
from pytest_cuke.model.serialization import as_dict, from_dict, from_json, to_json
from pytest_cuke.model.message_converter import feature_to_gherkin_document, scenario_to_pickle
from pytest_cuke.model.message_types import GherkinDocument, message_from_dict

SOURCE = Path(__file__).parents[2].joinpath("data", "source-navigation.feature").read_text()


def test_projection_preserves_the_official_source_ast_without_reparsing(monkeypatch):
    raw = Parser().parse(SOURCE)
    feature = build_feature_from_dict(raw, uri="features/navigation.feature")
    expected = message_from_dict(raw, GherkinDocument)
    expected.uri = feature.uri

    def no_reparse(*args, **kwargs):
        raise AssertionError("a source projection must not parse the feature again")

    monkeypatch.setattr(Parser, "parse", no_reparse)
    document = feature_to_gherkin_document(feature)
    assert document == expected
    assert document.feature is not None
    document.feature.name = "observer mutation"
    assert feature_to_gherkin_document(feature) == expected


def test_structural_model_edits_use_the_model_projection():
    feature = build_feature_from_dict(Parser().parse(SOURCE), uri="features/navigation.feature")
    edited = evolve(feature, name="Edited feature")
    document = feature_to_gherkin_document(edited)
    assert document.feature is not None
    assert document.feature.name == "Edited feature"
    assert feature.name == "Source navigation"


def test_pickle_uses_the_source_row_location_and_inherited_feature_tags():
    raw = Parser().parse(SOURCE)
    feature = build_feature_from_dict(raw, uri="features/navigation.feature")
    scenario = feature.rules[0].scenarios[0]
    row = scenario.examples[0].rows[0]
    expanded = evolve(scenario, examples=(), source_ast_node_ids=(scenario.id, row.id))
    pickle = scenario_to_pickle(expanded, uri=feature.uri, feature=feature)
    assert pickle.location is not None
    assert pickle.location.line == row.line
    assert pickle.location.column == 9
    assert "@feature-tag" in {tag.name for tag in pickle.tags}


def test_unknown_outline_row_location_is_not_replaced_by_the_heading_location():
    feature = build_feature_from_dict(Parser().parse(SOURCE), uri="features/navigation.feature")
    scenario = feature.rules[0].scenarios[0]
    expanded = evolve(scenario, examples=(), source_ast_node_ids=(scenario.id, "unknown-row"))
    assert scenario_to_pickle(expanded, uri=feature.uri, feature=feature).location is None


def test_parser_projection_stays_out_of_public_model_serialization():
    feature = build_feature_from_dict(Parser().parse(SOURCE), uri="features/navigation.feature")
    assert feature.source_projection is not None
    payload = as_dict(feature)
    assert "source_projection" not in payload
    restored = from_json(Feature, to_json(feature))
    assert restored == feature
    assert restored.source_projection is None
    assert feature_to_gherkin_document(restored, uri=feature.uri).feature.name == feature.name


def test_model_deserialization_does_not_accept_internal_projection_data():
    feature = build_feature_from_dict(Parser().parse(SOURCE), uri="features/navigation.feature")
    payload = as_dict(feature)
    payload["source_projection"] = {"document_json": "{}", "structure": [], "positions": []}
    restored = from_dict(Feature, payload)
    assert restored.source_projection is None
    assert restored == feature
