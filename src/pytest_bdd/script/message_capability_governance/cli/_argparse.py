"""
Argument parsing for message capability governance CLI.

Responsibility:
    Argument parsing for message capability governance CLI. It directly owns the observable contract, local decisions,
    and maintenance boundary for this module.

Reason for existence:
    This entity is the information expert for `pytest_bdd.script.message_capability_governance.cli._argparse` because it
    keeps the nearest code, data shape, call signature, and failure knowledge together.

Delegates:
    - parse_args: owns nested behavior below this boundary

Cohesion:
    The implementation stays together because its imports, calls, state writes, and return contract describe one
    maintainable decision unit.

Separation:
    - module peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
      widening caller knowledge.

Main consumers:
    - src/pytest_bdd/script/message_capability_governance/cli/_core.py: imports or references `_argparse`
    - src/pytest_bdd/script/message_capability_governance/cli/facade.py: imports or references `_argparse`

State and side effects:
    mutates parser, subparsers, sync_parser, decision_parser, diff_parser; depends on __future__.annotations, argparse,
    sys, pathlib.Path.

Invariants:
    - `pytest_bdd.script.message_capability_governance.cli._argparse` keeps its documented import path, ownership
      boundary, and observable behavior stable for callers.

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

import argparse
import sys
from pathlib import Path


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """
    Parse command-line arguments.

    Args:
        argv: Command-line arguments (defaults to sys.argv).

    Returns:
        Parsed arguments namespace.

    Responsibility:
        Parse command-line arguments. It directly owns the observable contract, local decisions, and maintenance
        boundary for this function. That boundary is intentionally stated in prose so maintainers can distinguish owned
        work from collaborators before editing.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.script.message_capability_governance.cli._argparse.parse_args` because it keeps the nearest code,
        data shape, call signature, and failure knowledge together.

    Delegates:
        - report_parser.add_argument: collaborator call used by this boundary
        - diff_parser.add_argument: collaborator call used by this boundary
        - subparsers.add_parser: collaborator call used by this boundary
        - checklist_parser.add_argument: collaborator call used by this boundary
        - sync_parser.add_argument: collaborator call used by this boundary
        - argparse.ArgumentParser: collaborator call used by this boundary

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
        mutates parser, subparsers, sync_parser, decision_parser, diff_parser.

    Invariants:
        - `pytest_bdd.script.message_capability_governance.cli._argparse.parse_args` keeps its documented import path,
          ownership boundary, and observable behavior stable for callers.

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
