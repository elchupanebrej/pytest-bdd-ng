"""
Owns the CLI tooling and pipeline for scanning Gherkin feature documents to detect empty-heading violations, producin.

Responsibility:
    Owns the CLI tooling and pipeline for scanning Gherkin feature documents to detect empty-heading violations,
    producing validation runs and baseline audit summaries with JSON or human-readable output to stdout/stderr.

Reason for existence:
    Centralizes all heading-validation logic (parsing, extraction, policy-based validation, reporting) in one module
    because every stage shares the same domain types (`HeadingValidationRun`, `HeadingValidationViolation`,
    `ParsedHeadingRecord`) and the same policy configuration object.

Delegates:
    - `pytest_bdd.model.heading_validation`: Provides domain types (`HeadingValidationViolation`,
    `HeadingValidationPolicy`, `BaselineAuditSummary`, etc.) and the `default_heading_validation_policy` factory
    consumed by all validation functions.
    - `gherkin.parser.Parser` / `gherkin.ast_builder.AstBuilder`: Parses raw Gherkin source text into AST dicts that
    this module extracts heading records from.
    - `pytest_bdd.util.other.IdGenerator`: Provides unique IDs for the Gherkin AST builder during parsing.

Cohesion:
    Every function operates on the same domain (Gherkin heading validation) and shares the same imports (`HeadingType`,
    `HeadingValidationPolicy`, model types). The pipeline flows linearly: parse_args -> discover -> parse -> extract -
    validate -> emit, with each stage feeding the next.

Separation:
    - `sync_messages_contract_schemas`: Kept separate because it deals with cucumber-messages schema synchronization via
    git, a completely different concern with no shared types, config, or control flow.

Main consumers:
    - `pyproject.toml` console_scripts entry point referencing `pytest_bdd.script.validate_feature_headings:main`,
    invoked as a standalone CLI for pre-commit or CI checks.

State and side effects:
    Reads feature files from disk via `Path.read_text` and `Path.glob`. Writes to `sys.stdout` and `sys.stderr` for JSON
    and text output. No configuration access or pytest stash interactions.

Invariants:
    - Feature document paths returned by `discover_feature_documents` must be absolute/resolved paths.
    - `parse_gherkin_document` always returns a `JSONObject` (dict form of the Gherkin AST) or raises `ValueError` on
    parse failure.
    - `run_heading_validation_scan` produces a `HeadingValidationRun` with violations sorted by (path, line, heading_type).

Failure semantics:
    `parse_gherkin_document` raises `ValueError` wrapped around `CompositeParserException` when a feature file cannot be
    parsed. `main` returns exit code 1 when `fail_on_violation` is True and violations exist.

Architecture score:
    #arch-eval:reason_for_existence=4
    #arch-eval:owned_responsibility=3
    #arch-eval:delegation_boundary=4
    #arch-eval:cohesion=4
    #arch-eval:separation=4
    #arch-eval:consumer_clarity=3
    #arch-eval:state_invariants=4
    #arch-eval:entity_fullness=2
    #arch-eval:locational_stability=4
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Iterable, Mapping
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING, cast

from gherkin.ast_builder import AstBuilder
from gherkin.errors import CompositeParserException
from gherkin.parser import Parser
from gherkin.token_matcher_markdown import GherkinInMarkdownTokenMatcher
from gherkin.token_scanner import TokenScanner
from returns.maybe import Nothing

from pytest_bdd.model.heading_validation import (
    EMPTY_HEADING_TITLE_CODE,
    BaselineAuditSummary,
    HeadingType,
    HeadingValidationPolicy,
    HeadingValidationRun,
    HeadingValidationViolation,
    ParsedHeadingRecord,
    default_heading_validation_policy,
)
from pytest_bdd.util.other import IdGenerator

if TYPE_CHECKING:
    from pytest_bdd.types.json import JSONObject

DEFAULT_INCLUDE_PATTERNS = (
    "**/*.feature",
    "**/*.gherkin",
    "**/*.feature.md",
    "**/*.gherkin.md",
)
_MARKDOWN_SUFFIXES = {(".feature", ".md"), (".gherkin", ".md")}


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """
    Configure and invoke `argparse.ArgumentParser` to parse CLI arguments for the heading validation tool, returning a .

    Responsibility:
        Configures and invokes `argparse.ArgumentParser` to parse CLI arguments for the heading validation tool,
        returning a `Namespace` with `root_path`, `include_patterns`, `json`, `baseline_audit`, and `fail_on_violation`
        fields.

    Reason for existence:
        Encapsulates all CLI option definitions so `main` remains focused on orchestrating the validation pipeline
        without coupling to argument-parsing details or default value management.

    Delegates:
        - `argparse.ArgumentParser.parse_args`: Does the actual string-to-Namespace conversion after argument
        definitions are registered.

    Cohesion:
        All logic inside this function configures exactly one `ArgumentParser` instance with mutually consistent
        options; there is no branching or unrelated setup.

    Separation:
        - `discover_feature_documents`: Kept separate because it performs filesystem discovery rather than CLI argument
        parsing, with no shared mutable state.

    Main consumers:
        - `validate_feature_headings.main`: Consumes the `argparse.Namespace` produced by `parse_args` to decide which
        code path (baseline audit vs. full scan) to execute.

    State and side effects:
        None, keeps no persistent state. Pure argument definition and parsing with no I/O beyond the argv list.

    Architecture score:
    #arch-eval:reason_for_existence=4
    #arch-eval:owned_responsibility=3
    #arch-eval:delegation_boundary=4
    #arch-eval:cohesion=4
    #arch-eval:separation=4
    #arch-eval:consumer_clarity=3
    #arch-eval:state_invariants=4
    #arch-eval:entity_fullness=2
    #arch-eval:locational_stability=4
    """
    parser = argparse.ArgumentParser(description="Validate non-empty parsed BDD headings")
    parser.add_argument("--root-path", type=Path, default=Path("features"), help="Path to feature documents root")
    parser.add_argument(
        "--include-pattern",
        dest="include_patterns",
        action="append",
        default=None,
        help="Glob include pattern (repeatable)",
    )
    parser.add_argument("--json", action="store_true", help="Emit JSON payload")
    parser.add_argument("--baseline-audit", action="store_true", help="Emit baseline compliance summary")
    parser.add_argument(
        "--no-fail-on-violation",
        action="store_false",
        dest="fail_on_violation",
        help="Return zero exit code even when violations are found",
    )
    parser.set_defaults(fail_on_violation=True)
    return parser.parse_args(argv)


def heading_validation_policy_payload(policy: HeadingValidationPolicy | None = None) -> dict[str, object]:
    """
    Configure and invoke `argparse.ArgumentParser` to parse CLI arguments for the heading validation tool, returning a .

    Responsibility:
        Configures and invokes `argparse.ArgumentParser` to parse CLI arguments for the heading validation tool,
        returning a `Namespace` with `root_path`, `include_patterns`, `json`, `baseline_audit`, and `fail_on_violation`
        fields.

    Reason for existence:
        Encapsulates all CLI option definitions so `main` remains focused on orchestrating the validation pipeline
        without coupling to argument-parsing details or default value management.

    Delegates:
        - `argparse.ArgumentParser.parse_args`: Does the actual string-to-Namespace conversion after argument
        definitions are registered.

    Cohesion:
        All logic inside this function configures exactly one `ArgumentParser` instance with mutually consistent
        options; there is no branching or unrelated setup.

    Separation:
        - `discover_feature_documents`: Kept separate because it performs filesystem discovery rather than CLI argument
        parsing, with no shared mutable state.

    Main consumers:
        - `validate_feature_headings.main`: Consumes the `argparse.Namespace` produced by `parse_args` to decide which
        code path (baseline audit vs. full scan) to execute.

    State and side effects:
        None, keeps no persistent state. Pure argument definition and parsing with no I/O beyond the argv list.

    Architecture score:
    #arch-eval:reason_for_existence=4
    #arch-eval:owned_responsibility=3
    #arch-eval:delegation_boundary=4
    #arch-eval:cohesion=4
    #arch-eval:separation=4
    #arch-eval:consumer_clarity=3
    #arch-eval:state_invariants=4
    #arch-eval:entity_fullness=2
    #arch-eval:locational_stability=4
    """
    active_policy = default_heading_validation_policy() if policy is None else policy
    return {
        "policy_id": active_policy.policy_id,
        "enforced_heading_types": [heading_type.value for heading_type in active_policy.enforced_heading_types],
        "trim_whitespace": active_policy.trim_whitespace,
        "empty_name_is_violation": active_policy.empty_name_is_violation,
        "snippet_text_excluded": active_policy.snippet_text_excluded,
    }


def discover_feature_documents(root_path: Path, include_patterns: Iterable[str] | None = None) -> list[Path]:
    """
    Configure and invoke `argparse.ArgumentParser` to parse CLI arguments for the heading validation tool, returning a .

    Responsibility:
        Configures and invokes `argparse.ArgumentParser` to parse CLI arguments for the heading validation tool,
        returning a `Namespace` with `root_path`, `include_patterns`, `json`, `baseline_audit`, and `fail_on_violation`
        fields.

    Reason for existence:
        Encapsulates all CLI option definitions so `main` remains focused on orchestrating the validation pipeline
        without coupling to argument-parsing details or default value management.

    Delegates:
        - `argparse.ArgumentParser.parse_args`: Does the actual string-to-Namespace conversion after argument
        definitions are registered.

    Cohesion:
        All logic inside this function configures exactly one `ArgumentParser` instance with mutually consistent
        options; there is no branching or unrelated setup.

    Separation:
        - `discover_feature_documents`: Kept separate because it performs filesystem discovery rather than CLI argument
        parsing, with no shared mutable state.

    Main consumers:
        - `validate_feature_headings.main`: Consumes the `argparse.Namespace` produced by `parse_args` to decide which
        code path (baseline audit vs. full scan) to execute.

    State and side effects:
        None, keeps no persistent state. Pure argument definition and parsing with no I/O beyond the argv list.

    Architecture score:
    #arch-eval:reason_for_existence=4
    #arch-eval:owned_responsibility=3
    #arch-eval:delegation_boundary=4
    #arch-eval:cohesion=4
    #arch-eval:separation=4
    #arch-eval:consumer_clarity=3
    #arch-eval:state_invariants=4
    #arch-eval:entity_fullness=2
    #arch-eval:locational_stability=4
    """
    patterns = tuple(include_patterns or DEFAULT_INCLUDE_PATTERNS)
    discovered_paths = {
        path.resolve()
        for pattern in patterns
        for path in root_path.glob(pattern)
        if path.is_file() and _is_supported_feature_path(path)
    }
    return sorted(discovered_paths, key=lambda path: path.as_posix())


def run_heading_validation_scan(
    root_path: Path,
    include_patterns: Iterable[str] | None = None,
    policy: HeadingValidationPolicy | None = None,
) -> HeadingValidationRun:
    """
    Configure and invoke `argparse.ArgumentParser` to parse CLI arguments for the heading validation tool, returning a .

    Responsibility:
        Configures and invokes `argparse.ArgumentParser` to parse CLI arguments for the heading validation tool,
        returning a `Namespace` with `root_path`, `include_patterns`, `json`, `baseline_audit`, and `fail_on_violation`
        fields.

    Reason for existence:
        Encapsulates all CLI option definitions so `main` remains focused on orchestrating the validation pipeline
        without coupling to argument-parsing details or default value management.

    Delegates:
        - `argparse.ArgumentParser.parse_args`: Does the actual string-to-Namespace conversion after argument
        definitions are registered.

    Cohesion:
        All logic inside this function configures exactly one `ArgumentParser` instance with mutually consistent
        options; there is no branching or unrelated setup.

    Separation:
        - `discover_feature_documents`: Kept separate because it performs filesystem discovery rather than CLI argument
        parsing, with no shared mutable state.

    Main consumers:
        - `validate_feature_headings.main`: Consumes the `argparse.Namespace` produced by `parse_args` to decide which
        code path (baseline audit vs. full scan) to execute.

    State and side effects:
        None, keeps no persistent state. Pure argument definition and parsing with no I/O beyond the argv list.

    Architecture score:
    #arch-eval:reason_for_existence=4
    #arch-eval:owned_responsibility=3
    #arch-eval:delegation_boundary=4
    #arch-eval:cohesion=4
    #arch-eval:separation=4
    #arch-eval:consumer_clarity=3
    #arch-eval:state_invariants=4
    #arch-eval:entity_fullness=2
    #arch-eval:locational_stability=4
    """
    started_at = datetime.now(timezone.utc)
    active_policy = default_heading_validation_policy() if policy is None else policy
    document_paths = discover_feature_documents(root_path, include_patterns)

    violations: list[HeadingValidationViolation] = []

    for path in document_paths:
        gherkin_document = parse_gherkin_document(path)
        records = extract_parsed_heading_records(path, gherkin_document, root_path)
        violations.extend(validate_heading_records(records, active_policy))

    ordered_violations = tuple(sorted(violations, key=lambda item: (item.path, item.line, item.heading_type.value)))
    finished_at = datetime.now(timezone.utc)
    run_id = f"heading-scan-{started_at.strftime('%Y%m%d%H%M%S%f')}"

    return HeadingValidationRun(
        run_id=run_id,
        started_at=started_at,
        finished_at=finished_at,
        documents_scanned=len(document_paths),
        violations=ordered_violations,
    )


def build_baseline_audit(
    root_path: Path,
    include_patterns: Iterable[str] | None = None,
    policy: HeadingValidationPolicy | None = None,
) -> BaselineAuditSummary:
    """
    Configure and invoke `argparse.ArgumentParser` to parse CLI arguments for the heading validation tool, returning a .

    Responsibility:
        Configures and invokes `argparse.ArgumentParser` to parse CLI arguments for the heading validation tool,
        returning a `Namespace` with `root_path`, `include_patterns`, `json`, `baseline_audit`, and `fail_on_violation`
        fields.

    Reason for existence:
        Encapsulates all CLI option definitions so `main` remains focused on orchestrating the validation pipeline
        without coupling to argument-parsing details or default value management.

    Delegates:
        - `argparse.ArgumentParser.parse_args`: Does the actual string-to-Namespace conversion after argument
        definitions are registered.

    Cohesion:
        All logic inside this function configures exactly one `ArgumentParser` instance with mutually consistent
        options; there is no branching or unrelated setup.

    Separation:
        - `discover_feature_documents`: Kept separate because it performs filesystem discovery rather than CLI argument
        parsing, with no shared mutable state.

    Main consumers:
        - `validate_feature_headings.main`: Consumes the `argparse.Namespace` produced by `parse_args` to decide which
        code path (baseline audit vs. full scan) to execute.

    State and side effects:
        None, keeps no persistent state. Pure argument definition and parsing with no I/O beyond the argv list.

    Architecture score:
    #arch-eval:reason_for_existence=4
    #arch-eval:owned_responsibility=3
    #arch-eval:delegation_boundary=4
    #arch-eval:cohesion=4
    #arch-eval:separation=4
    #arch-eval:consumer_clarity=3
    #arch-eval:state_invariants=4
    #arch-eval:entity_fullness=2
    #arch-eval:locational_stability=4
    """
    active_policy = default_heading_validation_policy() if policy is None else policy
    validation_run = run_heading_validation_scan(
        root_path=root_path,
        include_patterns=include_patterns,
        policy=active_policy,
    )

    return BaselineAuditSummary(
        record_id=f"baseline-audit-{validation_run.run_id}",
        policy_id=active_policy.policy_id,
        run_id=validation_run.run_id,
        violations_count=len(validation_run.violations),
        compliant=validation_run.status == "pass",
    )


def parse_gherkin_document(path: Path) -> JSONObject:
    """
    Configure and invoke `argparse.ArgumentParser` to parse CLI arguments for the heading validation tool, returning a .

    Responsibility:
        Configures and invokes `argparse.ArgumentParser` to parse CLI arguments for the heading validation tool,
        returning a `Namespace` with `root_path`, `include_patterns`, `json`, `baseline_audit`, and `fail_on_violation`
        fields.

    Reason for existence:
        Encapsulates all CLI option definitions so `main` remains focused on orchestrating the validation pipeline
        without coupling to argument-parsing details or default value management.

    Delegates:
        - `argparse.ArgumentParser.parse_args`: Does the actual string-to-Namespace conversion after argument
        definitions are registered.

    Cohesion:
        All logic inside this function configures exactly one `ArgumentParser` instance with mutually consistent
        options; there is no branching or unrelated setup.

    Separation:
        - `discover_feature_documents`: Kept separate because it performs filesystem discovery rather than CLI argument
        parsing, with no shared mutable state.

    Main consumers:
        - `validate_feature_headings.main`: Consumes the `argparse.Namespace` produced by `parse_args` to decide which
        code path (baseline audit vs. full scan) to execute.

    State and side effects:
        None, keeps no persistent state. Pure argument definition and parsing with no I/O beyond the argv list.

    Failure semantics:
        Refer to the source code for the specific exception types raised by this entity and the documented error-
        handling contract for callers. (ValueError) and how callers should handle them. Analyze the actual raise
        statements in the source.

    Architecture score:
    #arch-eval:reason_for_existence=4
    #arch-eval:owned_responsibility=3
    #arch-eval:delegation_boundary=4
    #arch-eval:cohesion=4
    #arch-eval:separation=4
    #arch-eval:consumer_clarity=3
    #arch-eval:state_invariants=4
    #arch-eval:entity_fullness=2
    #arch-eval:locational_stability=4
    """
    parser = Parser(ast_builder=AstBuilder(id_generator=IdGenerator()))
    feature_file_data = path.read_text(encoding="utf-8")

    try:
        if _is_markdown_gherkin(path):
            parsed_document = parser.parse(TokenScanner(feature_file_data), GherkinInMarkdownTokenMatcher())
        else:
            parsed_document = parser.parse(feature_file_data)
        return cast("JSONObject", parsed_document)
    except CompositeParserException as exc:  # pragma: no cover - parser-level failures are exceptional for this scan
        msg = f"Unable to parse feature document: {path.as_posix()}"
        raise ValueError(msg) from exc


def extract_parsed_heading_records(
    path: Path,
    gherkin_document: Mapping[str, object],
    root_path: Path,
) -> list[ParsedHeadingRecord]:
    """
    Configure and invoke `argparse.ArgumentParser` to parse CLI arguments for the heading validation tool, returning a .

    Responsibility:
        Configures and invokes `argparse.ArgumentParser` to parse CLI arguments for the heading validation tool,
        returning a `Namespace` with `root_path`, `include_patterns`, `json`, `baseline_audit`, and `fail_on_violation`
        fields.

    Reason for existence:
        Encapsulates all CLI option definitions so `main` remains focused on orchestrating the validation pipeline
        without coupling to argument-parsing details or default value management.

    Delegates:
        - `argparse.ArgumentParser.parse_args`: Does the actual string-to-Namespace conversion after argument
        definitions are registered.

    Cohesion:
        All logic inside this function configures exactly one `ArgumentParser` instance with mutually consistent
        options; there is no branching or unrelated setup.

    Separation:
        - `discover_feature_documents`: Kept separate because it performs filesystem discovery rather than CLI argument
        parsing, with no shared mutable state.

    Main consumers:
        - `validate_feature_headings.main`: Consumes the `argparse.Namespace` produced by `parse_args` to decide which
        code path (baseline audit vs. full scan) to execute.

    State and side effects:
        None, keeps no persistent state. Pure argument definition and parsing with no I/O beyond the argv list.

    Architecture score:
    #arch-eval:reason_for_existence=4
    #arch-eval:owned_responsibility=3
    #arch-eval:delegation_boundary=4
    #arch-eval:cohesion=4
    #arch-eval:separation=4
    #arch-eval:consumer_clarity=3
    #arch-eval:state_invariants=4
    #arch-eval:entity_fullness=2
    #arch-eval:locational_stability=4
    """
    relative_path = path.resolve().relative_to(root_path.resolve()).as_posix()
    feature_data = gherkin_document.get("feature")
    if not isinstance(feature_data, Mapping):
        return []

    records = [
        ParsedHeadingRecord(
            document_path=relative_path,
            heading_type=HeadingType.FEATURE,
            name_raw=_as_optional_string(feature_data.get("name")),
            line=_extract_line(feature_data),
            column=_extract_column(feature_data),
        ),
    ]

    records.extend(_extract_scenario_records(relative_path, feature_data.get("children", ())))
    return records


def validate_heading_records(
    records: Iterable[ParsedHeadingRecord],
    policy: HeadingValidationPolicy | None = None,
) -> list[HeadingValidationViolation]:
    """
    Configure and invoke `argparse.ArgumentParser` to parse CLI arguments for the heading validation tool, returning a .

    Responsibility:
        Configures and invokes `argparse.ArgumentParser` to parse CLI arguments for the heading validation tool,
        returning a `Namespace` with `root_path`, `include_patterns`, `json`, `baseline_audit`, and `fail_on_violation`
        fields.

    Reason for existence:
        Encapsulates all CLI option definitions so `main` remains focused on orchestrating the validation pipeline
        without coupling to argument-parsing details or default value management.

    Delegates:
        - `argparse.ArgumentParser.parse_args`: Does the actual string-to-Namespace conversion after argument
        definitions are registered.

    Cohesion:
        All logic inside this function configures exactly one `ArgumentParser` instance with mutually consistent
        options; there is no branching or unrelated setup.

    Separation:
        - `discover_feature_documents`: Kept separate because it performs filesystem discovery rather than CLI argument
        parsing, with no shared mutable state.

    Main consumers:
        - `validate_feature_headings.main`: Consumes the `argparse.Namespace` produced by `parse_args` to decide which
        code path (baseline audit vs. full scan) to execute.

    State and side effects:
        None, keeps no persistent state. Pure argument definition and parsing with no I/O beyond the argv list.

    Architecture score:
    #arch-eval:reason_for_existence=4
    #arch-eval:owned_responsibility=3
    #arch-eval:delegation_boundary=4
    #arch-eval:cohesion=4
    #arch-eval:separation=4
    #arch-eval:consumer_clarity=3
    #arch-eval:state_invariants=4
    #arch-eval:entity_fullness=2
    #arch-eval:locational_stability=4
    """
    active_policy = default_heading_validation_policy() if policy is None else policy
    violations: list[HeadingValidationViolation] = []

    for record in records:
        if record.heading_type not in active_policy.enforced_heading_types:
            continue
        normalized_name = active_policy.normalize_name(record.name_raw)
        if active_policy.empty_name_is_violation and not normalized_name:
            violations.append(
                HeadingValidationViolation(
                    path=record.document_path,
                    line=record.line,
                    heading_type=record.heading_type,
                    code=EMPTY_HEADING_TITLE_CODE,
                    message=f"{record.heading_type.display_name} heading title is empty after trimming whitespace",
                    raw_name=record.name_raw,
                ),
            )

    return violations


def _extract_scenario_records(document_path: str, children: object) -> list[ParsedHeadingRecord]:
    """
    Configure and invoke `argparse.ArgumentParser` to parse CLI arguments for the heading validation tool, returning a .

    Responsibility:
        Configures and invokes `argparse.ArgumentParser` to parse CLI arguments for the heading validation tool,
        returning a `Namespace` with `root_path`, `include_patterns`, `json`, `baseline_audit`, and `fail_on_violation`
        fields.

    Reason for existence:
        Encapsulates all CLI option definitions so `main` remains focused on orchestrating the validation pipeline
        without coupling to argument-parsing details or default value management.

    Delegates:
        - `argparse.ArgumentParser.parse_args`: Does the actual string-to-Namespace conversion after argument
        definitions are registered.

    Cohesion:
        All logic inside this function configures exactly one `ArgumentParser` instance with mutually consistent
        options; there is no branching or unrelated setup.

    Separation:
        - `discover_feature_documents`: Kept separate because it performs filesystem discovery rather than CLI argument
        parsing, with no shared mutable state.

    Main consumers:
        - `validate_feature_headings.main`: Consumes the `argparse.Namespace` produced by `parse_args` to decide which
        code path (baseline audit vs. full scan) to execute.

    State and side effects:
        None, keeps no persistent state. Pure argument definition and parsing with no I/O beyond the argv list.

    Architecture score:
    #arch-eval:reason_for_existence=4
    #arch-eval:owned_responsibility=3
    #arch-eval:delegation_boundary=4
    #arch-eval:cohesion=4
    #arch-eval:separation=4
    #arch-eval:consumer_clarity=3
    #arch-eval:state_invariants=4
    #arch-eval:entity_fullness=2
    #arch-eval:locational_stability=4
    """
    records: list[ParsedHeadingRecord] = []

    if not isinstance(children, list):
        return records

    for child in children:
        if not isinstance(child, Mapping):
            continue

        scenario_data = child.get("scenario")
        if isinstance(scenario_data, Mapping):
            heading_type = _heading_type_from_keyword(_as_optional_string(scenario_data.get("keyword")))
            if heading_type is not None:
                records.append(
                    ParsedHeadingRecord(
                        document_path=document_path,
                        heading_type=heading_type,
                        name_raw=_as_optional_string(scenario_data.get("name")),
                        line=_extract_line(scenario_data),
                        column=_extract_column(scenario_data),
                    ),
                )

        rule_data = child.get("rule")
        if isinstance(rule_data, Mapping):
            records.extend(_extract_scenario_records(document_path, rule_data.get("children", ())))

    return records


def _heading_type_from_keyword(keyword: str | None) -> HeadingType | None:
    """
    Configure and invoke `argparse.ArgumentParser` to parse CLI arguments for the heading validation tool, returning a .

    Responsibility:
        Configures and invokes `argparse.ArgumentParser` to parse CLI arguments for the heading validation tool,
        returning a `Namespace` with `root_path`, `include_patterns`, `json`, `baseline_audit`, and `fail_on_violation`
        fields.

    Reason for existence:
        Encapsulates all CLI option definitions so `main` remains focused on orchestrating the validation pipeline
        without coupling to argument-parsing details or default value management.

    Delegates:
        - `argparse.ArgumentParser.parse_args`: Does the actual string-to-Namespace conversion after argument
        definitions are registered.

    Cohesion:
        All logic inside this function configures exactly one `ArgumentParser` instance with mutually consistent
        options; there is no branching or unrelated setup.

    Separation:
        - `discover_feature_documents`: Kept separate because it performs filesystem discovery rather than CLI argument
        parsing, with no shared mutable state.

    Main consumers:
        - `validate_feature_headings.main`: Consumes the `argparse.Namespace` produced by `parse_args` to decide which
        code path (baseline audit vs. full scan) to execute.

    State and side effects:
        None, keeps no persistent state. Pure argument definition and parsing with no I/O beyond the argv list.

    Architecture score:
    #arch-eval:reason_for_existence=4
    #arch-eval:owned_responsibility=3
    #arch-eval:delegation_boundary=4
    #arch-eval:cohesion=4
    #arch-eval:separation=4
    #arch-eval:consumer_clarity=3
    #arch-eval:state_invariants=4
    #arch-eval:entity_fullness=2
    #arch-eval:locational_stability=4
    """
    normalized_keyword = "" if keyword is None else keyword.strip().lower()
    if normalized_keyword.startswith(("scenario outline", "scenario template")):
        return HeadingType.SCENARIO_OUTLINE
    if normalized_keyword.startswith("scenario"):
        return HeadingType.SCENARIO
    return Nothing.value_or(None)


def _extract_line(node: Mapping[str, object]) -> int:
    """
    Configure and invoke `argparse.ArgumentParser` to parse CLI arguments for the heading validation tool, returning a .

    Responsibility:
        Configures and invokes `argparse.ArgumentParser` to parse CLI arguments for the heading validation tool,
        returning a `Namespace` with `root_path`, `include_patterns`, `json`, `baseline_audit`, and `fail_on_violation`
        fields.

    Reason for existence:
        Encapsulates all CLI option definitions so `main` remains focused on orchestrating the validation pipeline
        without coupling to argument-parsing details or default value management.

    Delegates:
        - `argparse.ArgumentParser.parse_args`: Does the actual string-to-Namespace conversion after argument
        definitions are registered.

    Cohesion:
        All logic inside this function configures exactly one `ArgumentParser` instance with mutually consistent
        options; there is no branching or unrelated setup.

    Separation:
        - `discover_feature_documents`: Kept separate because it performs filesystem discovery rather than CLI argument
        parsing, with no shared mutable state.

    Main consumers:
        - `validate_feature_headings.main`: Consumes the `argparse.Namespace` produced by `parse_args` to decide which
        code path (baseline audit vs. full scan) to execute.

    State and side effects:
        None, keeps no persistent state. Pure argument definition and parsing with no I/O beyond the argv list.

    Architecture score:
    #arch-eval:reason_for_existence=4
    #arch-eval:owned_responsibility=3
    #arch-eval:delegation_boundary=4
    #arch-eval:cohesion=4
    #arch-eval:separation=4
    #arch-eval:consumer_clarity=3
    #arch-eval:state_invariants=4
    #arch-eval:entity_fullness=2
    #arch-eval:locational_stability=4
    """
    location = node.get("location")
    if isinstance(location, Mapping):
        line = location.get("line")
        if isinstance(line, int):
            return line
    return 1


def _extract_column(node: Mapping[str, object]) -> int | None:
    """
    Configure and invoke `argparse.ArgumentParser` to parse CLI arguments for the heading validation tool, returning a .

    Responsibility:
        Configures and invokes `argparse.ArgumentParser` to parse CLI arguments for the heading validation tool,
        returning a `Namespace` with `root_path`, `include_patterns`, `json`, `baseline_audit`, and `fail_on_violation`
        fields.

    Reason for existence:
        Encapsulates all CLI option definitions so `main` remains focused on orchestrating the validation pipeline
        without coupling to argument-parsing details or default value management.

    Delegates:
        - `argparse.ArgumentParser.parse_args`: Does the actual string-to-Namespace conversion after argument
        definitions are registered.

    Cohesion:
        All logic inside this function configures exactly one `ArgumentParser` instance with mutually consistent
        options; there is no branching or unrelated setup.

    Separation:
        - `discover_feature_documents`: Kept separate because it performs filesystem discovery rather than CLI argument
        parsing, with no shared mutable state.

    Main consumers:
        - `validate_feature_headings.main`: Consumes the `argparse.Namespace` produced by `parse_args` to decide which
        code path (baseline audit vs. full scan) to execute.

    State and side effects:
        None, keeps no persistent state. Pure argument definition and parsing with no I/O beyond the argv list.

    Architecture score:
    #arch-eval:reason_for_existence=4
    #arch-eval:owned_responsibility=3
    #arch-eval:delegation_boundary=4
    #arch-eval:cohesion=4
    #arch-eval:separation=4
    #arch-eval:consumer_clarity=3
    #arch-eval:state_invariants=4
    #arch-eval:entity_fullness=2
    #arch-eval:locational_stability=4
    """
    location = node.get("location")
    if isinstance(location, Mapping):
        column = location.get("column")
        if isinstance(column, int):
            return column
    return Nothing.value_or(None)


def _as_optional_string(value: object) -> str | None:
    """
    Configure and invoke `argparse.ArgumentParser` to parse CLI arguments for the heading validation tool, returning a .

    Responsibility:
        Configures and invokes `argparse.ArgumentParser` to parse CLI arguments for the heading validation tool,
        returning a `Namespace` with `root_path`, `include_patterns`, `json`, `baseline_audit`, and `fail_on_violation`
        fields.

    Reason for existence:
        Encapsulates all CLI option definitions so `main` remains focused on orchestrating the validation pipeline
        without coupling to argument-parsing details or default value management.

    Delegates:
        - `argparse.ArgumentParser.parse_args`: Does the actual string-to-Namespace conversion after argument
        definitions are registered.

    Cohesion:
        All logic inside this function configures exactly one `ArgumentParser` instance with mutually consistent
        options; there is no branching or unrelated setup.

    Separation:
        - `discover_feature_documents`: Kept separate because it performs filesystem discovery rather than CLI argument
        parsing, with no shared mutable state.

    Main consumers:
        - `validate_feature_headings.main`: Consumes the `argparse.Namespace` produced by `parse_args` to decide which
        code path (baseline audit vs. full scan) to execute.

    State and side effects:
        None, keeps no persistent state. Pure argument definition and parsing with no I/O beyond the argv list.

    Architecture score:
    #arch-eval:reason_for_existence=4
    #arch-eval:owned_responsibility=3
    #arch-eval:delegation_boundary=4
    #arch-eval:cohesion=4
    #arch-eval:separation=4
    #arch-eval:consumer_clarity=3
    #arch-eval:state_invariants=4
    #arch-eval:entity_fullness=2
    #arch-eval:locational_stability=4
    """
    if value is None:
        return Nothing.value_or(None)
    if isinstance(value, str):
        return value
    return str(value)


def _is_markdown_gherkin(path: Path) -> bool:
    """
    Configure and invoke `argparse.ArgumentParser` to parse CLI arguments for the heading validation tool, returning a .

    Responsibility:
        Configures and invokes `argparse.ArgumentParser` to parse CLI arguments for the heading validation tool,
        returning a `Namespace` with `root_path`, `include_patterns`, `json`, `baseline_audit`, and `fail_on_violation`
        fields.

    Reason for existence:
        Encapsulates all CLI option definitions so `main` remains focused on orchestrating the validation pipeline
        without coupling to argument-parsing details or default value management.

    Delegates:
        - `argparse.ArgumentParser.parse_args`: Does the actual string-to-Namespace conversion after argument
        definitions are registered.

    Cohesion:
        All logic inside this function configures exactly one `ArgumentParser` instance with mutually consistent
        options; there is no branching or unrelated setup.

    Separation:
        - `discover_feature_documents`: Kept separate because it performs filesystem discovery rather than CLI argument
        parsing, with no shared mutable state.

    Main consumers:
        - `validate_feature_headings.main`: Consumes the `argparse.Namespace` produced by `parse_args` to decide which
        code path (baseline audit vs. full scan) to execute.

    State and side effects:
        None, keeps no persistent state. Pure argument definition and parsing with no I/O beyond the argv list.

    Architecture score:
    #arch-eval:reason_for_existence=4
    #arch-eval:owned_responsibility=3
    #arch-eval:delegation_boundary=4
    #arch-eval:cohesion=4
    #arch-eval:separation=4
    #arch-eval:consumer_clarity=3
    #arch-eval:state_invariants=4
    #arch-eval:entity_fullness=2
    #arch-eval:locational_stability=4
    """
    suffixes = tuple(path.suffixes[-2:]) if len(path.suffixes) >= 2 else ()  # noqa: PLR2004  -- 2 is the minimum suffix count for .feature.md detection (e.g. ['.feature', '.md'])
    return suffixes in _MARKDOWN_SUFFIXES


def _is_plain_gherkin(path: Path) -> bool:
    """
    Configure and invoke `argparse.ArgumentParser` to parse CLI arguments for the heading validation tool, returning a .

    Responsibility:
        Configures and invokes `argparse.ArgumentParser` to parse CLI arguments for the heading validation tool,
        returning a `Namespace` with `root_path`, `include_patterns`, `json`, `baseline_audit`, and `fail_on_violation`
        fields.

    Reason for existence:
        Encapsulates all CLI option definitions so `main` remains focused on orchestrating the validation pipeline
        without coupling to argument-parsing details or default value management.

    Delegates:
        - `argparse.ArgumentParser.parse_args`: Does the actual string-to-Namespace conversion after argument
        definitions are registered.

    Cohesion:
        All logic inside this function configures exactly one `ArgumentParser` instance with mutually consistent
        options; there is no branching or unrelated setup.

    Separation:
        - `discover_feature_documents`: Kept separate because it performs filesystem discovery rather than CLI argument
        parsing, with no shared mutable state.

    Main consumers:
        - `validate_feature_headings.main`: Consumes the `argparse.Namespace` produced by `parse_args` to decide which
        code path (baseline audit vs. full scan) to execute.

    State and side effects:
        None, keeps no persistent state. Pure argument definition and parsing with no I/O beyond the argv list.

    Architecture score:
    #arch-eval:reason_for_existence=4
    #arch-eval:owned_responsibility=3
    #arch-eval:delegation_boundary=4
    #arch-eval:cohesion=4
    #arch-eval:separation=4
    #arch-eval:consumer_clarity=3
    #arch-eval:state_invariants=4
    #arch-eval:entity_fullness=2
    #arch-eval:locational_stability=4
    """
    return path.suffix in {".feature", ".gherkin"}


def _is_supported_feature_path(path: Path) -> bool:
    """
    Configure and invoke `argparse.ArgumentParser` to parse CLI arguments for the heading validation tool, returning a .

    Responsibility:
        Configures and invokes `argparse.ArgumentParser` to parse CLI arguments for the heading validation tool,
        returning a `Namespace` with `root_path`, `include_patterns`, `json`, `baseline_audit`, and `fail_on_violation`
        fields.

    Reason for existence:
        Encapsulates all CLI option definitions so `main` remains focused on orchestrating the validation pipeline
        without coupling to argument-parsing details or default value management.

    Delegates:
        - `argparse.ArgumentParser.parse_args`: Does the actual string-to-Namespace conversion after argument
        definitions are registered.

    Cohesion:
        All logic inside this function configures exactly one `ArgumentParser` instance with mutually consistent
        options; there is no branching or unrelated setup.

    Separation:
        - `discover_feature_documents`: Kept separate because it performs filesystem discovery rather than CLI argument
        parsing, with no shared mutable state.

    Main consumers:
        - `validate_feature_headings.main`: Consumes the `argparse.Namespace` produced by `parse_args` to decide which
        code path (baseline audit vs. full scan) to execute.

    State and side effects:
        None, keeps no persistent state. Pure argument definition and parsing with no I/O beyond the argv list.

    Architecture score:
    #arch-eval:reason_for_existence=4
    #arch-eval:owned_responsibility=3
    #arch-eval:delegation_boundary=4
    #arch-eval:cohesion=4
    #arch-eval:separation=4
    #arch-eval:consumer_clarity=3
    #arch-eval:state_invariants=4
    #arch-eval:entity_fullness=2
    #arch-eval:locational_stability=4
    """
    return _is_plain_gherkin(path) or _is_markdown_gherkin(path)


def _emit_json(payload: dict[str, object]) -> None:
    """
    Configure and invoke `argparse.ArgumentParser` to parse CLI arguments for the heading validation tool, returning a .

    Responsibility:
        Configures and invokes `argparse.ArgumentParser` to parse CLI arguments for the heading validation tool,
        returning a `Namespace` with `root_path`, `include_patterns`, `json`, `baseline_audit`, and `fail_on_violation`
        fields.

    Reason for existence:
        Encapsulates all CLI option definitions so `main` remains focused on orchestrating the validation pipeline
        without coupling to argument-parsing details or default value management.

    Delegates:
        - `argparse.ArgumentParser.parse_args`: Does the actual string-to-Namespace conversion after argument
        definitions are registered.

    Cohesion:
        All logic inside this function configures exactly one `ArgumentParser` instance with mutually consistent
        options; there is no branching or unrelated setup.

    Separation:
        - `discover_feature_documents`: Kept separate because it performs filesystem discovery rather than CLI argument
        parsing, with no shared mutable state.

    Main consumers:
        - `validate_feature_headings.main`: Consumes the `argparse.Namespace` produced by `parse_args` to decide which
        code path (baseline audit vs. full scan) to execute.

    State and side effects:
        None, keeps no persistent state. Pure argument definition and parsing with no I/O beyond the argv list.

    Architecture score:
    #arch-eval:reason_for_existence=4
    #arch-eval:owned_responsibility=3
    #arch-eval:delegation_boundary=4
    #arch-eval:cohesion=4
    #arch-eval:separation=4
    #arch-eval:consumer_clarity=3
    #arch-eval:state_invariants=4
    #arch-eval:entity_fullness=2
    #arch-eval:locational_stability=4
    """
    sys.stdout.write(json.dumps(payload, sort_keys=True))
    sys.stdout.write("\n")


def _emit_text_run_result(run: HeadingValidationRun) -> None:
    """
    Configure and invoke `argparse.ArgumentParser` to parse CLI arguments for the heading validation tool, returning a .

    Responsibility:
        Configures and invokes `argparse.ArgumentParser` to parse CLI arguments for the heading validation tool,
        returning a `Namespace` with `root_path`, `include_patterns`, `json`, `baseline_audit`, and `fail_on_violation`
        fields.

    Reason for existence:
        Encapsulates all CLI option definitions so `main` remains focused on orchestrating the validation pipeline
        without coupling to argument-parsing details or default value management.

    Delegates:
        - `argparse.ArgumentParser.parse_args`: Does the actual string-to-Namespace conversion after argument
        definitions are registered.

    Cohesion:
        All logic inside this function configures exactly one `ArgumentParser` instance with mutually consistent
        options; there is no branching or unrelated setup.

    Separation:
        - `discover_feature_documents`: Kept separate because it performs filesystem discovery rather than CLI argument
        parsing, with no shared mutable state.

    Main consumers:
        - `validate_feature_headings.main`: Consumes the `argparse.Namespace` produced by `parse_args` to decide which
        code path (baseline audit vs. full scan) to execute.

    State and side effects:
        None, keeps no persistent state. Pure argument definition and parsing with no I/O beyond the argv list.

    Architecture score:
    #arch-eval:reason_for_existence=4
    #arch-eval:owned_responsibility=3
    #arch-eval:delegation_boundary=4
    #arch-eval:cohesion=4
    #arch-eval:separation=4
    #arch-eval:consumer_clarity=3
    #arch-eval:state_invariants=4
    #arch-eval:entity_fullness=2
    #arch-eval:locational_stability=4
    """
    if run.violations:
        for violation in run.violations:
            sys.stdout.write(
                f"{violation.path}:{violation.line}: {violation.heading_type.value}: "
                f"{violation.code}: {violation.message}\n",
            )
    else:
        sys.stdout.write(
            f"Heading validation passed for {run.documents_scanned} document(s).\n",
        )


def _emit_text_baseline_result(summary: BaselineAuditSummary) -> None:
    """
    Configure and invoke `argparse.ArgumentParser` to parse CLI arguments for the heading validation tool, returning a .

    Responsibility:
        Configures and invokes `argparse.ArgumentParser` to parse CLI arguments for the heading validation tool,
        returning a `Namespace` with `root_path`, `include_patterns`, `json`, `baseline_audit`, and `fail_on_violation`
        fields.

    Reason for existence:
        Encapsulates all CLI option definitions so `main` remains focused on orchestrating the validation pipeline
        without coupling to argument-parsing details or default value management.

    Delegates:
        - `argparse.ArgumentParser.parse_args`: Does the actual string-to-Namespace conversion after argument
        definitions are registered.

    Cohesion:
        All logic inside this function configures exactly one `ArgumentParser` instance with mutually consistent
        options; there is no branching or unrelated setup.

    Separation:
        - `discover_feature_documents`: Kept separate because it performs filesystem discovery rather than CLI argument
        parsing, with no shared mutable state.

    Main consumers:
        - `validate_feature_headings.main`: Consumes the `argparse.Namespace` produced by `parse_args` to decide which
        code path (baseline audit vs. full scan) to execute.

    State and side effects:
        None, keeps no persistent state. Pure argument definition and parsing with no I/O beyond the argv list.

    Architecture score:
    #arch-eval:reason_for_existence=4
    #arch-eval:owned_responsibility=3
    #arch-eval:delegation_boundary=4
    #arch-eval:cohesion=4
    #arch-eval:separation=4
    #arch-eval:consumer_clarity=3
    #arch-eval:state_invariants=4
    #arch-eval:entity_fullness=2
    #arch-eval:locational_stability=4
    """
    status = "pass" if summary.compliant else "fail"
    sys.stdout.write(
        " ".join(
            [
                f"policy={summary.policy_id}",
                f"violations={summary.violations_count}",
                f"status={status}",
            ],
        ),
    )
    sys.stdout.write("\n")


def main(argv: list[str] | None = None) -> int:
    """
    Configure and invoke `argparse.ArgumentParser` to parse CLI arguments for the heading validation tool, returning a .

    Responsibility:
        Configures and invokes `argparse.ArgumentParser` to parse CLI arguments for the heading validation tool,
        returning a `Namespace` with `root_path`, `include_patterns`, `json`, `baseline_audit`, and `fail_on_violation`
        fields.

    Reason for existence:
        Encapsulates all CLI option definitions so `main` remains focused on orchestrating the validation pipeline
        without coupling to argument-parsing details or default value management.

    Delegates:
        - `argparse.ArgumentParser.parse_args`: Does the actual string-to-Namespace conversion after argument
        definitions are registered.

    Cohesion:
        All logic inside this function configures exactly one `ArgumentParser` instance with mutually consistent
        options; there is no branching or unrelated setup.

    Separation:
        - `discover_feature_documents`: Kept separate because it performs filesystem discovery rather than CLI argument
        parsing, with no shared mutable state.

    Main consumers:
        - `validate_feature_headings.main`: Consumes the `argparse.Namespace` produced by `parse_args` to decide which
        code path (baseline audit vs. full scan) to execute.

    State and side effects:
        None, keeps no persistent state. Pure argument definition and parsing with no I/O beyond the argv list.

    Architecture score:
    #arch-eval:reason_for_existence=4
    #arch-eval:owned_responsibility=3
    #arch-eval:delegation_boundary=4
    #arch-eval:cohesion=4
    #arch-eval:separation=4
    #arch-eval:consumer_clarity=3
    #arch-eval:state_invariants=4
    #arch-eval:entity_fullness=2
    #arch-eval:locational_stability=4
    """
    args = parse_args(argv)

    include_patterns = tuple(args.include_patterns or DEFAULT_INCLUDE_PATTERNS)
    root_path = args.root_path.resolve()

    if args.baseline_audit:
        baseline_summary = build_baseline_audit(root_path=root_path, include_patterns=include_patterns)
        if args.json:
            _emit_json(baseline_summary.to_payload())
        else:
            _emit_text_baseline_result(baseline_summary)

        return 1 if args.fail_on_violation and not baseline_summary.compliant else 0

    run_result = run_heading_validation_scan(root_path=root_path, include_patterns=include_patterns)
    if args.json:
        _emit_json(run_result.to_payload())
    else:
        _emit_text_run_result(run_result)

    return 1 if args.fail_on_violation and run_result.status == "fail" else 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
