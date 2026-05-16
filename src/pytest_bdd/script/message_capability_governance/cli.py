"""CLI entry point for message capability governance."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING, cast

from pytest_bdd.model.coverage.inventory import (
    SCHEMA_DIR,
    canonical_capability_id,
    canonical_capability_key,
)
from pytest_bdd.model.message_baseline_diff import WEEKLY_CADENCE, build_baseline_diff
from pytest_bdd.model.message_capability_inventory import (
    reconcile_runtime_scope_coverage,
    sync_capability_inventory,
)
from pytest_bdd.model.message_converter import envelope_from_dict, governance_value_to_dict
from pytest_bdd.model.message_governance_checklist import build_governance_checklist, render_checklist_markdown
from pytest_bdd.model.message_status_governance import normalize_capability_status
from pytest_bdd.model.message_stream_validation import collect_observed_capability_ids, validate_message_stream
from pytest_bdd.script.message_capability_governance.capabilities import (
    _load_capabilities,
    _load_capabilities_from_governance_report,
    _load_capability_ids,
    _validate_runtime_required_scope,
    _validate_scope_capability_ids,
)
from pytest_bdd.script.message_capability_governance.decisions import (
    _load_baseline_diff,
    _load_decisions,
    _select_active_decisions,
    _validate_decisions,
)
from pytest_bdd.script.message_capability_governance.schema import (
    validate_governance_report_payload,
)

if TYPE_CHECKING:
    from pytest_bdd.model.message_status_governance import CapabilityDecision
    from pytest_bdd.types.json import JSONObject


def _emit_text(text: str, *, output_path: Path | None = None) -> None:
    if output_path is not None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(text, encoding="utf-8")
        return
    sys.stdout.write(text)
    if not text.endswith("\n"):
        sys.stdout.write("\n")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """
    Parse command-line arguments.

    Args:
        argv: Command-line arguments (defaults to sys.argv).

    Returns:
        Parsed arguments namespace.

    """
    parser = argparse.ArgumentParser(description="Manage message capability governance artifacts")
    subparsers = parser.add_subparsers(dest="command", required=True)

    sync_parser = subparsers.add_parser("sync", help="Sync capabilities from baseline")
    sync_parser.add_argument("--baseline-release", required=True)
    sync_parser.add_argument("--input", type=Path, required=True)
    sync_parser.add_argument("--output", type=Path)

    decision_parser = subparsers.add_parser("validate-decision", help="Validate one decision JSON file")
    decision_parser.add_argument("--input", type=Path, required=True)

    diff_parser = subparsers.add_parser("diff", help="Build baseline diff")
    diff_parser.add_argument("--previous-baseline", required=True)
    diff_parser.add_argument("--current-baseline", required=True)
    diff_parser.add_argument("--previous", type=Path)
    diff_parser.add_argument("--current", type=Path)
    diff_parser.add_argument("--previous-governance", type=Path)
    diff_parser.add_argument("--current-governance", type=Path)
    diff_parser.add_argument("--output", type=Path)

    checklist_parser = subparsers.add_parser("checklist", help="Render release governance checklist")
    checklist_parser.add_argument("--capabilities", type=Path, required=True)
    checklist_parser.add_argument("--decisions", type=Path, required=True)
    checklist_parser.add_argument("--baseline-diff", type=Path)
    checklist_parser.add_argument("--format", choices=("json", "markdown"), default="json")
    checklist_parser.add_argument("--output", type=Path)

    report_parser = subparsers.add_parser("report", help="Generate governance coverage report from NDJSON")
    report_parser.add_argument("--messages-file", type=Path, required=True)
    report_parser.add_argument("--output", type=Path)
    report_parser.add_argument("--format", choices=("json", "markdown"), default="json")
    report_parser.add_argument("--baseline-release", default="unknown")
    report_parser.add_argument("--schema", type=Path, default=None)
    report_parser.add_argument(
        "--decisions",
        type=Path,
        default=None,
        help="Optional JSON decisions file that classifies uncovered capabilities.",
    )
    report_parser.add_argument(
        "--mandatory-capabilities-file",
        type=Path,
        default=None,
        help="Optional newline-delimited governance scope capability list for release.",
    )
    report_parser.add_argument(
        "--runtime-required-capabilities-file",
        type=Path,
        default=None,
        help="Optional newline-delimited subset that must be runtime-observed.",
    )
    report_parser.add_argument(
        "--require-fully-governed",
        action="store_true",
        default=False,
        help="Fail if report contains blocked or pending capabilities after decision merge.",
    )
    report_parser.add_argument(
        "--require-runtime-required-covered",
        action="store_true",
        default=False,
        help="Fail if any capability from --runtime-required-capabilities-file is not runtime-observed.",
    )
    report_parser.add_argument(
        "--require-non-runtime-classified",
        action="store_true",
        default=False,
        help="Fail if non-runtime-required uncovered capabilities are missing explicit classification.",
    )

    # Legacy fallback for quickstart.md:
    if argv is None:
        argv = sys.argv[1:]

    if "--messages-file" in argv and "report" not in argv:
        argv.insert(0, "report")

    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:  # noqa: C901, PLR0911, PLR0912, PLR0914, PLR0915
    """
    Run the governance CLI.

    Args:
        argv: Command-line arguments.

    Returns:
        Exit code.

    Raises:
        ValueError: If the operation cannot be completed.

    """
    args = parse_args(argv)

    if args.command == "sync":
        capabilities = _load_capabilities(args.input)
        sync_result = sync_capability_inventory(args.baseline_release, capabilities)
        _emit_text(json.dumps(governance_value_to_dict(sync_result), sort_keys=True), output_path=args.output)
        return 0

    if args.command == "validate-decision":
        from pytest_bdd.model.message_status_governance import (
            validate_capability_decision,
        )

        decisions = _load_decisions(args.input)
        if len(decisions) != 1:
            msg = "validate-decision expects a single decision object in the JSON array"
            raise ValueError(msg)
        decision_result = validate_capability_decision(decisions[0])
        _emit_text(json.dumps(governance_value_to_dict(decision_result), sort_keys=True))
        return 0 if decision_result.accepted else 1

    if args.command == "diff":
        if args.previous is not None and args.current is not None:
            previous_capabilities = _load_capabilities(args.previous)
            current_capabilities = _load_capabilities(args.current)
        elif args.previous_governance is not None and args.current_governance is not None:
            previous_capabilities = _load_capabilities_from_governance_report(args.previous_governance)
            current_capabilities = _load_capabilities_from_governance_report(args.current_governance)
        else:
            msg = (
                "diff requires either --previous/--current capability files "
                "or --previous-governance/--current-governance governance files."
            )
            raise ValueError(msg)
        diff_result = build_baseline_diff(
            previous_baseline=args.previous_baseline,
            current_baseline=args.current_baseline,
            previous_capabilities=previous_capabilities,
            current_capabilities=current_capabilities,
            generated_at=datetime.now(timezone.utc),
        )
        payload = cast("JSONObject", governance_value_to_dict(diff_result))
        payload["cadence"] = WEEKLY_CADENCE
        _emit_text(json.dumps(payload, sort_keys=True), output_path=args.output)
        return 0

    if args.command == "checklist":
        capabilities = _load_capabilities(args.capabilities)
        decisions = _load_decisions(args.decisions)
        baseline_diff = _load_baseline_diff(args.baseline_diff) if args.baseline_diff is not None else None
        checklist = build_governance_checklist(capabilities, decisions, baseline_diff=baseline_diff)
        if args.format == "markdown":
            _emit_text(render_checklist_markdown(checklist), output_path=args.output)
        else:
            _emit_text(json.dumps(governance_value_to_dict(checklist), sort_keys=True), output_path=args.output)
        return 0 if checklist.unresolved_blockers == 0 else 1

    if args.command == "report":
        if args.require_runtime_required_covered and args.runtime_required_capabilities_file is None:
            msg = "--require-runtime-required-covered requires --runtime-required-capabilities-file"
            raise ValueError(msg)

        envelopes = []
        with Path(args.messages_file).open(encoding="utf-8") as f:
            for line in f:
                stripped_line = line.strip()
                if stripped_line:
                    envelopes.append(envelope_from_dict(json.loads(stripped_line)))

        validation_result = validate_message_stream(envelopes, track_coverage=True)
        observed_capability_ids = set(collect_observed_capability_ids(envelopes))
        # Runtime lookup to respect monkeypatching on the package namespace
        import pytest_bdd.script.message_capability_governance as _pkg

        inventory = _pkg.generate_inventory(SCHEMA_DIR)
        mandatory_capability_ids: set[str] = set()
        if args.mandatory_capabilities_file is not None:
            mandatory_capability_ids = _load_capability_ids(args.mandatory_capabilities_file)
        runtime_required_capability_ids: set[str] = set()
        if args.runtime_required_capabilities_file is not None:
            runtime_required_capability_ids = _load_capability_ids(args.runtime_required_capabilities_file)
        decisions_by_capability: dict[str, CapabilityDecision] = {}
        if args.decisions is not None:
            validated_decisions = _validate_decisions(
                _load_decisions(args.decisions),
                mandatory_capability_ids=runtime_required_capability_ids,
            )
            decisions_by_capability = _select_active_decisions(
                validated_decisions,
                release_target=args.baseline_release,
            )

        capabilities_list: list[JSONObject] = []
        implemented_count = 0
        blocked_count = 0
        deferred_count = 0
        runtime_required_missing_count = 0
        non_runtime_covered_count = 0
        non_runtime_classified_count = 0
        mandatory_scope_violations: list[str] = []
        now = datetime.now(timezone.utc).isoformat()

        inventory_capability_ids = {
            canonical_capability_id(f"{payload_kind}.{path}" if path else payload_kind)
            for payload_kind, path in inventory.fields
        }
        unknown_decision_ids = sorted(set(decisions_by_capability).difference(inventory_capability_ids))
        if unknown_decision_ids:
            sample = ", ".join(unknown_decision_ids[:10])
            msg = f"Decision file contains unknown capability IDs (first 10): {sample}"
            raise ValueError(msg)
        if mandatory_capability_ids:
            _validate_scope_capability_ids(
                mandatory_capability_ids,
                inventory_capability_ids,
                scope_name="Mandatory capability",
            )
        if runtime_required_capability_ids:
            _validate_scope_capability_ids(
                runtime_required_capability_ids,
                inventory_capability_ids,
                scope_name="Runtime-required capability",
            )
            _validate_runtime_required_scope(
                runtime_required_capability_ids=runtime_required_capability_ids,
                mandatory_capability_ids=mandatory_capability_ids,
            )

        runtime_scope_reconciliation = reconcile_runtime_scope_coverage(
            inventory_capability_ids=inventory_capability_ids,
            runtime_required_capability_ids=runtime_required_capability_ids,
            observed_capability_ids=observed_capability_ids,
            classified_capability_ids=tuple(decisions_by_capability.keys()),
        )

        for payload_kind, path in sorted(inventory.fields):
            canonical_payload_kind, canonical_path = canonical_capability_key(payload_kind, path)
            capability_id = f"{canonical_payload_kind}.{canonical_path}" if canonical_path else canonical_payload_kind
            observed_runtime = capability_id in observed_capability_ids
            mandatory_scope = capability_id in mandatory_capability_ids if mandatory_capability_ids else False
            runtime_required = capability_id in runtime_required_capability_ids
            decision = decisions_by_capability.get(capability_id)
            decision_status = normalize_capability_status(decision.status) if decision is not None else None
            if observed_runtime:
                if decision_status == "Non-Implementable":
                    msg = (
                        "Capability has runtime evidence but is marked Non-Implementable: "
                        f"{capability_id}. This is a governance validation error."
                    )
                    raise ValueError(msg)
                if decision_status == "Partly-Applicable":
                    status = "Partly-Applicable"
                    if runtime_required:
                        disposition = "blocked"
                        blocked_count += 1
                        runtime_required_missing_count += 1
                    else:
                        disposition = "deferred"
                        deferred_count += 1
                        non_runtime_classified_count += 1
                else:
                    status = "Implemented"
                    disposition = "approved"
                    implemented_count += 1
                    if not runtime_required:
                        non_runtime_covered_count += 1
            elif decision is not None:
                status = decision_status or "Pending"
                if runtime_required:
                    disposition = "blocked"
                    blocked_count += 1
                    runtime_required_missing_count += 1
                elif status in {"Partly-Applicable", "Non-Implementable", "Not-Applicable"}:
                    disposition = "deferred"
                    deferred_count += 1
                else:
                    disposition = "blocked"
                    blocked_count += 1
                if not runtime_required:
                    non_runtime_classified_count += 1
            else:
                status = "Pending"
                disposition = "blocked"
                blocked_count += 1
                if runtime_required:
                    runtime_required_missing_count += 1
            payload = {
                "capability_id": capability_id,
                "status": status,
                "disposition": disposition,
                "mandatory_scope": mandatory_scope,
                "runtime_required": runtime_required,
                "observed_runtime": observed_runtime,
            }
            if decision is not None:
                if decision.rationale is not None:
                    payload["rationale"] = decision.rationale
                if decision.hard_limitation is not None:
                    payload["hard_limitation"] = decision.hard_limitation
                if decision.decision_owner is not None:
                    payload["decision_owner"] = decision.decision_owner
                if decision.reviewed_at is not None:
                    payload["reviewed_at"] = decision.reviewed_at.isoformat()
                if decision.evidence_refs:
                    payload["evidence_refs"] = list(decision.evidence_refs)
                if decision.recheck_trigger is not None:
                    payload["recheck_trigger"] = decision.recheck_trigger
            elif status in {"Pending", "Non-Implementable", "Not-Applicable", "Not-Acceptable"}:
                payload["rationale"] = "Auto-generated pending classification due to missing runtime evidence"
                payload["decision_owner"] = "Automation"
                payload["reviewed_at"] = now
                payload["evidence_refs"] = [str(args.messages_file)]

            if status == "Pending":
                payload["open_risk"] = "Missing runtime evidence or unresolved governance decision"
            elif status == "Implemented" and not observed_runtime:
                payload["open_risk"] = "Marked implemented by decision but runtime evidence is missing"
            elif disposition == "blocked":
                payload["open_risk"] = (
                    decision.rationale
                    if decision is not None and decision.rationale
                    else "Unresolved governance decision"
                )

            if mandatory_scope and not observed_runtime and decision is None:
                mandatory_scope_violations.append(capability_id)
            capabilities_list.append(payload)

        total_capabilities = len(capabilities_list)
        coverage_percentage = (implemented_count / total_capabilities * 100) if total_capabilities else 0.0

        report = {
            "version": "1.1",
            "generated_at": now,
            "baseline_release": args.baseline_release,
            "summary": {
                "total_capabilities": total_capabilities,
                "implemented_capabilities": implemented_count,
                "blocked_capabilities": blocked_count,
                "deferred_capabilities": deferred_count,
                "coverage_percentage": coverage_percentage,
                "runtime_required_total": runtime_scope_reconciliation.runtime_required_total,
                "runtime_required_covered": runtime_scope_reconciliation.runtime_required_covered,
                "runtime_required_missing": runtime_required_missing_count,
                "non_runtime_required_total": runtime_scope_reconciliation.non_runtime_required_total,
                "non_runtime_covered": non_runtime_covered_count,
                "non_runtime_classified": non_runtime_classified_count,
                "mandatory_scope_violations": len(mandatory_scope_violations),
            },
            "capabilities": capabilities_list,
        }

        validate_governance_report_payload(report, schema_path=args.schema)

        if args.require_fully_governed:
            unresolved = [
                capability
                for capability in report["capabilities"]
                if capability["status"] == "Pending" or capability["disposition"] == "blocked"
            ]
            if unresolved:
                _emit_text(json.dumps(report, indent=2, sort_keys=True), output_path=args.output)
                return 1

        if args.require_runtime_required_covered and runtime_required_missing_count:
            _emit_text(json.dumps(report, indent=2, sort_keys=True), output_path=args.output)
            return 1

        if args.require_non_runtime_classified and runtime_scope_reconciliation.has_unclassified_non_runtime_gaps:
            _emit_text(json.dumps(report, indent=2, sort_keys=True), output_path=args.output)
            return 1

        if args.format == "markdown":
            lines = [
                "# Message Status Governance Checklist",
                "",
                (
                    "**Purpose**: Release-facing checklist for capability status governance "
                    "and message-to-status traceability."
                ),
                "**Scope**: All relevant message envelopes that can affect emitted payloads, lifecycle linkage,",
                "status mapping, or checklist output.",
                "",
                "## Message Inventory",
                "",
            ]

            observed_kinds = (
                {pk for pk, _ in validation_result.observed_coverage.observed_fields}
                if (validation_result.observed_coverage is not None)
                else set()
            )
            for payload_kind in inventory.payload_kinds:
                check = "X" if payload_kind in observed_kinds else " "
                lines.append(f"- [{check}] `{payload_kind}`")

            lines.extend(
                [
                    "",
                    "## Status Decision Matrix",
                    "",
                    (
                        "| Capability / Message | Status | Rationale | Decision Owner | Evidence Refs | "
                        "Reviewed At | Hook / Formation Point |"
                    ),
                    "|----------------------|--------|-----------|----------------|---------------|-------------|------------------------|",
                ],
            )

            for payload_kind in ["test_step_finished", "test_case_finished", "test_run_finished", "attachment"]:
                status = "Implemented" if payload_kind in observed_kinds else "Pending"
                lines.append(
                    f"| `{payload_kind}` outcome mapping | {status} | Automatically tracked | Automation | "
                    f"`tests/messages/` | {datetime.now(timezone.utc).date()} | Runtime |",
                )

            lines.extend(
                [
                    "",
                    "## Release Decision",
                    "",
                    (
                        f"- [{'X' if not runtime_scope_reconciliation.has_unclassified_non_runtime_gaps else ' '}] "
                        "No non-runtime-required capability is missing classification."
                    ),
                    (
                        "- [X] All `Partly-Applicable`, `Non-Implementable`, `Not-Acceptable`, "
                        "`Not-Applicable`, and `Pending` entries have"
                    ),
                    "      `rationale`, `decision_owner`, `evidence_refs`, and `reviewed_at`.",
                    (
                        f"- [{'X' if runtime_required_missing_count == 0 else ' '}] "
                        "Runtime-required capabilities are covered by runtime evidence."
                    ),
                ],
            )

            _emit_text("\n".join(lines) + "\n", output_path=args.output)
        else:
            _emit_text(json.dumps(report, indent=2, sort_keys=True), output_path=args.output)
        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
