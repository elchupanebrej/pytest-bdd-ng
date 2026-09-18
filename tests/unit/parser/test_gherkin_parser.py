from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from pytest_bdd.exceptions import FeatureConcreteParseError
from pytest_bdd.gherkin_builder import build_feature_from_dict
from pytest_bdd.model.step import StepType
from pytest_bdd.parser import GherkinParser, default_parser_registry

pytestmark = pytest.mark.unit


if TYPE_CHECKING:
    from pathlib import Path


def test_parse_basic_gherkin_feature() -> None:
    text = """
    @feature_tag
    Feature: Basic Feature
      This is a basic feature description.

      Background:
        Given background step

      @scenario_tag
      Scenario: Basic Scenario
        Given a step
        When action occurs
        Then outcome expected
    """
    parser = GherkinParser()
    feature = parser.parse_text(text, uri="test.feature")

    assert feature.name == "Basic Feature"
    assert "basic feature description" in feature.description
    assert [t.name for t in feature.tags] == ["@feature_tag"]
    assert feature.background is not None
    assert len(feature.background.steps) == 1
    assert feature.background.steps[0].name == "background step"

    assert len(feature.scenarios) == 1
    sc = feature.scenarios[0]
    assert sc.name == "Basic Scenario"
    assert [t.name for t in sc.tags] == ["@scenario_tag"]
    assert len(sc.steps) == 3
    assert [s.name for s in sc.steps] == ["a step", "action occurs", "outcome expected"]


def test_parse_normalizes_step_type_vocabulary() -> None:
    text = """
    Feature: Vocabulary Feature
      Scenario: Conjunctions inherit the previous step type
        Given a precondition
        And another precondition
        When an action occurs
        But not this one
        Then an outcome is expected

      Scenario: Leading conjunction
        And an orphaned step
    """
    parser = GherkinParser()
    feature = parser.parse_text(text)

    steps = feature.scenarios[0].steps
    assert [s.keyword for s in steps] == ["Given", "And", "When", "But", "Then"]
    assert [s.prefix for s in steps] == ["given", "and", "when", "but", "then"]
    assert [s.type for s in steps] == [
        StepType.context,
        StepType.context,
        StepType.action,
        StepType.action,
        StepType.outcome,
    ]

    assert feature.scenarios[1].steps[0].type is StepType.unknown


def test_parse_docstrings_and_datatables() -> None:
    text = """
    Feature: Rich Steps Feature
      Scenario: Rich Step Scenario
        Given a docstring step
          \"\"\"text/plain
          Line 1
          Line 2
          \"\"\"
        When a datatable step
          | name  | age |
          | Alice | 30  |
          | Bob   | 25  |
    """
    parser = GherkinParser()
    feature = parser.parse_text(text)

    sc = feature.scenarios[0]
    step_doc = sc.steps[0]
    assert step_doc.doc_string is not None
    assert "Line 1\nLine 2" in step_doc.doc_string.content
    assert step_doc.doc_string.media_type == "text/plain"

    step_dt = sc.steps[1]
    assert step_dt.data_table is not None
    assert len(step_dt.data_table.rows) == 3
    assert [c.value for c in step_dt.data_table.rows[0].cells] == ["name", "age"]
    assert [c.value for c in step_dt.data_table.rows[1].cells] == ["Alice", "30"]


def test_parse_scenario_outline_and_examples() -> None:
    text = """
    Feature: Outline Feature
      @outline_tag
      Scenario Outline: Outline Scenario
        Given step with <var>
        When action with <var>
        Then result is <var>

        @example_tag
        Examples:
          | var |
          | one |
          | two |
    """
    parser = GherkinParser()
    feature = parser.parse_text(text)

    sc = feature.scenarios[0]
    assert len(sc.examples) == 1
    ex = sc.examples[0]
    assert [t.name for t in ex.tags] == ["@example_tag"]
    assert ex.header is not None
    assert [c.value for c in ex.header.cells] == ["var"]
    assert len(ex.rows) == 2
    assert [r.cells[0].value for r in ex.rows] == ["one", "two"]


def test_parse_rules_with_scenarios() -> None:
    text = """
    Feature: Rule Feature
      Rule: First Rule
        Background:
          Given rule background step

        @rule_sc_tag
        Scenario: Scenario inside rule
          Given inside rule
    """
    parser = GherkinParser()
    feature = parser.parse_text(text)

    assert len(feature.rules) == 1
    rule = feature.rules[0]
    assert rule.name == "First Rule"
    assert rule.background is not None
    assert len(rule.scenarios) == 1
    assert rule.scenarios[0].name == "Scenario inside rule"
    assert [t.name for t in rule.scenarios[0].tags] == ["@rule_sc_tag"]


def test_parse_syntax_error_raises_feature_concrete_parse_error() -> None:
    text = """
    Feature: Broken
      Scenario: Broken Scenario
        Given something
        Invalid syntax without keyword
    """
    parser = GherkinParser()
    with pytest.raises(FeatureConcreteParseError) as exc_info:
        parser.parse_text(text, uri="broken.feature")

    assert exc_info.value.args[1] > 0
    assert exc_info.value.args[3] == "broken.feature"
    assert "Line number:" in str(exc_info.value)


def test_parse_file_path(tmp_path: Path) -> None:
    feature_file = tmp_path / "example.feature"
    feature_file.write_text(
        "Feature: File Feature\n  Scenario: File Scenario\n    Given file step\n",
        encoding="utf-8",
    )
    parser = GherkinParser()
    feature = parser.parse(feature_file)
    assert feature.name == "File Feature"
    assert feature.filename == str(feature_file.as_posix())


def test_default_registry_has_gherkin_parser() -> None:
    p1 = default_parser_registry.get_parser_for_path("test.feature")
    p2 = default_parser_registry.get_parser_for_path("test.gherkin")
    p3 = default_parser_registry.get_parser_for_mimetype("text/x-gherkin")

    assert isinstance(p1, GherkinParser)
    assert isinstance(p2, GherkinParser)
    assert isinstance(p3, GherkinParser)


def test_build_feature_from_raw_dict_tolerates_variants() -> None:
    raw = {
        "feature": {
            "name": "Raw Feature",
            "keyword": "Feature",
            "language": "en",
            "location": {"line": 1},
            "children": [
                {"unknownChild": {}},
                {
                    "scenario": {
                        "name": "Scenario",
                        "keyword": "Scenario",
                        "location": {"line": 2},
                        "steps": [
                            {
                                "text": "mystery step",
                                "keyword": "Mystery",
                                "keywordType": "Weird",
                                "location": {"line": 3},
                            },
                            {
                                "text": "keywordless step",
                                "keyword": "Mystery",
                                "location": {"line": 4},
                            },
                        ],
                        "examples": [
                            {"name": "no header", "keyword": "Examples", "tableBody": [], "location": {"line": 5}}
                        ],
                    }
                },
                {
                    "rule": {
                        "name": "Rule",
                        "keyword": "Rule",
                        "location": {"line": 5},
                        "children": [
                            {"unknownChild": {}},
                            {
                                "scenario": {
                                    "name": "Rule Scenario",
                                    "keyword": "Scenario",
                                    "location": {"line": 6},
                                    "steps": [],
                                }
                            },
                        ],
                    }
                },
            ],
        }
    }

    feature = build_feature_from_dict(raw, uri="raw.feature")

    assert feature.name == "Raw Feature"
    assert [scenario.name for scenario in feature.scenarios] == ["Scenario"]
    assert [step.type for step in feature.scenarios[0].steps] == [StepType.unknown, StepType.unknown]
    assert feature.scenarios[0].examples[0].header is None
    assert [scenario.name for scenario in feature.rules[0].scenarios] == ["Rule Scenario"]
