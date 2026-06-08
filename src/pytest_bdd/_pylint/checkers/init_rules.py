"""
Responsibility:
    Responsibility: Responsibility: `pytest_bdd._pylint.checkers.init_rules` owns documented module behavior. It
    directly owns the observable contract, local decisions, and maintenance boundary for this module.

Reason for existence:
    This entity is the information expert for `pytest_bdd._pylint.checkers.init_rules` because it keeps the nearest
    code, data shape, call signature, and failure knowledge together.

Delegates:
    - InitRulesChecker: owns nested behavior below this boundary

Cohesion:
    The implementation stays together because its imports, calls, state writes, and return contract describe one
    maintainable decision unit.

Separation:
    - module peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
      widening caller knowledge.

Main consumers:
    - None found by static import/name scan; verify dynamic use before refactor

State and side effects:
    mutates filepath, has_code, stripped, has_imports, has_all; depends on __future__.annotations, pathlib.Path,
    astroid.nodes, pylint.checkers.BaseChecker.

Invariants:
    - `pytest_bdd._pylint.checkers.init_rules` keeps its documented import path, ownership boundary, and observable
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

from pathlib import Path

from astroid import nodes
from pylint.checkers import BaseChecker

CLASSIFICATION_COMMENTS = {
    "# init: public-api",
    "# init: allow",
    "# init: package-marker",
    "# init: no-check",
}

EXEMPT_COMMENT = "# init: no-check"


class InitRulesChecker(BaseChecker):
    """
    Checker for module hygiene rules: BLQ1401, BLQ1402, BLQ1403, BLQ1404.

    Responsibility:
        Checker for module hygiene rules: BLQ1401, BLQ1402, BLQ1403, BLQ1404. It directly owns the observable contract,
        local decisions, and maintenance boundary for this class.

    Reason for existence:
        This entity is the information expert for `pytest_bdd._pylint.checkers.init_rules.InitRulesChecker` because it
        keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - visit_assign: owns nested behavior below this boundary
        - visit_import: owns nested behavior below this boundary
        - visit_importfrom: owns nested behavior below this boundary
        - visit_module: owns nested behavior below this boundary
        - _is_exempt: owns nested behavior below this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/_pylint/__init__.py: imports or references `InitRulesChecker`

    State and side effects:
        mutates filepath, has_code, stripped, has_imports, has_all.

    Invariants:
        - `pytest_bdd._pylint.checkers.init_rules.InitRulesChecker` keeps its documented import path, ownership
          boundary, and observable behavior stable for callers.

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

    name = "init-rules"

    msgs = {
        "E9051": (
            "BLQ1401: %s defines __all__. Remove __all__ list entirely.",
            "all-defined",
            "BLQ1401: Defining __all__ is forbidden.",
        ),
        "E9052": (
            "BLQ1402: %s is empty or metadata-only. Delete this file (PEP 420).",
            "empty-init",
            "BLQ1402: Empty or metadata-only __init__.py files must be deleted.",
        ),
        "E9053": (
            "BLQ1403: %s contains only docstring. Add actual code or delete.",
            "docstring-only-init",
            "BLQ1403: __init__.py files containing only a docstring must be deleted or have code added.",
        ),
        "E9054": (
            "BLQ1404: imports '%s as %s'. Remove the 'as %s' alias.",
            "redundant-import-alias",
            "BLQ1404: Redundant import aliases are forbidden.",
        ),
    }

    def visit_assign(self, node: nodes.Assign) -> None:
        """
        Detect __all__ assignment.

        Responsibility:
            Detect __all__ assignment. It directly owns the observable contract, local decisions, and maintenance
            boundary for this method. That boundary is intentionally stated in prose so maintainers can distinguish
            owned work from collaborators before editing.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd._pylint.checkers.init_rules.InitRulesChecker.visit_assign` because it keeps the nearest code,
            data shape, call signature, and failure knowledge together.

        Delegates:
            - node.root: collaborator call used by this boundary
            - isinstance: collaborator call used by this boundary
            - self._is_exempt: collaborator call used by this boundary
            - self.add_message: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - None found by static import/name scan; verify dynamic use before refactor

        State and side effects:
            mutates filepath.

        Invariants:
            - `pytest_bdd._pylint.checkers.init_rules.InitRulesChecker.visit_assign` keeps its documented import path,
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
        filepath = node.root().file
        if not filepath or "pytest_bdd_testing" in filepath:
            return

        for target in node.targets:
            if isinstance(target, nodes.AssignName) and target.name == "__all__":
                if not self._is_exempt(filepath):
                    self.add_message("all-defined", node=node, args=(filepath,))

    def visit_import(self, node: nodes.Import) -> None:
        """
        Detect Y as Y redundant aliases.

        Responsibility:
            Detect Y as Y redundant aliases. It directly owns the observable contract, local decisions, and maintenance
            boundary for this method. That boundary is intentionally stated in prose so maintainers can distinguish
            owned work from collaborators before editing.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd._pylint.checkers.init_rules.InitRulesChecker.visit_import` because it keeps the nearest code,
            data shape, call signature, and failure knowledge together.

        Delegates:
            - node.root: collaborator call used by this boundary
            - self._is_exempt: collaborator call used by this boundary
            - self.add_message: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - None found by static import/name scan; verify dynamic use before refactor

        State and side effects:
            mutates filepath.

        Invariants:
            - `pytest_bdd._pylint.checkers.init_rules.InitRulesChecker.visit_import` keeps its documented import path,
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
        filepath = node.root().file
        if not filepath or "pytest_bdd_testing" in filepath:
            return
        if self._is_exempt(filepath):
            return

        for name, asname in node.names:
            if asname and asname == name:
                self.add_message("redundant-import-alias", node=node, args=(name, name, name))

    def visit_importfrom(self, node: nodes.ImportFrom) -> None:
        """
        Detect Y as Y redundant aliases in from-imports.

        Responsibility:
            Detect Y as Y redundant aliases in from-imports. It directly owns the observable contract, local decisions,
            and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd._pylint.checkers.init_rules.InitRulesChecker.visit_importfrom` because it keeps the nearest
            code, data shape, call signature, and failure knowledge together.

        Delegates:
            - node.root: collaborator call used by this boundary
            - self._is_exempt: collaborator call used by this boundary
            - self.add_message: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - None found by static import/name scan; verify dynamic use before refactor

        State and side effects:
            mutates filepath.

        Invariants:
            - `pytest_bdd._pylint.checkers.init_rules.InitRulesChecker.visit_importfrom` keeps its documented import
              path, ownership boundary, and observable behavior stable for callers.

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
        if not filepath or "pytest_bdd_testing" in filepath:
            return
        if self._is_exempt(filepath):
            return

        for name, asname in node.names:
            if asname and asname == name:
                self.add_message("redundant-import-alias", node=node, args=(name, name, name))

    def visit_module(self, node: nodes.Module) -> None:
        """
        Check __init__.py files for being empty or docstring-only.

        Responsibility:
            Check __init__.py files for being empty or docstring-only. It directly owns the observable contract, local
            decisions, and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd._pylint.checkers.init_rules.InitRulesChecker.visit_module` because it keeps the nearest code,
            data shape, call signature, and failure knowledge together.

        Delegates:
            - isinstance: collaborator call used by this boundary
            - self.add_message: collaborator call used by this boundary
            - self._is_exempt: collaborator call used by this boundary
            - Path: collaborator call used by this boundary
            - path.read_text: collaborator call used by this boundary
            - stripped.replace: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - None found by static import/name scan; verify dynamic use before refactor

        State and side effects:
            mutates has_code, stripped, has_imports, has_all, filepath.

        Invariants:
            - `pytest_bdd._pylint.checkers.init_rules.InitRulesChecker.visit_module` keeps its documented import path,
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
        if not filepath or "pytest_bdd_testing" in filepath:
            return
        if self._is_exempt(filepath):
            return

        path = Path(filepath)
        if path.name != "__init__.py":
            return

        # Check if there are any imports
        has_imports = False
        has_all = False
        has_code = False

        for child in node.body:
            if isinstance(child, (nodes.Import, nodes.ImportFrom)):
                has_imports = True
            elif isinstance(child, nodes.Assign):
                for target in child.targets:
                    if isinstance(target, nodes.AssignName) and target.name == "__all__":
                        has_all = True
                has_code = True
            elif isinstance(child, (nodes.FunctionDef, nodes.AsyncFunctionDef, nodes.ClassDef)):
                has_code = True

        if has_imports or has_all:
            return

        try:
            source = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            return

        # Strip comments and check if anything remains
        stripped = source
        for comment in CLASSIFICATION_COMMENTS:
            stripped = stripped.replace(comment, "")
        stripped = stripped.strip()

        # BLQ1402: Empty or metadata-only
        if not stripped:
            self.add_message("empty-init", node=node, args=(filepath,))
            return

        # BLQ1403: Docstring-only
        if not has_code:
            self.add_message("docstring-only-init", node=node, args=(filepath,))

    def _is_exempt(self, filepath: str) -> bool:
        """
        Responsibility:
            Responsibility: Responsibility: `pytest_bdd._pylint.checkers.init_rules.InitRulesChecker._is_exempt` owns
            documented method behavior. It directly owns the observable contract, local decisions, and maintenance
            boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd._pylint.checkers.init_rules.InitRulesChecker._is_exempt` because it keeps the nearest code, data
            shape, call signature, and failure knowledge together.

        Delegates:
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
            mutates source.

        Invariants:
            - `pytest_bdd._pylint.checkers.init_rules.InitRulesChecker._is_exempt` keeps its documented import path,
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
        try:
            source = Path(filepath).read_text(encoding="utf-8")
            return EXEMPT_COMMENT in source
        except Exception:  # noqa: BLE001
            return False
