from __future__ import annotations

from pytest_bdd.parser import GherkinParser


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
