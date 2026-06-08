"""
Shared utilities for the CLI package.

Responsibility:
    Shared utilities for the CLI package. It directly owns the observable contract, local decisions, and maintenance
    boundary for this module. That boundary is intentionally stated in prose so maintainers can distinguish owned work
    from collaborators before editing.

Reason for existence:
    This entity is the information expert for `pytest_bdd.script.message_capability_governance.cli._utils` because it
    keeps the nearest code, data shape, call signature, and failure knowledge together.

Delegates:
    - _emit_text: owns nested behavior below this boundary

Cohesion:
    The implementation stays together because its imports, calls, state writes, and return contract describe one
    maintainable decision unit.

Separation:
    - module peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
      widening caller knowledge.

Main consumers:
    - src/pytest_bdd/script/message_capability_governance/cli/_core.py: imports or references `_utils`
    - src/pytest_bdd/script/message_capability_governance/cli/_report.py: imports or references `_utils`

State and side effects:
    depends on __future__.annotations, sys, pathlib.Path.

Invariants:
    - `pytest_bdd.script.message_capability_governance.cli._utils` keeps its documented import path, ownership boundary,
      and observable behavior stable for callers.

Architecture score:
    #arch-eval:reason_for_existence=4
    #arch-eval:owned_responsibility=4
    #arch-eval:delegation_boundary=4
    #arch-eval:cohesion=3
    #arch-eval:separation=3
    #arch-eval:consumer_clarity=4
    #arch-eval:state_invariants=3
    #arch-eval:entity_fullness=3
    #arch-eval:locational_stability=3
"""

from __future__ import annotations

import sys
from pathlib import Path


def _emit_text(text: str, *, output_path: Path | None = None) -> None:
    """
    Responsibility:
        Responsibility: Responsibility: `pytest_bdd.script.message_capability_governance.cli._utils._emit_text` owns
        documented function behavior. It directly owns the observable contract, local decisions, and maintenance
        boundary for this function.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.script.message_capability_governance.cli._utils._emit_text` because it keeps the nearest code, data
        shape, call signature, and failure knowledge together.

    Delegates:
        - sys.stdout.write: collaborator call used by this boundary
        - output_path.parent.mkdir: collaborator call used by this boundary
        - output_path.write_text: collaborator call used by this boundary
        - text.endswith: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/script/message_capability_governance/cli/_core.py: imports or references `_emit_text`
        - src/pytest_bdd/script/message_capability_governance/cli/_report.py: imports or references `_emit_text`
        - src/pytest_bdd/script/message_capability_governance/cli/facade.py: imports or references `_emit_text`

    State and side effects:
        keeps no local persistent state beyond call-local values.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=4
    """
    if output_path is not None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(text, encoding="utf-8")
        return
    sys.stdout.write(text)
    if not text.endswith("\n"):
        sys.stdout.write("\n")
