from __future__ import annotations

from typing import Any

import pytest

from pytest_cuke._native_go._bridge import gherkin_go_available
from pytest_cuke.exceptions import FeatureConcreteParseError
from pytest_cuke.model.serialization import as_dict
from pytest_cuke.parser import GherkinParser, MarkdownParser


FEATURE = """@feature-tag
Feature: Пользовательские данные
  Background: общая подготовка
    Given среда готова
  @rule-tag
  Rule: поиск
    Background: подготовка правила
      Given каталог доступен
    @scenario-tag
    Scenario Outline: найти <значение>
      Given таблица:
        | поле | значение |
        | имя | <значение> |
      And документ:
        \"\"\"
        значение: <значение>
        \"\"\"
      Then найдено <значение>

      @example-tag
      Examples: значения
        | значение |
        | café |
        | 示例 |
"""


def _without_ids(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _without_ids(child) for key, child in value.items() if key != "id"}
    if isinstance(value, list | tuple):
        return [_without_ids(child) for child in value]
    return value


def _require_native_parser() -> None:
    if not gherkin_go_available():
        pytest.skip("requires a host-built pytest-cuke wheel with the Go parser library")


def test_native_parser_preserves_immutable_feature_model_fields() -> None:
    _require_native_parser()

    python_feature = GherkinParser().parse_text(FEATURE, parser_mode="python")
    native_feature = GherkinParser().parse_text(FEATURE, parser_mode="go")

    assert _without_ids(as_dict(native_feature)) == _without_ids(as_dict(python_feature))
    assert native_feature.name == "Пользовательские данные"
    assert native_feature.line == 2
    assert [tag.name for tag in native_feature.tags] == ["@feature-tag"]
    assert native_feature.background is not None
    assert native_feature.background.name == "общая подготовка"
    assert native_feature.background.line == 3

    rule = native_feature.rules[0]
    assert rule.name == "поиск"
    assert rule.line == 6
    assert [tag.name for tag in rule.tags] == ["@rule-tag"]
    assert rule.background is not None
    assert rule.background.name == "подготовка правила"

    scenario = rule.scenarios[0]
    assert scenario.line == 10
    assert [tag.name for tag in scenario.tags] == ["@rule-tag", "@scenario-tag"]
    assert scenario.steps[0].line == 11
    assert scenario.steps[0].data_table is not None
    assert scenario.steps[0].data_table.raw == [["поле", "значение"], ["имя", "<значение>"]]
    assert scenario.steps[1].doc_string is not None
    assert scenario.steps[1].doc_string.content == "значение: <значение>"

    examples = scenario.examples[0]
    assert examples.line == 21
    assert [tag.name for tag in examples.tags] == ["@example-tag"]
    assert examples.as_dicts() == [{"значение": "café"}, {"значение": "示例"}]


def test_auto_uses_python_markdown_model_when_native_parser_cannot_parse_it() -> None:
    _require_native_parser()
    markdown = "# Feature: Markdown\n\n## Scenario: Python markdown\n* Given a step\n"
    python_feature = MarkdownParser().parse_text(markdown, parser_mode="python")

    with pytest.warns(RuntimeWarning, match="falling back to Python"):
        auto_feature = MarkdownParser().parse_text(markdown, parser_mode="auto")

    assert _without_ids(as_dict(auto_feature)) == _without_ids(as_dict(python_feature))
    assert auto_feature.name == "Markdown"
    assert auto_feature.scenarios[0].name == "Python markdown"


def test_auto_keeps_python_location_for_malformed_input_rejected_by_native_parser() -> None:
    _require_native_parser()
    malformed = (
        "Feature: Broken\n  Scenario: Broken\n    Given a valid first step\n    Invalid syntax without keyword\n"
    )

    with pytest.raises(FeatureConcreteParseError) as error:
        GherkinParser().parse_text(malformed, uri="broken.feature", parser_mode="auto")

    assert error.value.args[1] == 4
    assert error.value.args[3] == "broken.feature"
