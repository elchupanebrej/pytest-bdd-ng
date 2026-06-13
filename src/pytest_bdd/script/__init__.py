"""
Provide the public entry point for the `message_capability_governance` CLI tooling, re-exporting `main` so callers c.

Responsibility:
    Provides the public entry point for the `message_capability_governance` CLI tooling, re-exporting `main` so callers
    can invoke governance workflows via `pytest_bdd.script.message_capability_governance_main`.>

Reason for existence:
    Exists as a thin public facade over the `message_capability_governance` sub-package to give consumers a stable,
    short import path for the governance CLI entry point without coupling them to the internal sub-package layout.>

Delegates:
    - `message_capability_governance.main`: The actual CLI entry point that dispatches subcommands (sync, validate-
    decision, diff, checklist, report) and owns all argument parsing and execution logic.>

Cohesion:
    This module contains only the governance CLI re-export. It is intentionally minimal to avoid polluting the
    `pytest_bdd.script` namespace with internal governance concerns that belong to the dedicated sub-package.

Separation:
    - `validate_feature_headings`: Kept separate because heading validation is an independent CLI concern (BDD document
    linting) with no shared state, imports, or control flow with message capability governance.>

Main consumers:
    - `pyproject.toml` console_scripts entry point referencing `pytest_bdd.script:message_capability_governance_main`,
    which resolves to this module's re-export of `message_capability_governance.main`.>

State and side effects:
    None, keeps no persistent state. This module is a pure re-export with no file I/O, network calls, or mutable globals
    beyond the import-time resolution of the governance sub-package.>

Invariants:
    - The `message_capability_governance_main` attribute must always be a callable compatible with `main(argv: list[str]
    | None = None) -> int` from `message_capability_governance.cli._core`.>

Architecture score:
    #arch-eval:reason_for_existence=3
    #arch-eval:owned_responsibility=2
    #arch-eval:delegation_boundary=4
    #arch-eval:cohesion=5
    #arch-eval:separation=4
    #arch-eval:consumer_clarity=4
    #arch-eval:state_invariants=5
    #arch-eval:entity_fullness=1
    #arch-eval:locational_stability=4
"""

from .message_capability_governance import main as message_capability_governance_main
