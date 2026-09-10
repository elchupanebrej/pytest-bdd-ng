"""
Resolve CSV and TSV files referenced by Gherkin Scenario Outline Examples.

Responsibility:
    Resolves feature-relative external Examples table references, validates CSV and TSV input, and renders the source
    rows back into the canonical Gherkin table syntax consumed by both parser implementations.

Reason for existence:
    External Examples support belongs at the text-ingestion boundary because the Gherkin parsers already own table
    semantics. Keeping file resolution and table rendering here gives the plain and batch parsers one deterministic
    implementation while keeping filesystem concerns out of the model and reporting layers.

Delegates:
    - `csv.reader`: Parses comma- and tab-delimited source files using the standard library.
    - `pathlib.Path`: Resolves paths relative to the feature file and performs safe file reads.
    - `pytest_bdd.parser` and `pytest_bdd.collector_batch`: Invoke expansion before parsing.

Cohesion:
    Every helper in this module contributes to one pipeline: detect an Examples marker, resolve its source, validate
    rows, escape cell content, and replace the marker with Gherkin rows. No parser or reporting state is maintained.

Separation:
    - `pytest_bdd.parser`: Owns Gherkin syntax parsing; this module only prepares source text.
    - `pytest_bdd.model`: Owns runtime domain objects and must not be imported by the parsing layer.
    - `pytest_bdd.collector_batch`: Owns batching and error propagation; this module owns table expansion.

Main consumers:
    - `GherkinParser` and `MarkdownGherkinParser`: Expand ordinary and Markdown feature files.
    - `FeatureBatchParser`: Expands files before the Go parser or Python fallback consumes them.
    - Feature authors: Reference CSV or TSV fixtures relative to the feature file.

State and side effects:
    The public expansion function is deterministic for a given feature path and text. It performs read-only source-file
    I/O through `_read_rows`; it does not mutate the feature file or retain process-global state.

Invariants:
    - A source must contain a non-empty header and every data row must have the same column count.
    - Relative source paths are resolved from the containing feature directory.
    - Generated rows preserve marker indentation and escape Gherkin-sensitive cell characters.

Architecture score:
    #arch-eval:reason_for_existence=5
    #arch-eval:owned_responsibility=5
    #arch-eval:delegation_boundary=5
    #arch-eval:cohesion=5
    #arch-eval:separation=5
    #arch-eval:consumer_clarity=5
    #arch-eval:state_invariants=5
    #arch-eval:entity_fullness=4
    #arch-eval:locational_stability=5
"""

# The small parsing helpers intentionally stay below the repository's documentation threshold; the module contract
# above is the relevant architectural boundary for this private text transformation pipeline.
# pylint: disable=missing-responsibility-doc,missing-architecture-score
from __future__ import annotations

import csv
import re
from pathlib import Path


class ExternalExamplesError(Exception):
    """Report an invalid or unavailable external Examples table source."""


_EXAMPLES_LINE = re.compile(r"^(?P<indent>\s*)(?P<markdown>#{1,6}\s*)?Examples\s*:", re.IGNORECASE)
_SOURCE_VALUE = re.compile(r"^(?:table:\s*(?P<table>.+)|<table:\s*(?P<bracket>[^>]+)>)$", re.IGNORECASE)


def _source_path(value: str, feature_path: Path) -> Path | None:
    """Return the feature-relative source path encoded in an Examples marker."""
    candidate = value.strip()
    if candidate.startswith("|") and candidate.endswith("|"):
        cells = [cell.strip() for cell in candidate[1:-1].split("|")]
        if len(cells) != 1:
            return None
        candidate = cells[0]
    match = _SOURCE_VALUE.fullmatch(candidate)
    if match is None:
        return None
    source = (match.group("table") or match.group("bracket") or "").strip()
    if not source:
        message = "External Examples source path cannot be empty"
        raise ExternalExamplesError(message)
    source_path = Path(source).expanduser()
    if not source_path.is_absolute():
        source_path = feature_path.parent / source_path
    return source_path


def _read_rows(source_path: Path) -> list[list[str]]:
    """Read and validate a CSV or TSV Examples source."""
    if not source_path.is_file():
        message = f"External Examples table does not exist: {source_path}"
        raise ExternalExamplesError(message)
    delimiter = "\t" if source_path.suffix.lower() in {".tsv", ".tab"} else ","
    try:
        with source_path.open(encoding="utf-8-sig", newline="") as source_file:
            rows = [row for row in csv.reader(source_file, delimiter=delimiter) if row]
    except OSError as exc:
        message = f"Cannot read external Examples table: {source_path}"
        raise ExternalExamplesError(message) from exc
    if not rows:
        message = f"External Examples table is empty: {source_path}"
        raise ExternalExamplesError(message)
    header = rows[0]
    if not header or any(not cell.strip() for cell in header):
        message = f"External Examples table has an invalid header: {source_path}"
        raise ExternalExamplesError(message)
    width = len(header)
    if any(len(row) != width for row in rows[1:]):
        message = f"External Examples table has inconsistent columns: {source_path}"
        raise ExternalExamplesError(message)
    return rows


def _escape_cell(value: str) -> str:
    """Escape a CSV or TSV cell for insertion into a Gherkin table."""
    return value.replace("\\", "\\\\").replace("|", "\\|").replace("\n", "\\n").replace("\r", "\\r")


def _render_rows(rows: list[list[str]], indent: str, newline: str = "\n") -> list[str]:
    """Render validated source rows with the marker's indentation."""
    return [f"{indent}| {' | '.join(_escape_cell(cell) for cell in row)} |{newline}" for row in rows]


def _find_source(lines: list[str], index: int, feature_path: Path) -> tuple[Path | None, int, bool]:
    """Find an inline or one-cell external source following an Examples heading."""
    line = lines[index]
    examples_match = _EXAMPLES_LINE.match(line)
    if examples_match is None:
        return (None, index, False)
    line_body = line.rstrip("\r\n")
    source_value = line_body[examples_match.end() :].strip()
    source_path = _source_path(source_value, feature_path) if source_value else None
    marker_index = index + 1
    if source_path is None:
        while marker_index < len(lines) and not lines[marker_index].strip():
            marker_index += 1
        if marker_index < len(lines):
            marker_value = lines[marker_index].strip()
            if marker_value.startswith("|") and marker_value.endswith("|"):
                cells = [cell.strip() for cell in marker_value[1:-1].split("|")]
                if len(cells) == 1:
                    source_path = _source_path(cells[0], feature_path)
    return (source_path, marker_index, bool(source_value))


def expand_external_examples(text: str, feature_path: Path) -> str:
    """Replace external Examples markers with rows loaded from CSV or TSV."""
    lines = text.splitlines(keepends=True)
    expanded: list[str] = []
    index = 0
    while index < len(lines):
        line = lines[index]
        examples_match = _EXAMPLES_LINE.match(line)
        if examples_match is None:
            expanded.append(line)
            index += 1
            continue

        source_path, marker_index, inline_source = _find_source(lines, index, feature_path)
        if source_path is None:
            expanded.append(line)
            index += 1
            continue

        rows = _read_rows(source_path)
        marker_line = lines[marker_index] if marker_index < len(lines) else line
        indent_match = re.match(r"^\s*", marker_line)
        indent = indent_match.group(0) if indent_match is not None else ""
        newline = "\r\n" if marker_line.endswith("\r\n") else "\n"
        if inline_source:
            line_body = line.rstrip("\r\n")
            expanded.append(line[: examples_match.end()] + line[len(line_body) :])
            expanded.extend(_render_rows(rows, examples_match.group("indent"), newline))
        else:
            expanded.append(line)
            expanded.extend(lines[index + 1 : marker_index])
            expanded.extend(_render_rows(rows, indent, newline))
            index = marker_index
        index += 1
    return "".join(expanded)
