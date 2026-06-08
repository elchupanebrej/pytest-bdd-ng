"""
Pylint checks for responsibility architecture documentation.

Responsibility:
    Pylint checks for responsibility architecture documentation. It directly owns the observable contract, local
    decisions, and maintenance boundary for this module.

Reason for existence:
    This entity is the information expert for `pytest_bdd._pylint.checkers.responsibility_docs` because it keeps the
    nearest code, data shape, call signature, and failure knowledge together.

Delegates:
    - ResponsibilityDocsChecker: owns nested behavior below this boundary

Cohesion:
    The implementation stays together because its imports, calls, state writes, and return contract describe one
    maintainable decision unit.

Separation:
    - module peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
      widening caller knowledge.

Main consumers:
    - None found by static import/name scan; verify dynamic use before refactor

State and side effects:
    mutates doc, sections, current, MIN_LONG_SECTION, PLACEHOLDER_RE; depends on __future__.annotations, ast, re,
    pathlib.Path, astroid.nodes.

Invariants:
    - `pytest_bdd._pylint.checkers.responsibility_docs` keeps its documented import path, ownership boundary, and
      observable behavior stable for callers.

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

from __future__ import annotations

import ast
import re
from pathlib import Path

from astroid import nodes
from pylint.checkers import BaseChecker

MIN_LONG_SECTION = 140
PLACEHOLDER_RE = re.compile(r"<[^>\n]+>")
REQUIRED_COMMON_SECTIONS = (
    "Responsibility",
    "Reason for existence",
    "Delegates",
    "Cohesion",
    "Separation",
    "Main consumers",
    "State and side effects",
    "Architecture score",
)
SCORE_CRITERIA = (
    "reason_for_existence",
    "owned_responsibility",
    "delegation_boundary",
    "cohesion",
    "separation",
    "consumer_clarity",
    "state_invariants",
    "entity_fullness",
    "locational_stability",
)


class ResponsibilityDocsChecker(BaseChecker):
    """
    Validate responsibility contracts on source entities.

    Responsibility:
        Validate responsibility contracts on source entities. It directly owns the observable contract, local decisions,
        and maintenance boundary for this class.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd._pylint.checkers.responsibility_docs.ResponsibilityDocsChecker` because it keeps the nearest code,
        data shape, call signature, and failure knowledge together.

    Delegates:
        - visit_module: owns nested behavior below this boundary
        - visit_classdef: owns nested behavior below this boundary
        - visit_functiondef: owns nested behavior below this boundary
        - visit_asyncfunctiondef: owns nested behavior below this boundary
        - _check_node: owns nested behavior below this boundary
        - _doc_for_node: owns nested behavior below this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/_pylint/__init__.py: imports or references `ResponsibilityDocsChecker`

    State and side effects:
        mutates doc, sections, current, name, msgs.

    Invariants:
        - `pytest_bdd._pylint.checkers.responsibility_docs.ResponsibilityDocsChecker` keeps its documented import path,
          ownership boundary, and observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=3
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=3
    """

    name = "responsibility-docs"

    msgs = {
        "R9010": (
            "BLQ910: missing responsibility documentation section: %s",
            "missing-responsibility-doc",
            "Module, class, function, and method docstrings must include responsibility architecture sections.",
        ),
        "R9011": (
            "BLQ911: responsibility documentation section is too short: %s",
            "short-responsibility-doc",
            "Responsibility and Reason for existence must be descriptive enough to explain the architecture boundary.",
        ),
        "R9012": (
            "BLQ912: legacy responsibility documentation section used: %s",
            "legacy-responsibility-doc",
            "Use Cohesion and Separation instead of Not split because and Not merged with.",
        ),
        "R9013": (
            "BLQ913: missing or invalid architecture score tag: %s",
            "missing-architecture-score",
            "Responsibility documentation must include parseable #arch-eval tags with integer values from 0 to 5.",
        ),
        "R9014": (
            "BLQ914: unfilled responsibility placeholder in section: %s",
            "unfilled-responsibility-placeholder",
            "Responsibility documentation template placeholders must be replaced before commit.",
        ),
    }

    def visit_module(self, node: nodes.Module) -> None:
        """
        Validate module-level responsibility documentation.

        Responsibility:
            Validate module-level responsibility documentation. It directly owns the observable contract, local
            decisions, and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd._pylint.checkers.responsibility_docs.ResponsibilityDocsChecker.visit_module` because it keeps
            the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - self._check_node: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - None found by static import/name scan; verify dynamic use before refactor

        State and side effects:
            keeps no local persistent state beyond call-local values.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=2
            #arch-eval:state_invariants=3
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=2
        """
        self._check_node(node, require_invariants=True)

    def visit_classdef(self, node: nodes.ClassDef) -> None:
        """
        Validate class-level responsibility documentation.

        Responsibility:
            Validate class-level responsibility documentation. It directly owns the observable contract, local
            decisions, and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd._pylint.checkers.responsibility_docs.ResponsibilityDocsChecker.visit_classdef` because it keeps
            the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - self._check_node: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - None found by static import/name scan; verify dynamic use before refactor

        State and side effects:
            keeps no local persistent state beyond call-local values.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=2
            #arch-eval:state_invariants=3
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=2
        """
        self._check_node(node, require_invariants=True)

    def visit_functiondef(self, node: nodes.FunctionDef) -> None:
        """
        Validate function and method responsibility documentation.

        Responsibility:
            Validate function and method responsibility documentation. It directly owns the observable contract, local
            decisions, and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd._pylint.checkers.responsibility_docs.ResponsibilityDocsChecker.visit_functiondef` because it
            keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - self._check_node: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - None found by static import/name scan; verify dynamic use before refactor

        State and side effects:
            keeps no local persistent state beyond call-local values.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=2
            #arch-eval:state_invariants=3
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=2
        """
        self._check_node(node, require_invariants=False)

    def visit_asyncfunctiondef(self, node: nodes.AsyncFunctionDef) -> None:
        """
        Validate async function and method responsibility documentation.

        Responsibility:
            Validate async function and method responsibility documentation. It directly owns the observable contract,
            local decisions, and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd._pylint.checkers.responsibility_docs.ResponsibilityDocsChecker.visit_asyncfunctiondef` because
            it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - self._check_node: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - None found by static import/name scan; verify dynamic use before refactor

        State and side effects:
            keeps no local persistent state beyond call-local values.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=2
            #arch-eval:state_invariants=3
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=2
        """
        self._check_node(node, require_invariants=False)

    def _check_node(self, node: nodes.NodeNG, *, require_invariants: bool) -> None:
        """
        Responsibility:
            Responsibility: Responsibility:
            `pytest_bdd._pylint.checkers.responsibility_docs.ResponsibilityDocsChecker._check_node` owns documented
            method behavior. It directly owns the observable contract, local decisions, and maintenance boundary for
            this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd._pylint.checkers.responsibility_docs.ResponsibilityDocsChecker._check_node` because it keeps the
            nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - self.add_message: collaborator call used by this boundary
            - sections.get: collaborator call used by this boundary
            - self._doc_for_node: collaborator call used by this boundary
            - self._parse_sections: collaborator call used by this boundary
            - list: collaborator call used by this boundary
            - required.append: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - None found by static import/name scan; verify dynamic use before refactor

        State and side effects:
            mutates doc, sections, required, text, tag_pattern.

        Invariants:
            - `pytest_bdd._pylint.checkers.responsibility_docs.ResponsibilityDocsChecker._check_node` keeps its
              documented import path, ownership boundary, and observable behavior stable for callers.

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
        filepath = node.root().file
        if filepath:
            normalized_path = filepath.replace("\\", "/")
            if (
                "pytest_bdd_testing/" in normalized_path
                or "/tests/" in normalized_path
                or normalized_path.startswith("tests/")
            ):
                return

        doc = self._doc_for_node(node)
        sections = self._parse_sections(doc)
        required = list(REQUIRED_COMMON_SECTIONS)
        if require_invariants:
            required.append("Invariants")
        for section in required:
            if not sections.get(section):
                self.add_message("missing-responsibility-doc", node=node, args=(section,))
            elif PLACEHOLDER_RE.search(sections[section]):
                self.add_message("unfilled-responsibility-placeholder", node=node, args=(section,))
        for section in ("Responsibility", "Reason for existence"):
            text = " ".join(sections.get(section, "").split())
            if text and len(text) < MIN_LONG_SECTION:
                self.add_message("short-responsibility-doc", node=node, args=(section,))
        for legacy in ("Not split because", "Not merged with"):
            if legacy in sections:
                self.add_message("legacy-responsibility-doc", node=node, args=(legacy,))
        for criterion in SCORE_CRITERIA:
            tag_pattern = rf"#arch-eval:{criterion}=([0-5])(?:\s|$)"
            if not re.search(tag_pattern, doc):
                self.add_message("missing-architecture-score", node=node, args=(criterion,))

    def _doc_for_node(self, node: nodes.NodeNG) -> str:
        """
        Responsibility:
            Responsibility: Responsibility:
            `pytest_bdd._pylint.checkers.responsibility_docs.ResponsibilityDocsChecker._doc_for_node` owns documented
            method behavior. It directly owns the observable contract, local decisions, and maintenance boundary for
            this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd._pylint.checkers.responsibility_docs.ResponsibilityDocsChecker._doc_for_node` because it keeps
            the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - getattr: collaborator call used by this boundary
            - str: collaborator call used by this boundary
            - isinstance: collaborator call used by this boundary
            - ast.parse: collaborator call used by this boundary
            - Path.read_text: collaborator call used by this boundary
            - Path: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - None found by static import/name scan; verify dynamic use before refactor

        State and side effects:
            mutates doc_node, doc, tree.

        Invariants:
            - `pytest_bdd._pylint.checkers.responsibility_docs.ResponsibilityDocsChecker._doc_for_node` keeps its
              documented import path, ownership boundary, and observable behavior stable for callers.

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
        doc_node = getattr(node, "doc_node", None)
        if doc_node is not None and getattr(doc_node, "value", None):
            return str(doc_node.value)
        doc = getattr(node, "doc", None)
        if doc:
            return str(doc)
        if isinstance(node, nodes.Module) and node.file:
            try:
                tree = ast.parse(Path(node.file).read_text(encoding="utf-8"), filename=node.file)
            except (OSError, SyntaxError, UnicodeDecodeError):
                return ""
            return ast.get_docstring(tree) or ""
        return ""

    def _parse_sections(self, doc: str) -> dict[str, str]:
        """
        Responsibility:
            Responsibility: Responsibility:
            `pytest_bdd._pylint.checkers.responsibility_docs.ResponsibilityDocsChecker._parse_sections` owns documented
            method behavior. It directly owns the observable contract, local decisions, and maintenance boundary for
            this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd._pylint.checkers.responsibility_docs.ResponsibilityDocsChecker._parse_sections` because it keeps
            the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - doc.splitlines: collaborator call used by this boundary
            - raw_line.strip: collaborator call used by this boundary
            - append: collaborator call used by this boundary
            - join.strip: collaborator call used by this boundary
            - join: collaborator call used by this boundary
            - sections.items: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - None found by static import/name scan; verify dynamic use before refactor

        State and side effects:
            mutates current, headings, sections, line.

        Invariants:
            - `pytest_bdd._pylint.checkers.responsibility_docs.ResponsibilityDocsChecker._parse_sections` keeps its
              documented import path, ownership boundary, and observable behavior stable for callers.

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
        headings = {
            "Responsibility:",
            "Reason for existence:",
            "Delegates:",
            "Cohesion:",
            "Separation:",
            "Main consumers:",
            "State and side effects:",
            "Invariants:",
            "Failure semantics:",
            "Architecture score:",
            "Not split because:",
            "Not merged with:",
        }
        sections: dict[str, list[str]] = {}
        current: str | None = None
        for raw_line in doc.splitlines():
            line = raw_line.strip()
            if line in headings:
                current = line[:-1]
                sections[current] = []
            elif current:
                sections[current].append(raw_line)
        return {key: "\n".join(value).strip() for key, value in sections.items()}
