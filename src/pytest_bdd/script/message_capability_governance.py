from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Final, cast

from jsonschema import validators

from pytest_bdd.model.coverage.inventory import (
    SCHEMA_DIR,
    canonical_capability_id,
    canonical_capability_key,
    generate_inventory,
)
from pytest_bdd.model.message_baseline_diff import WEEKLY_CADENCE, BaselineDiffRecord, build_baseline_diff
from pytest_bdd.model.message_capability import (
    CapabilityCategory,
    CapabilityImpact,
    CapabilityRelevance,
    MessageCapability,
)
from pytest_bdd.model.message_capability_inventory import (
    reconcile_inventory_with_mandatory_scope,
    reconcile_runtime_scope_coverage,
    sync_capability_inventory,
)
from pytest_bdd.model.message_converter import envelope_from_dict, governance_value_to_dict
from pytest_bdd.model.message_governance_checklist import build_governance_checklist, render_checklist_markdown
from pytest_bdd.model.message_status_governance import (
    CapabilityDecision,
    ensure_single_status_per_capability,
    normalize_capability_status,
    validate_capability_decision,
    validate_mandatory_scope_decision,
)
from pytest_bdd.model.message_validation import collect_observed_capability_ids, validate_message_stream

ALLOWED_CATEGORIES: Final[set[str]] = {"core", "lifecycle", "hook", "attachment", "parameter", "metadata"}
ALLOWED_IMPACTS: Final[set[str]] = {
    "emitted_envelope_payload",
    "lifecycle_linkage",
    "status_mapping",
    "governance_checklist_output",
}
ALLOWED_RELEVANCE: Final[set[str]] = {"relevant", "out_of_scope"}
DEFAULT_GOVERNANCE_SCHEMA_GLOB: Final[str] = "specs/*/contracts/governance-report.schema.json"
DEFAULT_GOVERNANCE_SCHEMA_RELATIVE_PATH: Final[Path] = Path(
    "specs/008-maximize-messages-coverage/contracts/governance-report.schema.json"
)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _candidate_repo_roots() -> tuple[Path, ...]:
    cwd = Path.cwd().resolve()
    repo_root = _repo_root().resolve()
    candidates: list[Path] = []
    seen: set[Path] = set()
    for base in (cwd, repo_root):
        for candidate in (base, *base.parents):
            if candidate not in seen:
                seen.add(candidate)
                candidates.append(candidate)
    return tuple(candidates)


def discover_governance_schema_path() -> Path | None:
    canonical_path = (_repo_root().resolve() / DEFAULT_GOVERNANCE_SCHEMA_RELATIVE_PATH).resolve()
    if canonical_path.exists():
        return canonical_path
    candidates: list[Path] = []
    for root in _candidate_repo_roots():
        candidates.extend(sorted(root.glob(DEFAULT_GOVERNANCE_SCHEMA_GLOB)))
    if not candidates:
        return None
    normalized_candidates = sorted({candidate.resolve() for candidate in candidates}, key=lambda path: str(path))
    return normalized_candidates[0]


def load_governance_report_schema(schema_path: Path | None = None) -> dict[str, Any]:
    effective_path = schema_path or discover_governance_schema_path()
    if effective_path is None:
        msg = "Unable to locate governance report schema."
        raise FileNotFoundError(msg)
    return cast(dict[str, Any], _load_json(effective_path))


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
    return cast(Any, json.loads(path.read_text(encoding="utf-8")))


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
                hard_limitation=item.get("hard_limitation"),
                decision_owner=item.get("decision_owner"),
                evidence_refs=tuple(item.get("evidence_refs") or []),
                reviewed_at=reviewed_at,
                release_target=str(item.get("release_target", "next-release")),
                recheck_trigger=item.get("recheck_trigger"),
            )
        )
    return result


def _validate_decisions(
    decisions: list[CapabilityDecision],
    *,
    mandatory_capability_ids: set[str] | None = None,
) -> list[CapabilityDecision]:
    canonical_decisions = [
        CapabilityDecision(
            capability_id=canonical_capability_id(decision.capability_id),
            status=decision.status,
            release_target=decision.release_target,
            rationale=decision.rationale,
            hard_limitation=decision.hard_limitation,
            decision_owner=decision.decision_owner,
            evidence_refs=decision.evidence_refs,
            reviewed_at=decision.reviewed_at,
            recheck_trigger=decision.recheck_trigger,
        )
        for decision in decisions
    ]

    uniqueness = ensure_single_status_per_capability(canonical_decisions)
    if not uniqueness.is_unique:
        msg = f"Duplicate capability decisions found for: {', '.join(uniqueness.duplicates)}"
        raise ValueError(msg)

    mandatory_ids = mandatory_capability_ids or set()
    validated: list[CapabilityDecision] = []
    for decision in canonical_decisions:
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
        mandatory_violations = validate_mandatory_scope_decision(
            decision,
            mandatory_capability_ids=mandatory_ids,
        )
        if mandatory_violations:
            msg = "; ".join(mandatory_violations)
            raise ValueError(msg)
        validated.append(decision)

    return validated


def _select_active_decisions(
    decisions: list[CapabilityDecision],
    *,
    release_target: str,
) -> dict[str, CapabilityDecision]:
    grouped: dict[str, list[CapabilityDecision]] = {}
    for decision in decisions:
        grouped.setdefault(decision.capability_id, []).append(decision)

    active: dict[str, CapabilityDecision] = {}
    for capability_id, candidates in grouped.items():
        exact = [decision for decision in candidates if decision.release_target == release_target]
        if exact:
            active[capability_id] = exact[0]
            continue

        next_release = [decision for decision in candidates if decision.release_target == "next-release"]
        if next_release:
            active[capability_id] = next_release[0]
            continue

        active[capability_id] = max(
            candidates,
            key=lambda decision: (
                decision.reviewed_at.isoformat() if decision.reviewed_at is not None else "",
                decision.release_target,
            ),
        )
    return active


def _load_capability_ids(path: Path) -> set[str]:
    capability_ids: set[str] = set()
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        capability_ids.add(canonical_capability_id(line))
    return capability_ids


def _validate_scope_capability_ids(
    capability_ids: set[str],
    inventory_capability_ids: set[str],
    *,
    scope_name: str,
) -> None:
    reconciliation = reconcile_inventory_with_mandatory_scope(
        inventory_capability_ids=inventory_capability_ids,
        mandatory_capability_ids=capability_ids,
    )
    unknown_ids = list(reconciliation.missing_mandatory_capability_ids)
    if unknown_ids:
        sample = ", ".join(unknown_ids[:10])
        msg = f"{scope_name} file contains unknown capability IDs (first 10): {sample}"
        raise ValueError(msg)


def _validate_runtime_required_scope(
    *,
    runtime_required_capability_ids: set[str],
    mandatory_capability_ids: set[str],
) -> None:
    if not mandatory_capability_ids:
        return
    out_of_scope = sorted(set(runtime_required_capability_ids).difference(mandatory_capability_ids))
    if out_of_scope:
        sample = ", ".join(out_of_scope[:10])
        msg = f"runtime-required capability file contains IDs outside mandatory scope (first 10): {sample}"
        raise ValueError(msg)


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
        if args.require_runtime_required_covered and args.runtime_required_capabilities_file is None:
            msg = "--require-runtime-required-covered requires --runtime-required-capabilities-file"
            raise ValueError(msg)

        envelopes = []
        with Path(args.messages_file).open(encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    envelopes.append(envelope_from_dict(json.loads(line)))

        validation_result = validate_message_stream(envelopes, track_coverage=True)
        observed_capability_ids = set(collect_observed_capability_ids(envelopes))
        inventory = generate_inventory(SCHEMA_DIR)
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

        capabilities_list: list[dict[str, Any]] = []
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
                "**Purpose**: Release-facing checklist for capability status governance and message-to-status traceability.",
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
                    f"- [{'X' if not runtime_scope_reconciliation.has_unclassified_non_runtime_gaps else ' '}] No non-runtime-required capability is missing classification.",
                    "- [X] All `Partly-Applicable`, `Non-Implementable`, `Not-Acceptable`, `Not-Applicable`, and `Pending` entries have",
                    "      `rationale`, `decision_owner`, `evidence_refs`, and `reviewed_at`.",
                    f"- [{'X' if runtime_required_missing_count == 0 else ' '}] Runtime-required capabilities are covered by runtime evidence.",
                ]
            )

            _emit_text("\n".join(lines) + "\n", output_path=args.output)
        else:
            _emit_text(json.dumps(report, indent=2, sort_keys=True), output_path=args.output)
        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
