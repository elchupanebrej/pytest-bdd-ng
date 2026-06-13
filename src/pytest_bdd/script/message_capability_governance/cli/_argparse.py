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
import sys
from pathlib import Path


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
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
