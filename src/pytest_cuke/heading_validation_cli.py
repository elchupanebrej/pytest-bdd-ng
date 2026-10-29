"""Argument and output adapter for the standalone ``cuke validate`` command."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import TYPE_CHECKING

from pytest_cuke.heading_scanner import (
    HeadingValidationScanError,
    build_baseline_audit,
    run_heading_validation_scan,
)
from pytest_cuke.heading_validation import (
    BaselineAuditSummary,
    HeadingValidationRun,
    heading_validation_policy_payload,
)

if TYPE_CHECKING:
    import argparse


def configure_validation_parser(parser: argparse.ArgumentParser) -> None:
    """Add scan, baseline, JSON and advisory options to the reserved command."""
    parser.add_argument(
        "--include-pattern",
        dest="include_patterns",
        action="append",
        default=None,
        help="glob include pattern (repeatable)",
    )
    parser.add_argument("--json", action="store_true", help="emit the structured JSON payload")
    parser.add_argument("--baseline-audit", action="store_true", help="emit the baseline compliance summary")
    parser.add_argument(
        "--policy",
        action="store_true",
        help="emit the active heading policy as JSON",
    )
    parser.add_argument(
        "--no-fail-on-violation",
        action="store_false",
        dest="fail_on_violation",
        help="advisory mode: return zero when headings violate the policy",
    )
    parser.set_defaults(fail_on_violation=True)


def run_validation_command(namespace: argparse.Namespace) -> int:
    """Run the selected validation operation and return its process status."""
    if namespace.policy:
        _emit_json(heading_validation_policy_payload())
        return 0

    root_path = Path(namespace.features_dir)
    try:
        if namespace.baseline_audit:
            summary = build_baseline_audit(root_path, include_patterns=namespace.include_patterns)
            if namespace.json:
                _emit_json(summary.to_payload())
            else:
                _emit_text_baseline_result(summary)
            return 1 if namespace.fail_on_violation and not summary.compliant else 0

        run = run_heading_validation_scan(root_path, include_patterns=namespace.include_patterns)
    except HeadingValidationScanError as error:
        if namespace.json:
            _emit_json({"error": error.to_payload()})
        else:
            print(f"cuke validate: {error}", file=sys.stderr)
        return 2

    if namespace.json:
        _emit_json(run.to_payload())
    else:
        _emit_text_run_result(run)
    return 1 if namespace.fail_on_violation and run.violations else 0


def _emit_json(payload: dict[str, object]) -> None:
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True))


def _emit_text_run_result(run: HeadingValidationRun) -> None:
    if run.violations:
        for violation in run.violations:
            print(
                f"{violation.path}:{violation.line}: {violation.heading_type.value}: "
                f"{violation.code}: {violation.message}",
            )
    else:
        print(f"Heading validation passed for {run.documents_scanned} document(s).")


def _emit_text_baseline_result(summary: BaselineAuditSummary) -> None:
    status = "pass" if summary.compliant else "fail"
    print(f"policy={summary.policy_id} violations={summary.violations_count} status={status}")


__all__ = ["configure_validation_parser", "run_validation_command"]
