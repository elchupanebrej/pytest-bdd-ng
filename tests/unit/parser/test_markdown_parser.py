from __future__ import annotations

from pytest_bdd.parser import MarkdownParser


def test_parse_basic_markdown_feature() -> None:
    text = """# Feature: Markdown Feature

  Markdown description

  ## Background:
  * Given a background step

  `@scenario_tag`
  ## Scenario: Markdown Scenario
  * Given a step
  * When an action occurs
  * Then an outcome is observed
"""
    parser = MarkdownParser()
    feature = parser.parse_text(text, uri="test.feature.md")

    assert feature.name == "Markdown Feature"
    assert feature.background is not None
    assert len(feature.background.steps) == 1
    assert feature.background.steps[0].name == "a background step"

    assert len(feature.scenarios) == 1
    sc = feature.scenarios[0]
    assert sc.name == "Markdown Scenario"
    assert [t.name for t in sc.tags] == ["@scenario_tag"]
    assert len(sc.steps) == 3
    assert [s.name for s in sc.steps] == ["a step", "an action occurs", "an outcome is observed"]


def test_parse_markdown_docstrings_and_datatables() -> None:
    text = """# Feature: Rich Markdown Steps

  ## Scenario: Markdown with Rich Steps
  * Given a docstring step
  ```text/plain
  DocString line 1
  DocString line 2
  ```
  * When a datatable step
    | name  | age |
    | Alice | 30  |
    | Bob   | 25  |
"""
    parser = MarkdownParser()
    feature = parser.parse_text(text)

    sc = feature.scenarios[0]
    step_doc = sc.steps[0]
    assert step_doc.doc_string is not None
    assert "DocString line 1\nDocString line 2" in step_doc.doc_string.content
    assert step_doc.doc_string.media_type == "text/plain"

    step_dt = sc.steps[1]
    assert step_dt.data_table is not None
    assert len(step_dt.data_table.rows) == 3
    assert [c.value for c in step_dt.data_table.rows[0].cells] == ["name", "age"]
    assert [c.value for c in step_dt.data_table.rows[1].cells] == ["Alice", "30"]


def test_parse_markdown_scenario_outline_and_examples() -> None:
    text = """# Feature: Markdown Outlines

  `@outline_tag`
  ## Scenario Outline: Outline in Markdown
  * Given cucumber count <start>
  * When I eat <eat>
  * Then remaining is <left>

  `@example_tag`
  ### Examples:
    | start | eat | left |
    |    10 |   3 |    7 |
    |    20 |   5 |   15 |
"""
    parser = MarkdownParser()
    feature = parser.parse_text(text)

    sc = feature.scenarios[0]
    assert len(sc.examples) == 1
    ex = sc.examples[0]
    assert [t.name for t in ex.tags] == ["@example_tag"]
    assert ex.header is not None
    assert [c.value for c in ex.header.cells] == ["start", "eat", "left"]
    assert len(ex.rows) == 2
    assert [r.cells[0].value for r in ex.rows] == ["10", "20"]
