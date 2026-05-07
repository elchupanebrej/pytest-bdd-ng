"""Validate parsed BDD headings for non-empty titles."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Iterable, Mapping
from datetime import datetime, timezone
from pathlib import Path
from typing import cast

from gherkin.ast_builder import AstBuilder
from gherkin.errors import CompositeParserException
from gherkin.parser import Parser
from gherkin.token_matcher_markdown import GherkinInMarkdownTokenMatcher
from gherkin.token_scanner import TokenScanner

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
from pytest_bdd.types.json import JSONObject
from pytest_bdd.util.other import IdGenerator

DEFAULT_INCLUDE_PATTERNS = (
    "**/*.feature",
    "**/*.gherkin",
    "**/*.feature.md",
    "**/*.gherkin.md",
)
_MARKDOWN_SUFFIXES = {(".feature", ".md"), (".gherkin", ".md")}


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command line arguments."""
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
    """Serialize heading validation policy for contract checks."""
    active_policy = default_heading_validation_policy() if policy is None else policy
    return {
        "policy_id": active_policy.policy_id,
        "enforced_heading_types": [heading_type.value for heading_type in active_policy.enforced_heading_types],
        "trim_whitespace": active_policy.trim_whitespace,
        "empty_name_is_violation": active_policy.empty_name_is_violation,
        "snippet_text_excluded": active_policy.snippet_text_excluded,
    }


def discover_feature_documents(root_path: Path, include_patterns: Iterable[str] | None = None) -> list[Path]:
    """Discover feature documents under a root path."""
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
    """Execute heading validation scan for feature documents."""
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
    """Build baseline compliance summary for repository feature documents."""
    active_policy = default_heading_validation_policy() if policy is None else policy
    validation_run = run_heading_validation_scan(
        root_path=root_path, include_patterns=include_patterns, policy=active_policy
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

    Raises:
        ValueError: If the feature document cannot be parsed.

    """
    parser = Parser(ast_builder=AstBuilder(id_generator=IdGenerator()))
    feature_file_data = path.read_text(encoding="utf-8")

    try:
        if _is_markdown_gherkin(path):
            parsed_document = parser.parse(TokenScanner(feature_file_data), GherkinInMarkdownTokenMatcher())
        else:
            parsed_document = parser.parse(feature_file_data)
        return cast(JSONObject, parsed_document)
    except CompositeParserException as exc:  # pragma: no cover - parser-level failures are exceptional for this scan
        msg = f"Unable to parse feature document: {path.as_posix()}"
        raise ValueError(msg) from exc


def extract_parsed_heading_records(
    path: Path, gherkin_document: Mapping[str, object], root_path: Path
) -> list[ParsedHeadingRecord]:
    """Extract heading records from parsed feature document."""
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
    """Validate heading records against policy."""
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
    normalized_keyword = "" if keyword is None else keyword.strip().lower()
    if normalized_keyword.startswith(("scenario outline", "scenario template")):
        return HeadingType.SCENARIO_OUTLINE
    if normalized_keyword.startswith("scenario"):
        return HeadingType.SCENARIO
    return None


def _extract_line(node: Mapping[str, object]) -> int:
    location = node.get("location")
    if isinstance(location, Mapping):
        line = location.get("line")
        if isinstance(line, int):
            return line
    return 1


def _extract_column(node: Mapping[str, object]) -> int | None:
    location = node.get("location")
    if isinstance(location, Mapping):
        column = location.get("column")
        if isinstance(column, int):
            return column
    return None


def _as_optional_string(value: object) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        return value
    return str(value)


def _is_markdown_gherkin(path: Path) -> bool:
    suffixes = tuple(path.suffixes[-2:]) if len(path.suffixes) >= 2 else ()
    return suffixes in _MARKDOWN_SUFFIXES


def _is_plain_gherkin(path: Path) -> bool:
    return path.suffix in {".feature", ".gherkin"}


def _is_supported_feature_path(path: Path) -> bool:
    return _is_plain_gherkin(path) or _is_markdown_gherkin(path)


def _emit_json(payload: dict[str, object]) -> None:
    sys.stdout.write(json.dumps(payload, sort_keys=True))
    sys.stdout.write("\n")


def _emit_text_run_result(run: HeadingValidationRun) -> None:
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
    """CLI entry point."""
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
