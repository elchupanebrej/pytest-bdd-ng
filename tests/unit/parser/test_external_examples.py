from __future__ import annotations

import csv
import os
from pathlib import Path

import pytest

from pytest_cuke.exceptions import FeatureConcreteParseError
from pytest_cuke.external_examples import expand_external_examples
from pytest_cuke.parser import GherkinParser, MarkdownParser
from pytest_cuke.scenario_locator import ScenarioLocatorFilterMixin


def _feature_source(examples_heading: str) -> str:
    return (
        "Feature: External examples\n"
        "  Scenario Outline: Read external rows\n"
        "    Given the value is <value>\n"
        f"    {examples_heading}"
    )


def _row_values(feature_path: Path) -> list[tuple[str, ...]]:
    feature = GherkinParser().parse(feature_path)
    examples = feature.scenarios[0].examples[0]
    return [row.values for row in examples.rows]


@pytest.mark.parametrize(
    "heading",
    [
        "Examples: table: users.csv\n",
        "Examples: <table:users.csv>\n",
        "Examples: | table: users.csv |\n",
        "Examples:\n    | table: users.csv |\n",
    ],
    ids=["inline-table-marker", "angle-table-marker", "inline-pipe-marker", "below-heading-marker"],
)
def test_external_examples_markers_load_feature_relative_csv(tmp_path, heading):
    feature_path = tmp_path / "feature.feature"
    (tmp_path / "users.csv").write_text("value\nfirst\nsecond\n", encoding="utf-8")
    feature_path.write_text(_feature_source(heading), encoding="utf-8")

    assert _row_values(feature_path) == [("first",), ("second",)]
    assert feature_path.read_text(encoding="utf-8").endswith(heading)


def test_inline_examples_tables_are_unchanged(tmp_path):
    feature_path = tmp_path / "feature.feature"
    feature_path.write_text(
        _feature_source("Examples: Named\n      | value |\n      | inline |\n"),
        encoding="utf-8",
    )

    assert _row_values(feature_path) == [("inline",)]


@pytest.mark.parametrize(
    "marker",
    [
        "Examples: table: missing.csv\n",
        "Examples: <table:missing.csv>\n",
        "Examples: | table: missing.csv |\n",
        "Examples:\n      | table: missing.csv |\n",
    ],
    ids=["heading", "angle", "inline-pipe", "below-heading"],
)
@pytest.mark.parametrize(
    "container",
    ["double-quote", "single-quote", "backtick-fence", "tilde-fence", "gherkin-comment"],
    ids=[
        "gherkin-double-docstring",
        "gherkin-single-docstring",
        "markdown-backtick-fence",
        "markdown-tilde-fence",
        "gherkin-comment",
    ],
)
def test_marker_spellings_inside_literal_regions_are_not_expanded(tmp_path, marker, container):
    data_path = tmp_path / "real.csv"
    data_path.write_text("value\nreal\n", encoding="utf-8")
    markdown = container.endswith("fence")
    feature_path = tmp_path / ("feature.feature.md" if markdown else "feature.feature")

    if container == "double-quote":
        literal = f'    Given literal content:\n      """\n{marker}      """\n'
    elif container == "single-quote":
        literal = f"    Given literal content:\n      '''\n{marker}      '''\n"
    elif container == "backtick-fence":
        literal = f"    ````gherkin\n{marker}    ````\n"
    elif container == "tilde-fence":
        literal = f"    ~~~~~gherkin\n{marker}    ~~~~~~\n"
    else:
        literal = f"    # {marker.strip()}\n"

    if markdown:
        content = (
            "# Feature: Literal markers\n"
            "## Scenario Outline: A real external source\n"
            "  * Given value <value>\n"
            f"{literal}"
            "### Examples: table: real.csv\n"
        )
    else:
        content = (
            "Feature: Literal markers\n"
            "  Scenario Outline: A real external source\n"
            "    Given value <value>\n"
            f"{literal}"
            "    Examples: table: real.csv\n"
        )

    expanded = expand_external_examples(content, feature_path)

    assert len(expanded.bindings) == 1
    assert expanded.bindings[0].source.path == str(data_path.resolve())
    assert "missing.csv" in expanded.content
    assert "| real |" in expanded.content


def test_markdown_fenced_code_blocks_close_only_with_matching_fence_character(tmp_path):
    feature_path = tmp_path / "feature.feature.md"
    data_path = tmp_path / "real.csv"
    data_path.write_text("value\nreal\n", encoding="utf-8")
    content = (
        "# Feature: Literal markers\n"
        "## Scenario Outline: A real external source\n"
        "  * Given value <value>\n"
        "    ~~~~gherkin\n"
        "Examples: table: missing.csv\n"
        "    ````\n"
        "    ~~~~~\n"
        "### Examples: table: real.csv\n"
    )

    expanded = expand_external_examples(content, feature_path)

    assert len(expanded.bindings) == 1
    assert expanded.bindings[0].source.path == str(data_path.resolve())
    assert "missing.csv" in expanded.content


def test_gherkin_examples_comment_is_not_an_external_source(tmp_path):
    feature_path = tmp_path / "feature.feature"
    data_path = tmp_path / "real.csv"
    data_path.write_text("value\nreal\n", encoding="utf-8")
    content = (
        "Feature: Gherkin comments\n"
        "  Scenario Outline: A real external source\n"
        "    Given value <value>\n"
        "    # Examples: table: missing.csv\n"
        "    Examples: table: real.csv\n"
    )

    expanded = expand_external_examples(content, feature_path)

    assert len(expanded.bindings) == 1
    assert expanded.bindings[0].source.path == str(data_path.resolve())
    assert "# Examples: table: missing.csv" in expanded.content


@pytest.mark.parametrize("suffix, delimiter", [("tsv", "\t"), ("tab", "\t")])
def test_markdown_outline_reads_bom_crlf_tsv_and_tab_sources(tmp_path, suffix, delimiter):
    feature_path = tmp_path / "outline.feature.md"
    data_path = tmp_path / f"users.{suffix}"
    data_path.write_bytes(
        f"\ufeffvalue{delimiter}kind\r\n\r\nfirst{delimiter}one\r\n\r\nsecond{delimiter}two\r\n".encode()
    )
    feature_path.write_text(
        "# Feature: External Markdown examples\r\n"
        "## Scenario Outline: Read external rows\r\n"
        "* Given the value is <value>\r\n"
        "### Examples:\r\n"
        f"    | table: {data_path.name} |\r\n",
        encoding="utf-8",
        newline="",
    )

    original_feature = feature_path.read_bytes()
    original_data = data_path.read_bytes()
    feature = MarkdownParser().parse(feature_path)
    examples = feature.scenarios[0].examples[0]
    assert examples.column_names == ("value", "kind")
    assert [row.values for row in examples.rows] == [("first", "one"), ("second", "two")]
    assert feature.uri == feature_path.as_posix()
    assert feature.filename == feature_path.as_posix()
    assert feature_path.read_bytes() == original_feature
    assert data_path.read_bytes() == original_data


def test_csv_escaping_preserves_empty_cells_and_special_values(tmp_path):
    feature_path = tmp_path / "feature.feature"
    data_path = tmp_path / "values.csv"
    values = ["", "comma, value", "pipe | value", r"slash\value", "first\nsecond"]
    with data_path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream, lineterminator="\r\n")
        writer.writerow(["empty", "comma", "pipe", "slash", "multiline"])
        writer.writerow(values)
    original_feature = _feature_source("Examples: table: values.csv\n")
    feature_path.write_text(original_feature, encoding="utf-8")
    original_data = data_path.read_bytes()

    feature = GherkinParser().parse(feature_path)
    assert feature.scenarios[0].examples[0].rows[0].values == tuple(values)
    assert feature_path.read_text(encoding="utf-8") == original_feature
    assert data_path.read_bytes() == original_data


def test_multiple_external_sections_keep_unique_rows_and_original_source_locations(tmp_path):
    feature_path = tmp_path / "feature.feature"
    first_path = tmp_path / "first.csv"
    second_path = tmp_path / "second.csv"
    first_path.write_text("value\nfirst\n", encoding="utf-8")
    second_path.write_text("value\nsecond\n", encoding="utf-8")
    content = (
        "Feature: External source map\n"
        "  Scenario Outline: Read source rows\n"
        "    Given the value is <value>\n"
        "    Examples: table: first.csv\n"
        "    Examples: table: second.csv\n"
        "  Scenario: After the outline\n"
        "    Given this step keeps its original line\n"
    )
    feature_path.write_text(content, encoding="utf-8")

    feature = GherkinParser().parse(feature_path)
    outline, following = feature.scenarios
    expected_following_line = content.splitlines().index("  Scenario: After the outline") + 1
    expected_following_step_line = content.splitlines().index("    Given this step keeps its original line") + 1

    assert outline.line == 2
    assert [example.external_source.section_index for example in outline.examples] == [1, 2]
    assert [example.external_source.path for example in outline.examples] == [
        str(first_path.resolve()),
        str(second_path.resolve()),
    ]
    assert [example.header.line for example in outline.examples] == [0, 0]
    assert [[row.line for row in example.rows] for example in outline.examples] == [[0], [0]]
    assert following.line == expected_following_line
    assert following.steps[0].line == expected_following_step_line

    expanded_rows = [
        scenario
        for _, scenario in ScenarioLocatorFilterMixin().filter_scenarios(feature)
        if scenario.external_example_source is not None
    ]
    assert len(expanded_rows) == 2
    assert len({scenario.id for scenario in expanded_rows}) == 2
    assert len({scenario.name for scenario in expanded_rows}) == 2
    assert [
        (
            scenario.external_example_source.section_index,
            scenario.external_example_source.row_index,
            scenario.external_example_source.source_line,
        )
        for scenario in expanded_rows
    ] == [(1, 1, 2), (2, 1, 2)]

    inline_path = tmp_path / "inline.feature"
    inline_path.write_text(
        "Feature: External source map\n"
        "  Scenario Outline: Read source rows\n"
        "    Given the value is <value>\n"
        "    Examples:\n"
        "      | value |\n"
        "      | first |\n"
        "    Examples:\n"
        "      | value  |\n"
        "      | second |\n"
        "  Scenario: After the outline\n"
        "    Given this step keeps its original line\n",
        encoding="utf-8",
    )
    inline_feature = GherkinParser().parse(inline_path)
    external_steps = sorted(tuple(step.name for step in scenario.steps) for scenario in expanded_rows)
    inline_steps = sorted(
        tuple(step.name for step in scenario.steps)
        for _, scenario in ScenarioLocatorFilterMixin().filter_scenarios(inline_feature)
        if scenario.name.startswith("Read source rows")
    )
    assert (
        external_steps
        == inline_steps
        == [
            ("the value is first",),
            ("the value is second",),
        ]
    )


@pytest.mark.parametrize(
    "source_bytes, expected_message",
    [
        (b"", "empty"),
        (b"name,\nAlice,1\n", "blank column"),
        (b"name,age\nAlice\n", "row 2 has 1 columns; expected 2"),
        (b"name\n\xff\n", "decode"),
    ],
)
def test_invalid_external_source_fails_with_feature_and_resolved_source(tmp_path, source_bytes, expected_message):
    feature_path = tmp_path / "feature.feature"
    data_path = tmp_path / "users.csv"
    data_path.write_bytes(source_bytes)
    feature_path.write_text(_feature_source("Examples: table: users.csv\n"), encoding="utf-8")

    with pytest.raises(FeatureConcreteParseError) as raised:
        GherkinParser().parse(feature_path)

    message = str(raised.value)
    assert expected_message in message.lower()
    assert str(feature_path.resolve()) in message
    assert str(data_path.resolve()) in message


def test_missing_external_source_is_actionable(tmp_path):
    feature_path = tmp_path / "feature.feature"
    missing_path = tmp_path / "missing.csv"
    feature_path.write_text(_feature_source("Examples: table: missing.csv\n"), encoding="utf-8")

    with pytest.raises(FeatureConcreteParseError) as raised:
        GherkinParser().parse(feature_path)

    assert "missing" in str(raised.value).lower()
    assert str(feature_path.resolve()) in str(raised.value)
    assert str(missing_path.resolve()) in str(raised.value)


def test_windows_relative_separator_resolves_from_feature_directory(tmp_path):
    feature_path = tmp_path / "feature.feature"
    data_path = tmp_path / "source data" / "users.csv"
    data_path.parent.mkdir()
    data_path.write_text("value\nwindows path\n", encoding="utf-8")
    feature_path.write_text(_feature_source(r"Examples: table: source data\users.csv" + "\n"), encoding="utf-8")

    assert _row_values(feature_path) == [("windows path",)]


def test_external_data_is_reloaded_for_every_parse(tmp_path):
    feature_path = tmp_path / "feature.feature"
    data_path = tmp_path / "users.csv"
    feature_path.write_text(_feature_source("Examples: table: users.csv\n"), encoding="utf-8")
    data_path.write_text("value\nfirst\n", encoding="utf-8")

    assert _row_values(feature_path) == [("first",)]
    data_path.write_text("value\nsecond\n", encoding="utf-8")
    assert _row_values(feature_path) == [("second",)]


def test_external_paths_are_resolved_without_changing_process_directory(tmp_path):
    elsewhere = tmp_path / "feature area" / "тест space"
    elsewhere.mkdir(parents=True)
    feature_path = elsewhere / "feature.feature"
    data_path = elsewhere / "данные users.csv"
    data_path.write_text("value\nunicode path\n", encoding="utf-8")
    feature_path.write_text(_feature_source(f"Examples: table: {data_path.as_posix()}\n"), encoding="utf-8")
    original_feature = feature_path.read_bytes()
    original_data = data_path.read_bytes()
    cwd = Path.cwd()

    assert _row_values(feature_path) == [("unicode path",)]
    assert Path.cwd() == cwd
    assert feature_path.read_bytes() == original_feature
    assert data_path.read_bytes() == original_data


@pytest.mark.skipif(os.name != "nt", reason="native Windows absolute paths require Windows")
def test_native_windows_absolute_external_path(tmp_path):
    feature_path = tmp_path / "feature.feature"
    data_path = tmp_path / "users.csv"
    data_path.write_text("value\nwindows absolute\n", encoding="utf-8")
    feature_path.write_text(_feature_source(f"Examples: table: {data_path}\n"), encoding="utf-8")

    assert _row_values(feature_path) == [("windows absolute",)]


def test_unreadable_external_source_names_both_paths(tmp_path, monkeypatch):
    feature_path = tmp_path / "feature.feature"
    data_path = tmp_path / "users.csv"
    data_path.write_text("value\nfirst\n", encoding="utf-8")
    feature_path.write_text(_feature_source("Examples: table: users.csv\n"), encoding="utf-8")
    original_open = Path.open

    def unreadable(path, *args, **kwargs):
        if path == data_path:
            raise PermissionError(os.fspath(path))
        return original_open(path, *args, **kwargs)

    monkeypatch.setattr(Path, "open", unreadable)
    with pytest.raises(FeatureConcreteParseError) as raised:
        GherkinParser().parse(feature_path)

    assert str(feature_path.resolve()) in str(raised.value)
    assert str(data_path.resolve()) in str(raised.value)
    assert "permission" in str(raised.value).lower()
