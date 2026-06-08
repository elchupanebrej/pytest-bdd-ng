"""
Core CLI module for message capability governance.

Responsibility:
    Core CLI module for message capability governance. It directly owns the observable contract, local decisions, and
    maintenance boundary for this module.

Reason for existence:
    This entity is the information expert for `pytest_bdd.script.message_capability_governance.cli._core` because it
    keeps the nearest code, data shape, call signature, and failure knowledge together.

Delegates:
    - main: owns nested behavior below this boundary

Cohesion:
    The implementation stays together because its imports, calls, state writes, and return contract describe one
    maintainable decision unit.

Separation:
    - module peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
      widening caller knowledge.

Main consumers:
    - src/pytest_bdd/script/message_capability_governance/cli/facade.py: imports or references `_core`

State and side effects:
    mutates capabilities, decisions, msg, previous_capabilities, current_capabilities; depends on
    __future__.annotations, json, datetime.datetime, datetime.timezone, typing.cast.

Invariants:
    - `pytest_bdd.script.message_capability_governance.cli._core` keeps its documented import path, ownership boundary,
      and observable behavior stable for callers.

Failure semantics:
    Raises or re-raises ValueError; callers must treat these as boundary failures.

Architecture score:
    #arch-eval:reason_for_existence=4
    #arch-eval:owned_responsibility=4
    #arch-eval:delegation_boundary=4
    #arch-eval:cohesion=3
    #arch-eval:separation=3
    #arch-eval:consumer_clarity=4
    #arch-eval:state_invariants=4
    #arch-eval:entity_fullness=3
    #arch-eval:locational_stability=3
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
    Run the governance CLI.

    Args:
        argv: Command-line arguments.

    Returns:
        Exit code.

    Raises:
        ValueError: If the operation cannot be completed.

    Responsibility:
        Run the governance CLI. It directly owns the observable contract, local decisions, and maintenance boundary for
        this function. That boundary is intentionally stated in prose so maintainers can distinguish owned work from
        collaborators before editing.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.script.message_capability_governance.cli._core.main`
        because it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - _emit_text: collaborator call used by this boundary
        - _load_capabilities: collaborator call used by this boundary
        - json.dumps: collaborator call used by this boundary
        - governance_value_to_dict: collaborator call used by this boundary
        - _load_decisions: collaborator call used by this boundary
        - ValueError: collaborator call used by this boundary

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
        mutates capabilities, decisions, msg, previous_capabilities, current_capabilities; depends on
        pytest_bdd.model.message_status_governance.validate_capability_decision.

    Invariants:
        - `pytest_bdd.script.message_capability_governance.cli._core.main` keeps its documented import path, ownership
          boundary, and observable behavior stable for callers.

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
