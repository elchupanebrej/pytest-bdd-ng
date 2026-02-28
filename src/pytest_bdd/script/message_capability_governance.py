from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Final, cast

from pytest_bdd.model.message_baseline_diff import WEEKLY_CADENCE, BaselineDiffRecord, build_baseline_diff
from pytest_bdd.model.message_capability import (
    CapabilityCategory,
    CapabilityImpact,
    CapabilityRelevance,
    MessageCapability,
)
from pytest_bdd.model.message_capability_inventory import sync_capability_inventory
from pytest_bdd.model.message_converter import governance_value_to_dict
from pytest_bdd.model.message_governance_checklist import build_governance_checklist, render_checklist_markdown
from pytest_bdd.model.message_status_governance import (
    CapabilityDecision,
    normalize_capability_status,
    validate_capability_decision,
)

ALLOWED_CATEGORIES: Final[set[str]] = {"core", "lifecycle", "hook", "attachment", "parameter", "metadata"}
ALLOWED_IMPACTS: Final[set[str]] = {
    "emitted_envelope_payload",
    "lifecycle_linkage",
    "status_mapping",
    "governance_checklist_output",
}
ALLOWED_RELEVANCE: Final[set[str]] = {"relevant", "out_of_scope"}


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


def _load_baseline_diff(path: Path) -> BaselineDiffRecord:
    payload = _load_json(path)
    if not isinstance(payload, dict):
        msg = f"Expected baseline diff object in {path}"
        raise TypeError(msg)
    generated_at_raw = payload.get("generated_at")
    generated_at = datetime.fromisoformat(generated_at_raw) if isinstance(generated_at_raw, str) else datetime.now(UTC)
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
    diff_parser.add_argument("--previous", type=Path, required=True)
    diff_parser.add_argument("--current", type=Path, required=True)

    checklist_parser = subparsers.add_parser("checklist", help="Render release governance checklist")
    checklist_parser.add_argument("--capabilities", type=Path, required=True)
    checklist_parser.add_argument("--decisions", type=Path, required=True)
    checklist_parser.add_argument("--baseline-diff", type=Path)
    checklist_parser.add_argument("--format", choices=("json", "markdown"), default="json")
    checklist_parser.add_argument("--output", type=Path)

    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
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
        previous_capabilities = _load_capabilities(args.previous)
        current_capabilities = _load_capabilities(args.current)
        diff_result = build_baseline_diff(
            previous_baseline=args.previous_baseline,
            current_baseline=args.current_baseline,
            previous_capabilities=previous_capabilities,
            current_capabilities=current_capabilities,
            generated_at=datetime.now(UTC),
        )
        payload = governance_value_to_dict(diff_result)
        payload["cadence"] = WEEKLY_CADENCE
        _emit_text(json.dumps(payload, sort_keys=True))
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

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
