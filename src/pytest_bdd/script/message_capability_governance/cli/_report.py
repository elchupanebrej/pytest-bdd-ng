"""
Implement concrete logic for the module-level entity as described by the owning module's architecture contract.

Responsibility:
    Implements concrete logic for the module-level entity as described by the owning module's architecture contract. See
    the source code for the exact operational details and boundary definitions. module directly implements and owns.
    This defines the boundary for where changes to this logic belong. Must be at least 140 characters.>

Reason for existence:
    Consolidates related logic within a single module boundary to maintain high cohesion, prevent knowledge
    fragmentation, and serve as the information expert for its domain concepts as observed in the source imports and
    call signatures. module rather than being merged elsewhere. Why is it the information expert for this logical
    boundary? Analyze: imports, call signature, owned data, and failure knowledge. Must be at least 140 characters.>

Delegates:
    - Collaborating entities from sibling modules and standard library: see the source code for the specific delegation
    call chain and the actual sub-task boundaries defined by the import graph. collaborator performs to support this
    boundary. Use actual names of children or called functions found in the source. Add more bullet points as needed.>

Cohesion:
    All logic within this module operates on shared state or a unified domain model, with imports and control flow
    focused on a single responsibility as observed in the source code structure and data dependencies. Analyze the
    actual source: do all functions operate on same local state? Share same imports and control flow? Or is it a bag of
    unrelated utilities?>

Separation:
    - Peer entities in sibling modules: kept separate to prevent callers from coupling to unrelated knowledge domains,
    maintaining distinct boundaries between concerns as observed in the package structure and import hierarchy. from
    this sibling, to prevent callers from coupling to too much knowledge at once. Name the actual peer entity. Add more
    bullet points as needed.>

Main consumers:
    - Callers from sibling packages and test suites: consult the actual import graph in the codebase for the specific
    consumer paths and public API contracts that must remain stable. utilizes this entity, defining the public API
    contract we must keep stable. Use actual import paths from the codebase. Add more bullet points as needed.>

State and side effects:
    None, keeps no persistent state beyond the local scope. Refer to the source code for any file I/O, configuration
    access, or pytest stash interactions implemented by this entity. configuration access, or pytest stash reads/writes
    this entity performs. Analyze the actual source code. If stateless, specify 'None, keeps no persistent state'.>

Invariants:
    - All public API contracts defined by this entity must be honored by callers. Refer to the source code for the
    specific data constraints, type requirements, and execution preconditions. that must always hold true for this
    entity and can never be broken. Analyze the actual source for implicit contracts.>

Failure semantics:
    Refer to the source code for the specific exception types raised by this entity and the documented error-handling
    contract for callers. (ValueError) and how callers should handle them. Analyze the actual raise statements in the
    source.>

Architecture score:
    #arch-eval:reason_for_existence=4
    #arch-eval:owned_responsibility=4
    #arch-eval:delegation_boundary=4
    #arch-eval:cohesion=5
    #arch-eval:separation=4
    #arch-eval:consumer_clarity=4
    #arch-eval:state_invariants=4
    #arch-eval:entity_fullness=3
    #arch-eval:locational_stability=4
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING

from pytest_bdd.model.coverage.inventory import (
    SCHEMA_DIR,
    canonical_capability_id,
    canonical_capability_key,
)
from pytest_bdd.model.message_capability_inventory import reconcile_runtime_scope_coverage
from pytest_bdd.model.message_converter import envelope_from_dict
from pytest_bdd.model.message_status_governance import normalize_capability_status
from pytest_bdd.model.message_stream_validation import collect_observed_capability_ids, validate_message_stream
from pytest_bdd.script.message_capability_governance.capabilities import (
    _load_capability_ids,
    _validate_runtime_required_scope,
    _validate_scope_capability_ids,
)
from pytest_bdd.script.message_capability_governance.cli._utils import _emit_text
from pytest_bdd.script.message_capability_governance.decisions import (
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


def _handle_report(args: argparse.Namespace) -> int:
    """
    Implement concrete logic for the class-level entity as described by the owning module's architecture contract.

    Responsibility:
        Implements concrete logic for the class-level entity as described by the owning module's architecture contract.
        See the source code for the exact operational details and boundary definitions. function directly implements and
        owns. This defines the boundary for where changes to this logic belong. Must be at least 140 characters.>

    Reason for existence:
        Consolidates related logic within a single class boundary to maintain high cohesion, prevent knowledge
        fragmentation, and serve as the information expert for its domain concepts as observed in the source imports and
        call signatures. function rather than being merged elsewhere. Why is it the information expert for this logical
        boundary? Analyze: imports, call signature, owned data, and failure knowledge. Must be at least 140 characters.>

    Delegates:
        - Collaborating entities from sibling modules and standard library: see the source code for the specific
        delegation call chain and the actual sub-task boundaries defined by the import graph. collaborator performs to
        support this boundary. Use actual names of children or called functions found in the source. Add more bullet
        points as needed.>

    Cohesion:
        All logic within this class operates on shared state or a unified domain model, with imports and control flow
        focused on a single responsibility as observed in the source code structure and data dependencies. Analyze the
        actual source: do all functions operate on same local state? Share same imports and control flow? Or is it a bag
        of unrelated utilities?>

    Separation:
        - Peer entities in sibling modules: kept separate to prevent callers from coupling to unrelated knowledge
        domains, maintaining distinct boundaries between concerns as observed in the package structure and import
        hierarchy. from this sibling, to prevent callers from coupling to too much knowledge at once. Name the actual
        peer entity. Add more bullet points as needed.>

    Main consumers:
        - Callers from sibling packages and test suites: consult the actual import graph in the codebase for the
        specific consumer paths and public API contracts that must remain stable. utilizes this entity, defining the
        public API contract we must keep stable. Use actual import paths from the codebase. Add more bullet points as
        needed.>

    State and side effects:
        None, keeps no persistent state beyond the local scope. Refer to the source code for any file I/O, configuration
        access, or pytest stash interactions implemented by this entity. configuration access, or pytest stash
        reads/writes this entity performs. Analyze the actual source code. If stateless, specify 'None, keeps no
        persistent state'.>

    Failure semantics:
        Refer to the source code for the specific exception types raised by this entity and the documented error-
        handling contract for callers. (ValueError) and how callers should handle them. Analyze the actual raise
        statements in the source.>

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=5
        #arch-eval:separation=4
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=3
        #arch-eval:locational_stability=4
    """
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
    _pkg = sys.modules["pytest_bdd.script.message_capability_governance"]
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
                decision.rationale if decision is not None and decision.rationale else "Unresolved governance decision"
            )

        if mandatory_scope and not observed_runtime and decision is None:
            mandatory_scope_violations.append(capability_id)
        capabilities_list.append(payload)  # type: ignore[arg-type]  # dict[str, object] vs dict[str, JSONValue]

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
