"""Load external Examples tables before a feature parser sees the source."""

from __future__ import annotations

import csv
import os
import re
from dataclasses import dataclass
from pathlib import Path, PureWindowsPath
from typing import TYPE_CHECKING

from attrs import evolve

from pytest_cuke.exceptions import FeatureConcreteParseError
from pytest_cuke.model import (
    Background,
    ExternalExamplesSource,
    Feature,
    Scenario,
    Step,
    TableRow,
    Tag,
)

if TYPE_CHECKING:
    from collections.abc import Sequence


_EXAMPLES_HEADING = re.compile(
    r"^(?P<prefix>\s*(?:#{1,6}[ \t]*)?Examples[ \t]*:[ \t]*)(?P<rest>.*?)\s*$",
    re.I,
)
_TABLE_MARKER = re.compile(r"^table[ \t]*:[ \t]*(?P<path>.+?)\s*$", re.I)


class _SourceFailure(Exception):
    """A source-specific error to report against the referencing feature."""


@dataclass(frozen=True)
class ExternalExamplesBinding:
    """A generated Examples heading and its original external source."""

    generated_examples_line: int
    source: ExternalExamplesSource


@dataclass(frozen=True)
class SourceLine:
    """Map a transformed physical line back to source, or to its marker."""

    original_line: int | None
    diagnostic_line: int


@dataclass(frozen=True)
class ExpandedFeatureText:
    """Expanded Gherkin text plus metadata that must survive model conversion."""

    content: str
    bindings: tuple[ExternalExamplesBinding, ...] = ()
    line_map: tuple[SourceLine, ...] = ()


def _line_parts(line: str) -> tuple[str, str]:
    if line.endswith("\r\n"):
        return line[:-2], "\r\n"
    if line.endswith(("\n", "\r")):
        return line[:-1], line[-1:]
    return line, ""


def _marker_path(value: str) -> str | None:
    candidate = value.strip()
    if candidate.startswith("|") and candidate.endswith("|"):
        cells = candidate[1:-1].split("|")
        if len(cells) != 1:
            return None
        candidate = cells[0].strip()
    if candidate.startswith("<") and candidate.endswith(">"):
        candidate = candidate[1:-1].strip()

    match = _TABLE_MARKER.fullmatch(candidate)
    if match is None:
        return None
    path = match.group("path").strip()
    if len(path) >= 2 and path[0] == path[-1] and path[0] in "'\"":
        path = path[1:-1]
    return path or None


def _resolve_windows_drive_path(raw_path: str, windows_path: PureWindowsPath) -> Path:
    if os.name == "nt":
        return Path(raw_path)
    if windows_path.drive.startswith("\\\\"):
        unc_root = windows_path.drive.strip("\\").replace("\\", "/")
        return Path("//") / unc_root / Path(*windows_path.parts[1:])
    drive = windows_path.drive.rstrip(":").lower()
    drive_root = Path("/mnt") / drive
    if not drive_root.is_dir():
        raise ValueError(f"Windows drive path {raw_path!r} cannot be resolved on this platform")
    return drive_root / Path(*windows_path.parts[1:])


def _resolve_external_path(feature_path: Path, raw_path: str) -> Path:
    """Resolve POSIX and Windows-style paths from the feature folder."""
    windows_path = PureWindowsPath(raw_path)
    if windows_path.drive:
        return _resolve_windows_drive_path(raw_path, windows_path)
    if windows_path.root:
        return Path(raw_path) if os.name == "nt" else Path("/") / Path(*windows_path.parts[1:])

    normalized = windows_path.as_posix() if "\\" in raw_path else raw_path
    candidate = Path(normalized)
    return candidate if candidate.is_absolute() else feature_path.resolve().parent / candidate


def _read_records(source_path: Path) -> tuple[list[list[str]], list[int]]:
    try:
        with source_path.open("r", encoding="utf-8-sig", newline="") as source_file:
            reader = csv.reader(source_file, delimiter="\t" if source_path.suffix.lower() in {".tsv", ".tab"} else ",")
            records: list[list[str]] = []
            physical_lines: list[int] = []
            previous_line = 0
            for record in reader:
                record_start_line = previous_line + 1
                previous_line = reader.line_num
                # csv.reader returns [] for a physically blank record. Keep an
                # intentional quoted empty value, which is a real CSV cell.
                if record:
                    records.append(record)
                    physical_lines.append(record_start_line)
    except (OSError, UnicodeError, csv.Error) as error:
        raise _SourceFailure(f"could not read source ({type(error).__name__}): {error}") from error

    if not records:
        raise _SourceFailure("source is empty (no non-blank CSV records)")

    headers = records[0]
    if not headers or any(not header.strip() for header in headers):
        raise _SourceFailure("header contains a blank column name")
    if len(records) == 1:
        raise _SourceFailure("source has a header but no data rows")
    for index, record in enumerate(records[1:], start=2):
        if len(record) != len(headers):
            raise _SourceFailure(f"row {index} has {len(record)} columns; expected {len(headers)}")
    return records, physical_lines


def _escape_cell(value: str) -> str:
    # Gherkin table cells support escaped backslashes, pipes, and line feeds.
    # CSV files may use CRLF or bare CR within a quoted field; normalize those
    # embedded line endings to the Gherkin-supported line-feed escape.
    normalized = value.replace("\r\n", "\n").replace("\r", "\n")
    return normalized.replace("\\", "\\\\").replace("|", "\\|").replace("\n", "\\n")


def _render_records(records: Sequence[Sequence[str]], indent: str, newline: str) -> str:
    rendered = []
    for record in records:
        rendered.append(f"{indent}| " + " | ".join(_escape_cell(value) for value in record) + f" |{newline}")
    return "".join(rendered)


def _format_source_error(
    error: Exception,
    source_path: Path | str,
    feature_path: Path,
    line_number: int,
    marker_line: str,
) -> FeatureConcreteParseError:
    source_label = source_path.resolve() if isinstance(source_path, Path) else source_path
    message = (
        f"External Examples source error: {error}. Referenced source: {source_label}; feature: {feature_path.resolve()}"
    )
    return FeatureConcreteParseError(message, line_number, marker_line.strip(), str(feature_path.resolve()))


def expand_external_examples(content: str, feature_path: Path) -> ExpandedFeatureText:
    """Replace supported external table markers with escaped Gherkin rows.

    The transformation is read-only and deliberately uncached. The same
    source text and feature path are consumed by the Gherkin and Markdown
    parsers, including explicit feature bindings and autoload collection.
    """
    lines = content.splitlines(keepends=True)
    if not lines:
        return ExpandedFeatureText(content)

    output: list[str] = []
    line_map: list[SourceLine] = []
    bindings: list[ExternalExamplesBinding] = []
    is_markdown = feature_path.name.lower().endswith((".md", ".markdown"))
    docstring_delimiter: str | None = None
    markdown_fence: tuple[str, int] | None = None

    def append_original(raw_line: str, source_line: int) -> None:
        output.append(raw_line)
        line_map.append(SourceLine(original_line=source_line, diagnostic_line=source_line))

    def append_generated(rendered: str, marker_line_number: int) -> None:
        output.append(rendered)
        generated_lines = rendered.splitlines(keepends=True)
        line_map.extend(SourceLine(original_line=None, diagnostic_line=marker_line_number) for _ in generated_lines)

    index = 0
    while index < len(lines):
        raw_line = lines[index]
        line_text, line_ending = _line_parts(raw_line)
        stripped = line_text.strip()
        if docstring_delimiter is not None:
            append_original(raw_line, index + 1)
            if stripped == docstring_delimiter:
                docstring_delimiter = None
            index += 1
            continue
        if markdown_fence is not None:
            append_original(raw_line, index + 1)
            fence_character, fence_length = markdown_fence
            closing_fence = re.match(r"^\s*(?P<fence>`+|~+)[ \t]*$", line_text)
            if (
                closing_fence is not None
                and closing_fence.group("fence")[0] == fence_character
                and len(closing_fence.group("fence")) >= fence_length
            ):
                markdown_fence = None
            index += 1
            continue

        # Marker text in Gherkin doc strings and Markdown fenced code examples
        # is literal content, not an external Examples declaration.
        docstring = re.match(r"^\s*(?P<delimiter>\"\"\"|''')(?:[^\r\n]*)$", line_text)
        if docstring is not None:
            append_original(raw_line, index + 1)
            docstring_delimiter = docstring.group("delimiter")
            index += 1
            continue
        if is_markdown:
            fence = re.match(r"^\s*(?P<fence>`{3,}|~{3,})(?:[^\r\n]*)$", line_text)
            if fence is not None:
                append_original(raw_line, index + 1)
                markdown_fence = (fence.group("fence")[0], len(fence.group("fence")))
                index += 1
                continue

        # Gherkin comments are comments even when their body starts with the
        # word Examples. Markdown headings remain eligible for Markdown Gherkin.
        if not is_markdown and line_text.lstrip().startswith("#"):
            append_original(raw_line, index + 1)
            index += 1
            continue

        heading = _EXAMPLES_HEADING.match(line_text)
        if heading is None:
            append_original(raw_line, index + 1)
            index += 1
            continue

        heading_indent_match = re.match(r"\s*", heading.group("prefix"))
        indent = heading_indent_match.group(0) if heading_indent_match else ""
        if is_markdown and not 2 <= len(indent) <= 5:
            # The Gherkin-in-Markdown matcher reserves unindented pipe rows
            # for ordinary Markdown tables.
            indent = "    "
        marker = _marker_path(heading.group("rest"))
        marker_line = line_text
        marker_index = index
        if marker is None:
            lookahead = index + 1
            while lookahead < len(lines) and not _line_parts(lines[lookahead])[0].strip():
                lookahead += 1
            if lookahead < len(lines):
                next_text, _ = _line_parts(lines[lookahead])
                marker = _marker_path(next_text.strip())
                if marker is not None:
                    marker_index = lookahead
                    marker_line = next_text

        if marker is None:
            append_original(raw_line, index + 1)
            index += 1
            continue

        try:
            source_path = _resolve_external_path(feature_path, marker)
        except (OSError, ValueError) as error:
            raise _format_source_error(error, marker, feature_path, marker_index + 1, marker_line) from error
        try:
            records, source_lines = _read_records(source_path)
        except _SourceFailure as error:
            raise _format_source_error(error, source_path, feature_path, marker_index + 1, marker_line) from error

        generated_examples_line = len(line_map) + 1
        bindings.append(
            ExternalExamplesBinding(
                generated_examples_line=generated_examples_line,
                source=ExternalExamplesSource(
                    path=str(source_path.resolve()),
                    marker_line=marker_index + 1,
                    section_index=len(bindings) + 1,
                    header_line=source_lines[0],
                    row_lines=tuple(source_lines[1:]),
                ),
            )
        )

        if marker_index == index:
            output.append(heading.group("prefix").rstrip() + (line_ending or "\n"))
            line_map.append(SourceLine(original_line=index + 1, diagnostic_line=index + 1))
            table_newline = line_ending or "\n"
            append_generated(_render_records(records, indent, table_newline), marker_index + 1)
            index += 1
        else:
            # Keep the Examples heading and intervening blank lines. Replace
            # only the one-cell marker row with the generated table.
            for original_index in range(index, marker_index):
                append_original(lines[original_index], original_index + 1)
            marker_text, marker_ending = _line_parts(lines[marker_index])
            marker_indent_match = re.match(r"\s*", marker_text)
            assert marker_indent_match is not None
            marker_indent = marker_indent_match.group(0)
            if is_markdown and not 2 <= len(marker_indent) <= 5:
                marker_indent = "    "
            append_generated(
                _render_records(records, marker_indent, marker_ending or line_ending or "\n"),
                marker_index + 1,
            )
            index = marker_index + 1

    return ExpandedFeatureText("".join(output), tuple(bindings), tuple(line_map))


def attach_external_examples_sources(feature: Feature, bindings: Sequence[ExternalExamplesBinding]) -> Feature:
    """Attach source provenance to immutable Examples nodes by generated heading line."""
    source_by_line = {binding.generated_examples_line: binding.source for binding in bindings}
    if not source_by_line:
        return feature

    def attach_scenario(scenario: Scenario) -> Scenario:
        examples = tuple(
            evolve(example, external_source=source_by_line[example.line]) if example.line in source_by_line else example
            for example in scenario.examples
        )
        return evolve(scenario, examples=examples)

    scenarios = tuple(attach_scenario(scenario) for scenario in feature.scenarios)
    rules = tuple(
        evolve(rule, scenarios=tuple(attach_scenario(scenario) for scenario in rule.scenarios))
        for rule in feature.rules
    )
    return evolve(feature, scenarios=scenarios, rules=rules)


def map_feature_source_lines(feature: Feature, line_map: Sequence[SourceLine]) -> Feature:
    """Restore original AST locations and mark generated Examples cells unknown."""

    def source_line(line: int) -> int:
        if 1 <= line <= len(line_map):
            return line_map[line - 1].original_line or 0
        return line

    def map_tag(tag: Tag) -> Tag:
        return evolve(tag, line=source_line(tag.line))

    def map_row(row: TableRow) -> TableRow:
        return evolve(
            row,
            line=source_line(row.line),
            cells=tuple(evolve(cell, line=source_line(cell.line)) for cell in row.cells),
        )

    def map_step(step: Step) -> Step:
        doc_string = step.doc_string
        if doc_string is not None:
            doc_string = evolve(doc_string, line=source_line(doc_string.line))
        data_table = step.data_table
        if data_table is not None:
            data_table = evolve(
                data_table,
                line=source_line(data_table.line),
                rows=tuple(map_row(row) for row in data_table.rows),
            )
        return evolve(step, line=source_line(step.line), doc_string=doc_string, data_table=data_table)

    def map_background(background: Background | None) -> Background | None:
        if background is None:
            return None
        return evolve(
            background,
            line=source_line(background.line),
            steps=tuple(map_step(step) for step in background.steps),
        )

    def map_scenario(scenario: Scenario) -> Scenario:
        examples = tuple(
            evolve(
                example,
                line=source_line(example.line),
                header=map_row(example.header) if example.header is not None else None,
                rows=tuple(map_row(row) for row in example.rows),
            )
            for example in scenario.examples
        )
        return evolve(
            scenario,
            line=source_line(scenario.line),
            tags=tuple(map_tag(tag) for tag in scenario.tags),
            steps=tuple(map_step(step) for step in scenario.steps),
            background=map_background(scenario.background),
            examples=examples,
        )

    scenarios = tuple(map_scenario(scenario) for scenario in feature.scenarios)
    rules = tuple(
        evolve(
            rule,
            line=source_line(rule.line),
            tags=tuple(map_tag(tag) for tag in rule.tags),
            background=map_background(rule.background),
            scenarios=tuple(map_scenario(scenario) for scenario in rule.scenarios),
        )
        for rule in feature.rules
    )
    return evolve(
        feature,
        line=source_line(feature.line),
        tags=tuple(map_tag(tag) for tag in feature.tags),
        background=map_background(feature.background),
        scenarios=scenarios,
        rules=rules,
    )


def remap_parse_error(error: FeatureConcreteParseError, expanded: ExpandedFeatureText, source: str, uri: str) -> None:
    """Raise a parse error at its original line, anchored to the marker if synthetic."""
    line = error.args[1] if len(error.args) > 1 and isinstance(error.args[1], int) else 0
    mapped = expanded.line_map[line - 1] if 1 <= line <= len(expanded.line_map) else None
    original_line = mapped.original_line if mapped is not None else line
    diagnostic_line = original_line or (mapped.diagnostic_line if mapped else line)
    original_lines = source.splitlines()
    line_text = original_lines[diagnostic_line - 1] if 1 <= diagnostic_line <= len(original_lines) else ""
    message = error.args[0] if error.args else str(error)
    raise FeatureConcreteParseError(message, diagnostic_line, line_text, uri) from error


__all__ = [
    "attach_external_examples_sources",
    "expand_external_examples",
    "map_feature_source_lines",
    "remap_parse_error",
]
