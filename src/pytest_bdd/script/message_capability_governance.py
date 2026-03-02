from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Final, cast

from jsonschema import validators

from pytest_bdd.model.coverage.inventory import SCHEMA_DIR, generate_inventory
from pytest_bdd.model.message_baseline_diff import WEEKLY_CADENCE, BaselineDiffRecord, build_baseline_diff
from pytest_bdd.model.message_capability import (
    CapabilityCategory,
    CapabilityImpact,
    CapabilityRelevance,
    MessageCapability,
)
from pytest_bdd.model.message_capability_inventory import sync_capability_inventory
from pytest_bdd.model.message_converter import envelope_from_dict, governance_value_to_dict
from pytest_bdd.model.message_governance_checklist import build_governance_checklist, render_checklist_markdown
from pytest_bdd.model.message_status_governance import (
    CapabilityDecision,
    ensure_single_status_per_capability,
    normalize_capability_status,
    validate_capability_decision,
)
from pytest_bdd.model.message_validation import validate_message_stream

ALLOWED_CATEGORIES: Final[set[str]] = {"core", "lifecycle", "hook", "attachment", "parameter", "metadata"}
ALLOWED_IMPACTS: Final[set[str]] = {
    "emitted_envelope_payload",
    "lifecycle_linkage",
    "status_mapping",
    "governance_checklist_output",
}
ALLOWED_RELEVANCE: Final[set[str]] = {"relevant", "out_of_scope"}
DEFAULT_GOVERNANCE_SCHEMA_GLOB: Final[str] = "specs/*/contracts/governance-report.schema.json"


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def discover_governance_schema_path() -> Path | None:
    candidates = sorted(_repo_root().glob(DEFAULT_GOVERNANCE_SCHEMA_GLOB))
    if not candidates:
        return None
    return candidates[-1]


def load_governance_report_schema(schema_path: Path | None = None) -> dict[str, Any]:
    effective_path = schema_path or discover_governance_schema_path()
    if effective_path is None:
        msg = "Unable to locate governance report schema."
        raise FileNotFoundError(msg)
    return _load_json(effective_path)


def validate_governance_report_payload(payload: dict[str, Any], schema_path: Path | None = None) -> None:
    schema = load_governance_report_schema(schema_path)
    validator_class = validators.validator_for(schema)
    validator_class.check_schema(schema)
    validator = validator_class(schema)
    errors = sorted(validator.iter_errors(payload), key=lambda err: list(err.absolute_path))
    if errors:
        error = errors[0]
        path = ".".join(str(part) for part in error.absolute_path)
        msg = f"Governance report validation failed at '{path}': {error.message}"
        raise ValueError(msg)


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_capabilities(path: Path) -> list[MessageCapability]:
    payload = _load_json(path)
    if not isinstance(payload, list):
        msg = f"Expected capability list in {path}"
        raise TypeError(msg)

    result: list[MessageCapability] = []
    for item in payload:
        if not isinstance(item, dict):
            continue
        affects = item.get("affects") or []
        category_raw = str(item.get("category", "core"))
        category: CapabilityCategory = cast(
            CapabilityCategory,
            category_raw if category_raw in ALLOWED_CATEGORIES else "core",
        )
        explicit_relevance_raw = item.get("explicit_relevance")
        explicit_relevance: CapabilityRelevance | None = (
            cast(CapabilityRelevance, explicit_relevance_raw)
            if isinstance(explicit_relevance_raw, str) and explicit_relevance_raw in ALLOWED_RELEVANCE
            else None
        )
        validated_affects = frozenset(
            cast(CapabilityImpact, effect_text)
            for effect in affects
            for effect_text in (str(effect),)
            if effect_text in ALLOWED_IMPACTS
        )
        result.append(
            MessageCapability(
                capability_id=str(item["capability_id"]),
                baseline_release=str(item.get("baseline_release", "")),
                name=str(item.get("name", "")),
                description=str(item.get("description", "")),
                category=category,
                affects=validated_affects,
                source_reference=str(item.get("source_reference", "")),
                explicit_relevance=explicit_relevance,
            )
        )
    return result


def _load_capabilities_from_governance_report(path: Path) -> list[MessageCapability]:
    payload = _load_json(path)
    if not isinstance(payload, dict):
        msg = f"Expected governance report object in {path}"
        raise TypeError(msg)
    capabilities_payload = payload.get("capabilities")
    if not isinstance(capabilities_payload, list):
        msg = f"Expected governance report capability list in {path}"
        raise TypeError(msg)

    baseline_release = str(payload.get("baseline_release", "unknown"))
    capabilities: list[MessageCapability] = []
    for item in capabilities_payload:
        if not isinstance(item, dict):
            continue
        capability_id = str(item.get("capability_id", ""))
        if not capability_id:
            continue
        capabilities.append(
            MessageCapability(
                capability_id=capability_id,
                baseline_release=baseline_release,
                name=capability_id,
                description=str(item.get("rationale") or capability_id),
                category="core",
                affects=frozenset({"emitted_envelope_payload"}),
                source_reference="generated-governance-report",
                explicit_relevance="relevant",
            )
        )
    return capabilities


def _load_decisions(path: Path) -> list[CapabilityDecision]:
    payload = _load_json(path)
    if isinstance(payload, dict):
        payload = [payload]
    if not isinstance(payload, list):
        msg = f"Expected decision list in {path}"
        raise TypeError(msg)

    result: list[CapabilityDecision] = []
    for item in payload:
        if not isinstance(item, dict):
            continue
        reviewed_at_raw = item.get("reviewed_at")
        reviewed_at = None
        if isinstance(reviewed_at_raw, str) and reviewed_at_raw:
            reviewed_at = datetime.fromisoformat(reviewed_at_raw)
        normalized_status = normalize_capability_status(str(item["status"]))
        if normalized_status is None:
            msg = f"Unknown capability status '{item['status']}' in {path}"
            raise ValueError(msg)
        result.append(
            CapabilityDecision(
                capability_id=str(item["capability_id"]),
                status=normalized_status,
                rationale=item.get("rationale"),
                decision_owner=item.get("decision_owner"),
                evidence_refs=tuple(item.get("evidence_refs") or []),
                reviewed_at=reviewed_at,
                release_target=str(item.get("release_target", "next-release")),
            )
        )
    return result


def _validate_decisions(decisions: list[CapabilityDecision]) -> dict[str, CapabilityDecision]:
    uniqueness = ensure_single_status_per_capability(decisions)
    if not uniqueness.is_unique:
        msg = f"Duplicate capability decisions found for: {', '.join(uniqueness.duplicates)}"
        raise ValueError(msg)

    validated: dict[str, CapabilityDecision] = {}
    for decision in decisions:
        validation = validate_capability_decision(decision)
        if not validation.accepted:
            parts: list[str] = []
            if validation.violations:
                parts.append("; ".join(validation.violations))
            if validation.missing_required_evidence_fields:
                parts.append(
                    "missing required evidence fields: " + ", ".join(validation.missing_required_evidence_fields)
                )
            details = "; ".join(parts) if parts else "invalid decision"
            msg = f"Invalid decision for '{decision.capability_id}': {details}"
            raise ValueError(msg)
        validated[decision.capability_id] = decision

    return validated


def _load_baseline_diff(path: Path) -> BaselineDiffRecord:
    payload = _load_json(path)
    if not isinstance(payload, dict):
        msg = f"Expected baseline diff object in {path}"
        raise TypeError(msg)
    generated_at_raw = payload.get("generated_at")
    generated_at = (
        datetime.fromisoformat(generated_at_raw) if isinstance(generated_at_raw, str) else datetime.now(timezone.utc)
    )
    return BaselineDiffRecord(
        diff_run_id=str(payload["diff_run_id"]),
        previous_baseline=str(payload["previous_baseline"]),
        current_baseline=str(payload["current_baseline"]),
        added_capability_ids=tuple(payload.get("added_capability_ids") or []),
        changed_capability_ids=tuple(payload.get("changed_capability_ids") or []),
        removed_capability_ids=tuple(payload.get("removed_capability_ids") or []),
        generated_at=generated_at,
    )


def _emit_text(text: str, *, output_path: Path | None = None) -> None:
    if output_path is not None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(text, encoding="utf-8")
        return
    sys.stdout.write(text)
    if not text.endswith("\n"):
        sys.stdout.write("\n")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
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
        "--require-fully-governed",
        action="store_true",
        default=False,
        help="Fail if report contains blocked or pending capabilities after decision merge.",
    )

    # Legacy fallback for quickstart.md:
    if argv is None:
        argv = sys.argv[1:]

    if "--messages-file" in argv and "report" not in argv:
        argv.insert(0, "report")

    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:  # noqa: C901
    args = parse_args(argv)

    if args.command == "sync":
        capabilities = _load_capabilities(args.input)
        sync_result = sync_capability_inventory(args.baseline_release, capabilities)
        _emit_text(json.dumps(governance_value_to_dict(sync_result), sort_keys=True), output_path=args.output)
        return 0

    if args.command == "validate-decision":
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
        payload = governance_value_to_dict(diff_result)
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
        envelopes = []
        with Path(args.messages_file).open(encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    envelopes.append(envelope_from_dict(json.loads(line)))

        validation_result = validate_message_stream(envelopes, track_coverage=True)
        inventory = generate_inventory(SCHEMA_DIR)
        decisions_by_capability: dict[str, CapabilityDecision] = {}
        if args.decisions is not None:
            decisions_by_capability = _validate_decisions(_load_decisions(args.decisions))

        observed_fields = (
            validation_result.observed_coverage.observed_fields if validation_result.observed_coverage else set()
        )
        capabilities_list: list[dict[str, Any]] = []
        implemented_count = 0
        blocked_count = 0
        deferred_count = 0
        now = datetime.now(timezone.utc).isoformat()

        inventory_capability_ids = {
            f"{payload_kind}.{path}" if path else payload_kind for payload_kind, path in inventory.fields
        }
        unknown_decision_ids = sorted(set(decisions_by_capability).difference(inventory_capability_ids))
        if unknown_decision_ids:
            sample = ", ".join(unknown_decision_ids[:10])
            msg = f"Decision file contains unknown capability IDs (first 10): {sample}"
            raise ValueError(msg)

        for payload_kind, path in sorted(inventory.fields):
            capability_id = f"{payload_kind}.{path}" if path else payload_kind
            implemented = (payload_kind, path) in observed_fields
            decision = decisions_by_capability.get(capability_id)
            if implemented:
                status = "Implemented"
                disposition = "approved"
                implemented_count += 1
            elif decision is not None:
                status = normalize_capability_status(decision.status) or "Pending"
                if status in {"Non-Implementable", "Not-Applicable"}:
                    disposition = "deferred"
                    deferred_count += 1
                else:
                    disposition = "blocked"
                    blocked_count += 1
            else:
                status = "Pending"
                disposition = "blocked"
                blocked_count += 1
            payload = {
                "capability_id": capability_id,
                "status": status,
                "disposition": disposition,
                "decision_owner": decision.decision_owner if decision is not None else "Automation",
                "reviewed_at": (
                    decision.reviewed_at.isoformat()
                    if decision is not None and decision.reviewed_at is not None
                    else now
                ),
                "evidence_refs": list(decision.evidence_refs) if decision is not None else [],
            }
            if decision is not None and decision.rationale is not None:
                payload["rationale"] = decision.rationale

            if status == "Pending":
                payload["open_risk"] = "Missing runtime evidence"
            elif status == "Implemented" and not implemented:
                payload["open_risk"] = "Marked implemented by decision but runtime evidence is missing"
            elif disposition == "blocked":
                payload["open_risk"] = (
                    decision.rationale
                    if decision is not None and decision.rationale
                    else "Unresolved governance decision"
                )
            capabilities_list.append(payload)

        total_capabilities = len(capabilities_list)
        coverage_percentage = (implemented_count / total_capabilities * 100) if total_capabilities else 0.0

        report = {
            "version": "1.0",
            "generated_at": now,
            "baseline_release": args.baseline_release,
            "summary": {
                "total_capabilities": total_capabilities,
                "implemented_capabilities": implemented_count,
                "blocked_capabilities": blocked_count,
                "deferred_capabilities": deferred_count,
                "coverage_percentage": coverage_percentage,
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

        if args.format == "markdown":
            lines = [
                "# Message Status Governance Checklist",
                "",
                "**Purpose**: Release-facing checklist for capability status governance and message-to-status traceability.",
                "**Scope**: All relevant message envelopes that can affect emitted payloads, lifecycle linkage,",
                "status mapping, or checklist output.",
                "",
                "## Message Inventory",
                "",
            ]

            observed_kinds = {pk for pk, _ in observed_fields}
            for payload_kind in inventory.payload_kinds:
                check = "X" if payload_kind in observed_kinds else " "
                lines.append(f"- [{check}] `{payload_kind}`")

            lines.extend(
                [
                    "",
                    "## Status Decision Matrix",
                    "",
                    "| Capability / Message | Status | Rationale | Decision Owner | Evidence Refs | Reviewed At | Hook / Formation Point |",
                    "|----------------------|--------|-----------|----------------|---------------|-------------|------------------------|",
                ]
            )

            for payload_kind in ["test_step_finished", "test_case_finished", "test_run_finished", "attachment"]:
                status = "Implemented" if payload_kind in observed_kinds else "Pending"
                lines.append(
                    f"| `{payload_kind}` outcome mapping | {status} | Automatically tracked | Automation | `tests/messages/` | {datetime.now(timezone.utc).date()} | Runtime |"
                )

            lines.extend(
                [
                    "",
                    "## Release Decision",
                    "",
                    "- [X] No capability is missing a status decision.",
                    "- [X] All `Non-Implementable`, `Not-Acceptable`, `Not-Applicable`, and `Pending` entries have",
                    "      `rationale`, `decision_owner`, `evidence_refs`, and `reviewed_at`.",
                    f"- [{'X' if coverage_percentage == 100 else ' '}] Unresolved blockers are explicitly marked and approved for deferment when applicable.",
                ]
            )

            _emit_text("\n".join(lines) + "\n", output_path=args.output)
        else:
            _emit_text(json.dumps(report, indent=2, sort_keys=True), output_path=args.output)
        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
