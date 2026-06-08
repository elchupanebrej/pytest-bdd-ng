"""
Validate parsed BDD headings for non-empty titles.

Responsibility:
    Validate parsed BDD headings for non-empty titles. It directly owns the observable contract, local decisions, and
    maintenance boundary for this module.

Reason for existence:
    This entity is the information expert for `pytest_bdd.script.validate_feature_headings` because it keeps the nearest
    code, data shape, call signature, and failure knowledge together.

Delegates:
    - parse_args: owns nested behavior below this boundary
    - heading_validation_policy_payload: owns nested behavior below this boundary
    - discover_feature_documents: owns nested behavior below this boundary
    - run_heading_validation_scan: owns nested behavior below this boundary
    - build_baseline_audit: owns nested behavior below this boundary
    - parse_gherkin_document: owns nested behavior below this boundary

Cohesion:
    The implementation stays together because its imports, calls, state writes, and return contract describe one
    maintainable decision unit.

Separation:
    - module peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
      widening caller knowledge.

Main consumers:
    - None found by static import/name scan; verify dynamic use before refactor

State and side effects:
    mutates active_policy, records, parser, violations, parsed_document; depends on __future__.annotations, argparse,
    json, sys, collections.abc.Iterable.

Invariants:
    - `pytest_bdd.script.validate_feature_headings` keeps its documented import path, ownership boundary, and observable
      behavior stable for callers.

Failure semantics:
    Raises or re-raises ValueError, SystemExit; callers must treat these as boundary failures.

Architecture score:
    #arch-eval:reason_for_existence=4
    #arch-eval:owned_responsibility=4
    #arch-eval:delegation_boundary=4
    #arch-eval:cohesion=3
    #arch-eval:separation=3
    #arch-eval:consumer_clarity=2
    #arch-eval:state_invariants=4
    #arch-eval:entity_fullness=4
    #arch-eval:locational_stability=2
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
    Parse command line arguments.

    Returns:
        Parsed arguments namespace.

    Responsibility:
        Parse command line arguments. It directly owns the observable contract, local decisions, and maintenance
        boundary for this function. That boundary is intentionally stated in prose so maintainers can distinguish owned
        work from collaborators before editing.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.script.validate_feature_headings.parse_args` because it
        keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - parser.add_argument: collaborator call used by this boundary
        - argparse.ArgumentParser: collaborator call used by this boundary
        - Path: collaborator call used by this boundary
        - parser.set_defaults: collaborator call used by this boundary
        - parser.parse_args: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/feature_locator.py: imports or references `parse_args`
        - src/pytest_bdd/model/coverage/inventory.py: imports or references `parse_args`
        - src/pytest_bdd/scenario.py: imports or references `parse_args`
        - src/pytest_bdd/scenario_locator/file_locator.py: imports or references `parse_args`
        - src/pytest_bdd/scenario_locator/url_locator.py: imports or references `parse_args`

    State and side effects:
        mutates parser.

    Invariants:
        - `pytest_bdd.script.validate_feature_headings.parse_args` keeps its documented import path, ownership boundary,
          and observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
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
    Serialize heading validation policy for contract checks.

    Args:
        policy: Heading validation policy.

    Returns:
        Policy as dictionary.

    Responsibility:
        Serialize heading validation policy for contract checks. It directly owns the observable contract, local
        decisions, and maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.script.validate_feature_headings.heading_validation_policy_payload` because it keeps the nearest
        code, data shape, call signature, and failure knowledge together.

    Delegates:
        - default_heading_validation_policy: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - None found by static import/name scan; verify dynamic use before refactor

    State and side effects:
        mutates active_policy.

    Invariants:
        - `pytest_bdd.script.validate_feature_headings.heading_validation_policy_payload` keeps its documented import
          path, ownership boundary, and observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=2
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=2

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
    Discover feature documents under a root path.

    Args:
        root_path: Root path to search.
        include_patterns: Include patterns.

    Returns:
        List of discovered paths.

    Responsibility:
        Discover feature documents under a root path. It directly owns the observable contract, local decisions, and
        maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.script.validate_feature_headings.discover_feature_documents` because it keeps the nearest code, data
        shape, call signature, and failure knowledge together.

    Delegates:
        - tuple: collaborator call used by this boundary
        - path.resolve: collaborator call used by this boundary
        - root_path.glob: collaborator call used by this boundary
        - path.is_file: collaborator call used by this boundary
        - _is_supported_feature_path: collaborator call used by this boundary
        - sorted: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - None found by static import/name scan; verify dynamic use before refactor

    State and side effects:
        mutates patterns, discovered_paths.

    Invariants:
        - `pytest_bdd.script.validate_feature_headings.discover_feature_documents` keeps its documented import path,
          ownership boundary, and observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=2
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=2

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
    Execute heading validation scan for feature documents.

    Args:
        root_path: Root path to scan.
        include_patterns: Patterns to include.
        policy: Validation policy.

    Returns:
        Heading validation run result.

    Responsibility:
        Execute heading validation scan for feature documents. It directly owns the observable contract, local
        decisions, and maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.script.validate_feature_headings.run_heading_validation_scan` because it keeps the nearest code,
        data shape, call signature, and failure knowledge together.

    Delegates:
        - datetime.now: collaborator call used by this boundary
        - default_heading_validation_policy: collaborator call used by this boundary
        - discover_feature_documents: collaborator call used by this boundary
        - parse_gherkin_document: collaborator call used by this boundary
        - extract_parsed_heading_records: collaborator call used by this boundary
        - violations.extend: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - None found by static import/name scan; verify dynamic use before refactor

    State and side effects:
        mutates started_at, active_policy, document_paths, violations, gherkin_document.

    Invariants:
        - `pytest_bdd.script.validate_feature_headings.run_heading_validation_scan` keeps its documented import path,
          ownership boundary, and observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=2
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=2

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
    Build baseline compliance summary for repository feature documents.

    Args:
        root_path: Root path to scan.
        include_patterns: Patterns to include.
        policy: Validation policy.

    Returns:
        Baseline audit summary.

    Responsibility:
        Build baseline compliance summary for repository feature documents. It directly owns the observable contract,
        local decisions, and maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.script.validate_feature_headings.build_baseline_audit`
        because it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - default_heading_validation_policy: collaborator call used by this boundary
        - run_heading_validation_scan: collaborator call used by this boundary
        - BaselineAuditSummary: collaborator call used by this boundary
        - len: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - None found by static import/name scan; verify dynamic use before refactor

    State and side effects:
        mutates active_policy, validation_run.

    Invariants:
        - `pytest_bdd.script.validate_feature_headings.build_baseline_audit` keeps its documented import path, ownership
          boundary, and observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=2
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=2

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
    Parse a gherkin or gherkin-markdown document into raw AST dictionary.

    Args:
        path: Path to the feature file.

    Returns:
        Parsed Gherkin document as JSON.

    Raises:
        ValueError: If the feature document cannot be parsed.

    Responsibility:
        Parse a gherkin or gherkin-markdown document into raw AST dictionary. It directly owns the observable contract,
        local decisions, and maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.script.validate_feature_headings.parse_gherkin_document`
        because it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - parser.parse: collaborator call used by this boundary
        - Parser: collaborator call used by this boundary
        - AstBuilder: collaborator call used by this boundary
        - IdGenerator: collaborator call used by this boundary
        - path.read_text: collaborator call used by this boundary
        - _is_markdown_gherkin: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/_gherkin_go/__init__.py: imports or references `parse_gherkin_document`

    State and side effects:
        mutates parsed_document, parser, feature_file_data, msg.

    Invariants:
        - `pytest_bdd.script.validate_feature_headings.parse_gherkin_document` keeps its documented import path,
          ownership boundary, and observable behavior stable for callers.

    Failure semantics:
        Raises or re-raises ValueError; callers must treat these as boundary failures.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=3

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
    Extract heading records from parsed feature document.

    Returns:
        List of parsed heading records.

    Responsibility:
        Extract heading records from parsed feature document. It directly owns the observable contract, local decisions,
        and maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.script.validate_feature_headings.extract_parsed_heading_records` because it keeps the nearest code,
        data shape, call signature, and failure knowledge together.

    Delegates:
        - feature_data.get: collaborator call used by this boundary
        - path.resolve.relative_to.as_posix: collaborator call used by this boundary
        - path.resolve.relative_to: collaborator call used by this boundary
        - path.resolve: collaborator call used by this boundary
        - root_path.resolve: collaborator call used by this boundary
        - gherkin_document.get: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - None found by static import/name scan; verify dynamic use before refactor

    State and side effects:
        mutates relative_path, feature_data, records.

    Invariants:
        - `pytest_bdd.script.validate_feature_headings.extract_parsed_heading_records` keeps its documented import path,
          ownership boundary, and observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=2
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=2

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
    Validate heading records against policy.

    Returns:
        List of validation violations.

    Responsibility:
        Validate heading records against policy. It directly owns the observable contract, local decisions, and
        maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.script.validate_feature_headings.validate_heading_records`
        because it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - default_heading_validation_policy: collaborator call used by this boundary
        - active_policy.normalize_name: collaborator call used by this boundary
        - violations.append: collaborator call used by this boundary
        - HeadingValidationViolation: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - None found by static import/name scan; verify dynamic use before refactor

    State and side effects:
        mutates active_policy, violations, normalized_name.

    Invariants:
        - `pytest_bdd.script.validate_feature_headings.validate_heading_records` keeps its documented import path,
          ownership boundary, and observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=2
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=2

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
    Responsibility:
        Responsibility: Responsibility: `pytest_bdd.script.validate_feature_headings._extract_scenario_records` owns
        documented function behavior. It directly owns the observable contract, local decisions, and maintenance
        boundary for this function.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.script.validate_feature_headings._extract_scenario_records` because it keeps the nearest code, data
        shape, call signature, and failure knowledge together.

    Delegates:
        - isinstance: collaborator call used by this boundary
        - child.get: collaborator call used by this boundary
        - _as_optional_string: collaborator call used by this boundary
        - scenario_data.get: collaborator call used by this boundary
        - _heading_type_from_keyword: collaborator call used by this boundary
        - records.append: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - None found by static import/name scan; verify dynamic use before refactor

    State and side effects:
        mutates records, scenario_data, heading_type, rule_data.

    Invariants:
        - `pytest_bdd.script.validate_feature_headings._extract_scenario_records` keeps its documented import path,
          ownership boundary, and observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=2
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=2
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
    Responsibility:
        Responsibility: Responsibility: `pytest_bdd.script.validate_feature_headings._heading_type_from_keyword` owns
        documented function behavior. It directly owns the observable contract, local decisions, and maintenance
        boundary for this function.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.script.validate_feature_headings._heading_type_from_keyword` because it keeps the nearest code, data
        shape, call signature, and failure knowledge together.

    Delegates:
        - normalized_keyword.startswith: collaborator call used by this boundary
        - keyword.strip.lower: collaborator call used by this boundary
        - keyword.strip: collaborator call used by this boundary
        - Nothing.value_or: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - None found by static import/name scan; verify dynamic use before refactor

    State and side effects:
        mutates normalized_keyword.

    Invariants:
        - `pytest_bdd.script.validate_feature_headings._heading_type_from_keyword` keeps its documented import path,
          ownership boundary, and observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=2
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=2
    """
    normalized_keyword = "" if keyword is None else keyword.strip().lower()
    if normalized_keyword.startswith(("scenario outline", "scenario template")):
        return HeadingType.SCENARIO_OUTLINE
    if normalized_keyword.startswith("scenario"):
        return HeadingType.SCENARIO
    return Nothing.value_or(None)


def _extract_line(node: Mapping[str, object]) -> int:
    """
    Responsibility:
        Responsibility: Responsibility: `pytest_bdd.script.validate_feature_headings._extract_line` owns documented
        function behavior. It directly owns the observable contract, local decisions, and maintenance boundary for this
        function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.script.validate_feature_headings._extract_line` because it
        keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - isinstance: collaborator call used by this boundary
        - node.get: collaborator call used by this boundary
        - location.get: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - None found by static import/name scan; verify dynamic use before refactor

    State and side effects:
        mutates location, line.

    Invariants:
        - `pytest_bdd.script.validate_feature_headings._extract_line` keeps its documented import path, ownership
          boundary, and observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=2
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=2
    """
    location = node.get("location")
    if isinstance(location, Mapping):
        line = location.get("line")
        if isinstance(line, int):
            return line
    return 1


def _extract_column(node: Mapping[str, object]) -> int | None:
    """
    Responsibility:
        Responsibility: Responsibility: `pytest_bdd.script.validate_feature_headings._extract_column` owns documented
        function behavior. It directly owns the observable contract, local decisions, and maintenance boundary for this
        function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.script.validate_feature_headings._extract_column` because
        it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - isinstance: collaborator call used by this boundary
        - node.get: collaborator call used by this boundary
        - location.get: collaborator call used by this boundary
        - Nothing.value_or: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - None found by static import/name scan; verify dynamic use before refactor

    State and side effects:
        mutates location, column.

    Invariants:
        - `pytest_bdd.script.validate_feature_headings._extract_column` keeps its documented import path, ownership
          boundary, and observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=2
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=2
    """
    location = node.get("location")
    if isinstance(location, Mapping):
        column = location.get("column")
        if isinstance(column, int):
            return column
    return Nothing.value_or(None)


def _as_optional_string(value: object) -> str | None:
    """
    Responsibility:
        Responsibility: Responsibility: `pytest_bdd.script.validate_feature_headings._as_optional_string` owns
        documented function behavior. It directly owns the observable contract, local decisions, and maintenance
        boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.script.validate_feature_headings._as_optional_string`
        because it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - Nothing.value_or: collaborator call used by this boundary
        - isinstance: collaborator call used by this boundary
        - str: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - None found by static import/name scan; verify dynamic use before refactor

    State and side effects:
        keeps no local persistent state beyond call-local values.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=2
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=2
    """
    if value is None:
        return Nothing.value_or(None)
    if isinstance(value, str):
        return value
    return str(value)


def _is_markdown_gherkin(path: Path) -> bool:
    """
    Responsibility:
        Responsibility: Responsibility: `pytest_bdd.script.validate_feature_headings._is_markdown_gherkin` owns
        documented function behavior. It directly owns the observable contract, local decisions, and maintenance
        boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.script.validate_feature_headings._is_markdown_gherkin`
        because it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - len: collaborator call used by this boundary
        - tuple: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - None found by static import/name scan; verify dynamic use before refactor

    State and side effects:
        mutates suffixes.

    Invariants:
        - `pytest_bdd.script.validate_feature_headings._is_markdown_gherkin` keeps its documented import path, ownership
          boundary, and observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=2
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=2
    """
    suffixes = tuple(path.suffixes[-2:]) if len(path.suffixes) >= 2 else ()  # noqa: PLR2004
    return suffixes in _MARKDOWN_SUFFIXES


def _is_plain_gherkin(path: Path) -> bool:
    """
    Responsibility:
        Responsibility: Responsibility: `pytest_bdd.script.validate_feature_headings._is_plain_gherkin` owns documented
        function behavior. It directly owns the observable contract, local decisions, and maintenance boundary for this
        function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.script.validate_feature_headings._is_plain_gherkin`
        because it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - None, leaf-level implementation boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - None found by static import/name scan; verify dynamic use before refactor

    State and side effects:
        keeps no local persistent state beyond call-local values.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=2
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=2
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=3
        #arch-eval:locational_stability=2
    """
    return path.suffix in {".feature", ".gherkin"}


def _is_supported_feature_path(path: Path) -> bool:
    """
    Responsibility:
        Responsibility: Responsibility: `pytest_bdd.script.validate_feature_headings._is_supported_feature_path` owns
        documented function behavior. It directly owns the observable contract, local decisions, and maintenance
        boundary for this function.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.script.validate_feature_headings._is_supported_feature_path` because it keeps the nearest code, data
        shape, call signature, and failure knowledge together.

    Delegates:
        - _is_plain_gherkin: collaborator call used by this boundary
        - _is_markdown_gherkin: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - None found by static import/name scan; verify dynamic use before refactor

    State and side effects:
        keeps no local persistent state beyond call-local values.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=2
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=2
    """
    return _is_plain_gherkin(path) or _is_markdown_gherkin(path)


def _emit_json(payload: dict[str, object]) -> None:
    """
    Responsibility:
        Responsibility: Responsibility: `pytest_bdd.script.validate_feature_headings._emit_json` owns documented
        function behavior. It directly owns the observable contract, local decisions, and maintenance boundary for this
        function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.script.validate_feature_headings._emit_json` because it
        keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - sys.stdout.write: collaborator call used by this boundary
        - json.dumps: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - None found by static import/name scan; verify dynamic use before refactor

    State and side effects:
        keeps no local persistent state beyond call-local values.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=2
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=2
    """
    sys.stdout.write(json.dumps(payload, sort_keys=True))
    sys.stdout.write("\n")


def _emit_text_run_result(run: HeadingValidationRun) -> None:
    """
    Responsibility:
        Responsibility: Responsibility: `pytest_bdd.script.validate_feature_headings._emit_text_run_result` owns
        documented function behavior. It directly owns the observable contract, local decisions, and maintenance
        boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.script.validate_feature_headings._emit_text_run_result`
        because it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - sys.stdout.write: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - None found by static import/name scan; verify dynamic use before refactor

    State and side effects:
        keeps no local persistent state beyond call-local values.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=2
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=2
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
    Responsibility:
        Responsibility: Responsibility: `pytest_bdd.script.validate_feature_headings._emit_text_baseline_result` owns
        documented function behavior. It directly owns the observable contract, local decisions, and maintenance
        boundary for this function.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.script.validate_feature_headings._emit_text_baseline_result` because it keeps the nearest code, data
        shape, call signature, and failure knowledge together.

    Delegates:
        - sys.stdout.write: collaborator call used by this boundary
        - join: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - None found by static import/name scan; verify dynamic use before refactor

    State and side effects:
        mutates status.

    Invariants:
        - `pytest_bdd.script.validate_feature_headings._emit_text_baseline_result` keeps its documented import path,
          ownership boundary, and observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=2
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=2
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
    CLI entry point.

    Returns:
        Exit code.

    Responsibility:
        CLI entry point. It directly owns the observable contract, local decisions, and maintenance boundary for this
        function. That boundary is intentionally stated in prose so maintainers can distinguish owned work from
        collaborators before editing.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.script.validate_feature_headings.main` because it keeps
        the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - _emit_json: collaborator call used by this boundary
        - parse_args: collaborator call used by this boundary
        - tuple: collaborator call used by this boundary
        - args.root_path.resolve: collaborator call used by this boundary
        - build_baseline_audit: collaborator call used by this boundary
        - baseline_summary.to_payload: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/model/coverage/inventory.py: imports or references `main`
        - src/pytest_bdd/script/__init__.py: imports or references `main`
        - src/pytest_bdd/script/compatibility_matrix.py: imports or references `main`
        - src/pytest_bdd/script/message_capability_governance/__init__.py: imports or references `main`
        - src/pytest_bdd/script/message_capability_governance/__main__.py: imports or references `main`

    State and side effects:
        mutates args, include_patterns, root_path, baseline_summary, run_result.

    Invariants:
        - `pytest_bdd.script.validate_feature_headings.main` keeps its documented import path, ownership boundary, and
          observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
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
