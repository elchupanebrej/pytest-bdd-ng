"""
Responsibility:
    Responsibility: Responsibility: `pytest_bdd._pylint.checkers.quality_gates` owns documented module behavior. It
    directly owns the observable contract, local decisions, and maintenance boundary for this module.

Reason for existence:
    This entity is the information expert for `pytest_bdd._pylint.checkers.quality_gates` because it keeps the nearest
    code, data shape, call signature, and failure knowledge together.

Delegates:
    - QualityGatesChecker: owns nested behavior below this boundary

Cohesion:
    The implementation stays together because its imports, calls, state writes, and return contract describe one
    maintainable decision unit.

Separation:
    - module peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
      widening caller knowledge.

Main consumers:
    - None found by static import/name scan; verify dynamic use before refactor

State and side effects:
    mutates filepath, has_test_methods, name, msgs, self._lines_cache; depends on __future__.annotations, pathlib.Path,
    typing.TYPE_CHECKING, astroid.nodes, pylint.checkers.BaseChecker.

Invariants:
    - `pytest_bdd._pylint.checkers.quality_gates` keeps its documented import path, ownership boundary, and observable
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
# pylint: disable=file-too-long
from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from astroid import nodes
from pylint.checkers import BaseChecker

if TYPE_CHECKING:
    from pylint.lint import PyLinter


class QualityGatesChecker(BaseChecker):
    """
    Checker for pytest-bdd quality gates: BLQ901, BLQ902, BLQ903.

    Responsibility:
        Checker for pytest-bdd quality gates: BLQ901, BLQ902, BLQ903. It directly owns the observable contract, local
        decisions, and maintenance boundary for this class.

    Reason for existence:
        This entity is the information expert for `pytest_bdd._pylint.checkers.quality_gates.QualityGatesChecker`
        because it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - __init__: owns nested behavior below this boundary
        - _get_lines: owns nested behavior below this boundary
        - _line_at: owns nested behavior below this boundary
        - _has_noqa_for_rule: owns nested behavior below this boundary
        - visit_return: owns nested behavior below this boundary
        - visit_excepthandler: owns nested behavior below this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/_pylint/__init__.py: imports or references `QualityGatesChecker`

    State and side effects:
        mutates filepath, has_test_methods, name, msgs, self._lines_cache.

    Invariants:
        - `pytest_bdd._pylint.checkers.quality_gates.QualityGatesChecker` keeps its documented import path, ownership
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

    name = "quality-gates"

    msgs = {
        "R9001": (
            "BLQ901: return None in non-hook function - use Nothing (Maybe) or Failure(reason) (Result) instead",
            "no-return-none",
            "BLQ901: return None in non-hook function is forbidden.",
        ),
        "W9002": (
            "BLQ902: bare except Exception: without logging - add logger.warning(exc_info=True) or # noqa: BLE001",
            "bare-except-exception",
            "BLQ902: bare except Exception: without logging is forbidden.",
        ),
        "R9003": (
            "BLQ903: test class found — use pytest-style functions instead of class-based tests",
            "no-test-class",
            "BLQ903: test class found.",
        ),
    }

    def __init__(self, linter: PyLinter) -> None:
        """
        Responsibility:
            Responsibility: Responsibility: `pytest_bdd._pylint.checkers.quality_gates.QualityGatesChecker.__init__`
            owns documented method behavior. It directly owns the observable contract, local decisions, and maintenance
            boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd._pylint.checkers.quality_gates.QualityGatesChecker.__init__` because it keeps the nearest code,
            data shape, call signature, and failure knowledge together.

        Delegates:
            - super.__init__: collaborator call used by this boundary
            - super: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/_gherkin_go/_types.py: imports or references `__init__`
            - src/pytest_bdd/_pylint/checkers/layer_rules.py: imports or references `__init__`
            - src/pytest_bdd/_pylint/checkers/plugin_patterns.py: imports or references `__init__`
            - src/pytest_bdd/model/message_extension.py: imports or references `__init__`
            - src/pytest_bdd/parsers/base.py: imports or references `__init__`

        State and side effects:
            mutates self._lines_cache.

        Invariants:
            - `pytest_bdd._pylint.checkers.quality_gates.QualityGatesChecker.__init__` keeps its documented import path,
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
        super().__init__(linter)
        self._lines_cache: dict[str, list[str]] = {}

    def _get_lines(self, node: nodes.NodeNG) -> list[str]:
        """
        Responsibility:
            Responsibility: Responsibility: `pytest_bdd._pylint.checkers.quality_gates.QualityGatesChecker._get_lines`
            owns documented method behavior. It directly owns the observable contract, local decisions, and maintenance
            boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd._pylint.checkers.quality_gates.QualityGatesChecker._get_lines` because it keeps the nearest
            code, data shape, call signature, and failure knowledge together.

        Delegates:
            - node.root: collaborator call used by this boundary
            - Path.read_text.splitlines: collaborator call used by this boundary
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
            mutates filepath.

        Invariants:
            - `pytest_bdd._pylint.checkers.quality_gates.QualityGatesChecker._get_lines` keeps its documented import
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
        if not filepath:
            return []
        if filepath not in self._lines_cache:
            try:
                self._lines_cache[filepath] = Path(filepath).read_text(encoding="utf-8").splitlines()
            except Exception:  # noqa: BLE001
                self._lines_cache[filepath] = []
        return self._lines_cache[filepath]

    def _line_at(self, lines: list[str], line_number: int) -> str:
        """
        Responsibility:
            Responsibility: Responsibility: `pytest_bdd._pylint.checkers.quality_gates.QualityGatesChecker._line_at`
            owns documented method behavior. It directly owns the observable contract, local decisions, and maintenance
            boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd._pylint.checkers.quality_gates.QualityGatesChecker._line_at` because it keeps the nearest code,
            data shape, call signature, and failure knowledge together.

        Delegates:
            - len: collaborator call used by this boundary

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
        if line_number < 1 or line_number > len(lines):
            return ""
        return lines[line_number - 1]

    def _has_noqa_for_rule(self, node: nodes.NodeNG, rules: tuple[str, ...]) -> bool:
        """
        Responsibility:
            Responsibility: Responsibility:
            `pytest_bdd._pylint.checkers.quality_gates.QualityGatesChecker._has_noqa_for_rule` owns documented method
            behavior. It directly owns the observable contract, local decisions, and maintenance boundary for this
            method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd._pylint.checkers.quality_gates.QualityGatesChecker._has_noqa_for_rule` because it keeps the
            nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - self._line_at: collaborator call used by this boundary
            - self._get_lines: collaborator call used by this boundary
            - any: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - None found by static import/name scan; verify dynamic use before refactor

        State and side effects:
            mutates lines, current_line, previous_line.

        Invariants:
            - `pytest_bdd._pylint.checkers.quality_gates.QualityGatesChecker._has_noqa_for_rule` keeps its documented
              import path, ownership boundary, and observable behavior stable for callers.

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
        lines = self._get_lines(node)
        current_line = self._line_at(lines, node.lineno)
        previous_line = self._line_at(lines, node.lineno - 1)
        for line in (current_line, previous_line):
            if "noqa" in line:
                if "noqa:" not in line:
                    return True
                if any(rule in line for rule in rules):
                    return True
        return False

    def visit_return(self, node: nodes.Return) -> None:
        """
        Detect return None in non-hook functions.

        Responsibility:
            Detect return None in non-hook functions. It directly owns the observable contract, local decisions, and
            maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd._pylint.checkers.quality_gates.QualityGatesChecker.visit_return` because it keeps the nearest
            code, data shape, call signature, and failure knowledge together.

        Delegates:
            - isinstance: collaborator call used by this boundary
            - node.root: collaborator call used by this boundary
            - any: collaborator call used by this boundary
            - node.scope: collaborator call used by this boundary
            - scope.name.startswith: collaborator call used by this boundary
            - self._has_noqa_for_rule: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - None found by static import/name scan; verify dynamic use before refactor

        State and side effects:
            mutates filepath, exempt_dirs, scope.

        Invariants:
            - `pytest_bdd._pylint.checkers.quality_gates.QualityGatesChecker.visit_return` keeps its documented import
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
        if not filepath:
            return
        # Exempt non-core directories and testing
        exempt_dirs = {"pytest_bdd_testing", "_pylint", "plugin", "util", "script", "scenario_locator"}
        if any(d in filepath for d in exempt_dirs):
            return

        # Check if value is None
        if not (isinstance(node.value, nodes.Const) and node.value.value is None):
            return

        # Check if we are inside a function scope
        scope = node.scope()
        if not isinstance(scope, (nodes.FunctionDef, nodes.AsyncFunctionDef)):
            return

        # Exempt pytest hooks
        if scope.name.startswith(("pytest_", "_pytest_")):
            return

        # Check for noqa comments
        if self._has_noqa_for_rule(node, ("BLQ901", "no-return-none")):
            return

        self.add_message("no-return-none", node=node)

    def visit_excepthandler(self, node: nodes.ExceptHandler) -> None:
        """
        Detect unlogged except Exception handlers.

        Responsibility:
            Detect unlogged except Exception handlers. It directly owns the observable contract, local decisions, and
            maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd._pylint.checkers.quality_gates.QualityGatesChecker.visit_excepthandler` because it keeps the
            nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - node.root: collaborator call used by this boundary
            - isinstance: collaborator call used by this boundary
            - self._has_noqa_for_rule: collaborator call used by this boundary
            - self._has_exception_logging: collaborator call used by this boundary
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
            - `pytest_bdd._pylint.checkers.quality_gates.QualityGatesChecker.visit_excepthandler` keeps its documented
              import path, ownership boundary, and observable behavior stable for callers.

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
        if filepath and "pytest_bdd_testing" in filepath:
            return

        # Check if handler handles Exception specifically
        if not (isinstance(node.type, nodes.Name) and node.type.name == "Exception"):
            return

        # Check for noqa comments
        if self._has_noqa_for_rule(node, ("BLE001", "BLQ902")):
            return

        # Check for logging inside handler body
        if self._has_exception_logging(node):
            return

        self.add_message("bare-except-exception", node=node)

    def _has_exception_logging(self, handler: nodes.ExceptHandler) -> bool:
        """
        Responsibility:
            Responsibility: Responsibility:
            `pytest_bdd._pylint.checkers.quality_gates.QualityGatesChecker._has_exception_logging` owns documented
            method behavior. It directly owns the observable contract, local decisions, and maintenance boundary for
            this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd._pylint.checkers.quality_gates.QualityGatesChecker._has_exception_logging` because it keeps the
            nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - stmt.nodes_of_class: collaborator call used by this boundary
            - self._is_supported_logging_call: collaborator call used by this boundary

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
        for stmt in handler.body:
            for child in stmt.nodes_of_class(nodes.Call):
                if self._is_supported_logging_call(child):
                    return True
        return False

    def _is_supported_logging_call(self, call: nodes.Call) -> bool:
        """
        Responsibility:
            Responsibility: Responsibility:
            `pytest_bdd._pylint.checkers.quality_gates.QualityGatesChecker._is_supported_logging_call` owns documented
            method behavior. It directly owns the observable contract, local decisions, and maintenance boundary for
            this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd._pylint.checkers.quality_gates.QualityGatesChecker._is_supported_logging_call` because it keeps
            the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - isinstance: collaborator call used by this boundary

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
        if not isinstance(call.func, nodes.Attribute):
            return False
        if not (isinstance(call.func.expr, nodes.Name) and call.func.expr.name in {"logger", "logging"}):
            return False

        if call.func.attrname == "exception":
            return True
        if call.func.attrname != "warning":
            return False

        # For warning, look for exc_info=True
        if not call.keywords:
            return False
        for kw in call.keywords:
            if kw.arg == "exc_info" and isinstance(kw.value, nodes.Const) and kw.value.value is True:
                return True
        return False

    def visit_classdef(self, node: nodes.ClassDef) -> None:
        """
        Detect test class definitions in test files.

        Responsibility:
            Detect test class definitions in test files. It directly owns the observable contract, local decisions, and
            maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd._pylint.checkers.quality_gates.QualityGatesChecker.visit_classdef` because it keeps the nearest
            code, data shape, call signature, and failure knowledge together.

        Delegates:
            - node.root: collaborator call used by this boundary
            - Path.name.startswith: collaborator call used by this boundary
            - Path: collaborator call used by this boundary
            - isinstance: collaborator call used by this boundary
            - item.name.startswith: collaborator call used by this boundary
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
            mutates has_test_methods, filepath.

        Invariants:
            - `pytest_bdd._pylint.checkers.quality_gates.QualityGatesChecker.visit_classdef` keeps its documented import
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
        if not filepath:
            return

        # Check if we are inside a test/cases directory or test file
        if not ("pytest_bdd_testing" in filepath or Path(filepath).name.startswith("test_")):
            return

        # Check if the class has any test methods
        has_test_methods = False
        for item in node.body:
            if isinstance(item, (nodes.FunctionDef, nodes.AsyncFunctionDef)) and item.name.startswith("test_"):
                has_test_methods = True
                break

        if has_test_methods:
            self.add_message("no-test-class", node=node)
