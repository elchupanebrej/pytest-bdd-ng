"""
Responsibility:
    Responsibility: Responsibility: `pytest_bdd._pylint.checkers.noqa_rules` owns documented module behavior. It
    directly owns the observable contract, local decisions, and maintenance boundary for this module.

Reason for existence:
    This entity is the information expert for `pytest_bdd._pylint.checkers.noqa_rules` because it keeps the nearest
    code, data shape, call signature, and failure knowledge together.

Delegates:
    - NoqaRulesChecker: owns nested behavior below this boundary

Cohesion:
    The implementation stays together because its imports, calls, state writes, and return contract describe one
    maintainable decision unit.

Separation:
    - module peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
      widening caller knowledge.

Main consumers:
    - None found by static import/name scan; verify dynamic use before refactor

State and side effects:
    mutates _BARE_NOQA_RE, _NO_EXPLANATION_RE, name, msgs, filepath; depends on __future__.annotations, re,
    pathlib.Path, astroid.nodes, pylint.checkers.BaseChecker.

Invariants:
    - `pytest_bdd._pylint.checkers.noqa_rules` keeps its documented import path, ownership boundary, and observable
      behavior stable for callers.

Architecture score:
    #arch-eval:reason_for_existence=4
    #arch-eval:owned_responsibility=4
    #arch-eval:delegation_boundary=4
    #arch-eval:cohesion=3
    #arch-eval:separation=3
    #arch-eval:consumer_clarity=2
    #arch-eval:state_invariants=4
    #arch-eval:entity_fullness=3
    #arch-eval:locational_stability=2
"""

# init: allow
from __future__ import annotations

import re
from pathlib import Path

from astroid import nodes
from pylint.checkers import BaseChecker

_BARE_NOQA_RE = re.compile(r"#\s*noqa(?::\s*)?$")
_NO_EXPLANATION_RE = re.compile(r"#\s*noqa:\s*[A-Z0-9]+(?:\s*,\s*[A-Z0-9]+)*\s*$")


class NoqaRulesChecker(BaseChecker):
    """
    Checker for noqa comments: BLQ1701, BLQ1702.

    Responsibility:
        Checker for noqa comments: BLQ1701, BLQ1702. It directly owns the observable contract, local decisions, and
        maintenance boundary for this class.

    Reason for existence:
        This entity is the information expert for `pytest_bdd._pylint.checkers.noqa_rules.NoqaRulesChecker` because it
        keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - visit_module: owns nested behavior below this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/_pylint/__init__.py: imports or references `NoqaRulesChecker`

    State and side effects:
        mutates name, msgs, filepath, path, source.

    Invariants:
        - `pytest_bdd._pylint.checkers.noqa_rules.NoqaRulesChecker` keeps its documented import path, ownership
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

    name = "noqa-rules"

    msgs = {
        "W9081": (
            "BLQ1701: bare '# noqa' comment. Specify warning codes: '# noqa: CODE  # brief reason'",
            "bare-noqa",
            "BLQ1701: Bare noqa comments are forbidden.",
        ),
        "W9082": (
            "BLQ1702: noqa comment missing explanation. Add explanation: '# noqa: CODE  # brief reason'",
            "missing-noqa-explanation",
            "BLQ1702: Explanation/reason is required for noqa comments.",
        ),
    }

    def visit_module(self, node: nodes.Module) -> None:
        """
        Scan file lines for noqa comment violations.

        Responsibility:
            Scan file lines for noqa comment violations. It directly owns the observable contract, local decisions, and
            maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd._pylint.checkers.noqa_rules.NoqaRulesChecker.visit_module` because it keeps the nearest code,
            data shape, call signature, and failure knowledge together.

        Delegates:
            - self.add_message: collaborator call used by this boundary
            - Path: collaborator call used by this boundary
            - any: collaborator call used by this boundary
            - part.startswith: collaborator call used by this boundary
            - path.read_text: collaborator call used by this boundary
            - enumerate: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - None found by static import/name scan; verify dynamic use before refactor

        State and side effects:
            mutates filepath, path, source, stripped.

        Invariants:
            - `pytest_bdd._pylint.checkers.noqa_rules.NoqaRulesChecker.visit_module` keeps its documented import path,
              ownership boundary, and observable behavior stable for callers.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=2
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=2
        """
        filepath = node.file
        if not filepath:
            return

        path = Path(filepath)
        if any(part.startswith(".") for part in path.parts) or "__pycache__" in path.parts:
            return

        try:
            source = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            return

        for line_no, line_text in enumerate(source.splitlines(), start=1):
            stripped = line_text.rstrip()

            if _BARE_NOQA_RE.search(stripped):
                self.add_message("bare-noqa", line=line_no, node=node)
                continue

            if _NO_EXPLANATION_RE.search(stripped):
                self.add_message("missing-noqa-explanation", line=line_no, node=node)
                continue
