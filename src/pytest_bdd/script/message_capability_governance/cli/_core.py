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

import json
from datetime import datetime, timezone
from typing import cast

from pytest_bdd.model.message_baseline_diff import WEEKLY_CADENCE, build_baseline_diff
from pytest_bdd.model.message_capability_inventory import sync_capability_inventory
from pytest_bdd.model.message_converter import governance_value_to_dict
from pytest_bdd.model.message_governance_checklist import build_governance_checklist, render_checklist_markdown
from pytest_bdd.script.message_capability_governance.capabilities import (
    _load_capabilities,
    _load_capabilities_from_governance_report,
)
from pytest_bdd.script.message_capability_governance.cli._argparse import parse_args
from pytest_bdd.script.message_capability_governance.cli._report import _handle_report
from pytest_bdd.script.message_capability_governance.cli._utils import _emit_text
from pytest_bdd.script.message_capability_governance.decisions import (
    _load_baseline_diff,
    _load_decisions,
)
from pytest_bdd.types.json import JSONObject


def main(argv: list[str] | None = None) -> int:
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
        return _handle_report(args)

    return 1
