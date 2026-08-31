"""Unit tests for external CSV and TSV Examples sources."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from pytest_bdd.collector_batch import FeatureBatchParser
from pytest_bdd.util.external_examples import ExternalExamplesError, expand_external_examples
from pytest_bdd.parser import GherkinParser
from pytest_bdd.util.other import IdGenerator

pytestmark = [pytest.mark.unit]


def _config() -> SimpleNamespace:
    """Build the minimal parser configuration used by the parser unit tests."""
    return SimpleNamespace(stash={IdGenerator.STASH_KEY: IdGenerator()}, hook=SimpleNamespace())


def test_csv_examples_source_is_loaded_relative_to_feature(tmp_path) -> None:
    """Load CSV headers and rows into a scenario outline Examples table."""
    feature_path = tmp_path / "features" / "users.feature"
    feature_path.parent.mkdir()
    (feature_path.parent / "data.csv").write_text("name,role\nAda,admin\nGrace,developer\n", encoding="utf-8")
    feature_path.write_text(
        "Feature: Users\n"
        "  Scenario Outline: User\n"
        "    Given <name> is a <role>\n"
        "    Examples:\n"
        "      | table: data.csv |\n",
        encoding="utf-8",
    )

    parsed = GherkinParser(id_generator=IdGenerator()).parse(_config(), feature_path, "file:users.feature")
    examples = parsed.gherkin_document.feature.children[0].scenario.examples[0]

    assert [cell.value for cell in examples.table_header.cells] == ["name", "role"]
    assert [[cell.value for cell in row.cells] for row in examples.table_body] == [
        ["Ada", "admin"],
        ["Grace", "developer"],
    ]


def test_tsv_examples_source_supports_bracket_marker(tmp_path) -> None:
    """Load a TSV source referenced with the alternate table marker syntax."""
    feature_path = tmp_path / "users.feature"
    (tmp_path / "data.tsv").write_text("name\trole\nAda\tadmin\n", encoding="utf-8")
    feature_path.write_text(
        "Feature: Users\n  Scenario Outline: User\n    Given <name> is a <role>\n    Examples: <table:data.tsv>\n",
        encoding="utf-8",
    )

    expanded = expand_external_examples(feature_path.read_text(encoding="utf-8"), feature_path)

    assert "| name | role |" in expanded
    assert "| Ada | admin |" in expanded


def test_inline_pipe_marker_is_expanded(tmp_path) -> None:
    """Support the compact one-line Examples marker spelling."""
    source = tmp_path / "users.csv"
    source.write_text("name,role\nAda,admin\n", encoding="utf-8")
    feature = tmp_path / "users.feature"

    rendered = expand_external_examples("Examples: | table: users.csv |\n", feature)

    assert rendered == "Examples:\n| name | role |\n| Ada | admin |\n"


def test_missing_examples_source_is_a_collection_error(tmp_path) -> None:
    """Reject a missing external table with its resolved feature-relative path."""
    feature_path = tmp_path / "users.feature"
    feature_path.write_text("Feature: Users\n  Examples: table: missing.csv\n", encoding="utf-8")

    with pytest.raises(ExternalExamplesError, match=r"missing\.csv"):
        expand_external_examples(feature_path.read_text(encoding="utf-8"), feature_path)

    batch_parser = FeatureBatchParser()
    batch_parser.register(feature_path)
    with pytest.raises(ExternalExamplesError, match=r"missing\.csv"):
        batch_parser.flush()
