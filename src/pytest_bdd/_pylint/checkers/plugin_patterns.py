"""
Responsibility:
    Responsibility: Responsibility: `pytest_bdd._pylint.checkers.plugin_patterns` owns documented module behavior. It
    directly owns the observable contract, local decisions, and maintenance boundary for this module.

Reason for existence:
    This entity is the information expert for `pytest_bdd._pylint.checkers.plugin_patterns` because it keeps the nearest
    code, data shape, call signature, and failure knowledge together.

Delegates:
    - PluginPatternsChecker: owns nested behavior below this boundary

Cohesion:
    The implementation stays together because its imports, calls, state writes, and return contract describe one
    maintainable decision unit.

Separation:
    - module peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
      widening caller knowledge.

Main consumers:
    - None found by static import/name scan; verify dynamic use before refactor

State and side effects:
    mutates current_plugin, parts, name, self._checked_missing_files, plugin_root; depends on __future__.annotations,
    pathlib.Path, typing.TYPE_CHECKING, astroid.nodes, pylint.checkers.BaseChecker.

Invariants:
    - `pytest_bdd._pylint.checkers.plugin_patterns` keeps its documented import path, ownership boundary, and observable
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
from typing import TYPE_CHECKING

from astroid import nodes
from pylint.checkers import BaseChecker

if TYPE_CHECKING:
    from pylint.lint import PyLinter


class PluginPatternsChecker(BaseChecker):
    """
    Checker for plugin pattern compliance: BLQ1001, BLQ1002, BLQ1003.

    Responsibility:
        Checker for plugin pattern compliance: BLQ1001, BLQ1002, BLQ1003. It directly owns the observable contract,
        local decisions, and maintenance boundary for this class.

    Reason for existence:
        This entity is the information expert for `pytest_bdd._pylint.checkers.plugin_patterns.PluginPatternsChecker`
        because it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - __init__: owns nested behavior below this boundary
        - visit_module: owns nested behavior below this boundary
        - _check_missing_files: owns nested behavior below this boundary
        - visit_importfrom: owns nested behavior below this boundary
        - visit_import: owns nested behavior below this boundary
        - visit_subscript: owns nested behavior below this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/_pylint/__init__.py: imports or references `PluginPatternsChecker`

    State and side effects:
        mutates current_plugin, parts, name, self._checked_missing_files, plugin_root.

    Invariants:
        - `pytest_bdd._pylint.checkers.plugin_patterns.PluginPatternsChecker` keeps its documented import path,
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

    name = "plugin-patterns"

    msgs = {
        "E9011": (
            "BLQ1001: missing required file '%s' in plugin '%s'",
            "missing-plugin-file",
            "BLQ1001: All plugins must have entrypoint.py, hook.py, and plugin.py.",
        ),
        "E9012": (
            "BLQ1002: cross-plugin import from '%s' in plugin '%s' (use hooks for inter-plugin communication)",
            "cross-plugin-import",
            "BLQ1002: Importing from other plugins is forbidden.",
        ),
        "E9013": (
            "BLQ1003: direct stash access in '%s' — use StashBound subclass for config.stash access",
            "direct-stash-access",
            "BLQ1003: Direct stash access is forbidden outside StashBound subclasses.",
        ),
    }

    def __init__(self, linter: PyLinter) -> None:
        """
        Responsibility:
            Responsibility: Responsibility: `pytest_bdd._pylint.checkers.plugin_patterns.PluginPatternsChecker.__init__`
            owns documented method behavior. It directly owns the observable contract, local decisions, and maintenance
            boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd._pylint.checkers.plugin_patterns.PluginPatternsChecker.__init__` because it keeps the nearest
            code, data shape, call signature, and failure knowledge together.

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
            - src/pytest_bdd/_pylint/checkers/quality_gates.py: imports or references `__init__`
            - src/pytest_bdd/model/message_extension.py: imports or references `__init__`
            - src/pytest_bdd/parsers/base.py: imports or references `__init__`

        State and side effects:
            mutates self._checked_missing_files.

        Invariants:
            - `pytest_bdd._pylint.checkers.plugin_patterns.PluginPatternsChecker.__init__` keeps its documented import
              path, ownership boundary, and observable behavior stable for callers.

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
        self._checked_missing_files = False

    def visit_module(self, node: nodes.Module) -> None:
        """
        Run once-per-lint checks and initialize module checks.

        Responsibility:
            Run once-per-lint checks and initialize module checks. It directly owns the observable contract, local
            decisions, and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd._pylint.checkers.plugin_patterns.PluginPatternsChecker.visit_module` because it keeps the
            nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - self._check_missing_files: collaborator call used by this boundary

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
        self._check_missing_files(node)

    def _check_missing_files(self, node: nodes.Module) -> None:
        """
        Responsibility:
            Responsibility: Responsibility:
            `pytest_bdd._pylint.checkers.plugin_patterns.PluginPatternsChecker._check_missing_files` owns documented
            method behavior. It directly owns the observable contract, local decisions, and maintenance boundary for
            this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd._pylint.checkers.plugin_patterns.PluginPatternsChecker._check_missing_files` because it keeps
            the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - Path.resolve: collaborator call used by this boundary
            - Path: collaborator call used by this boundary
            - candidate.is_dir: collaborator call used by this boundary
            - plugin_root.is_dir: collaborator call used by this boundary
            - sorted: collaborator call used by this boundary
            - plugin_root.iterdir: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - None found by static import/name scan; verify dynamic use before refactor

        State and side effects:
            mutates plugin_root, self._checked_missing_files, current_file, path, candidate.

        Invariants:
            - `pytest_bdd._pylint.checkers.plugin_patterns.PluginPatternsChecker._check_missing_files` keeps its
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
        if self._checked_missing_files:
            return
        self._checked_missing_files = True

        current_file = node.file
        if not current_file:
            return

        path = Path(current_file).resolve()
        plugin_root = None
        for parent in path.parents:
            candidate = parent / "plugin"
            if parent.name == "pytest_bdd" and candidate.is_dir():
                plugin_root = candidate
                break

        if not plugin_root or not plugin_root.is_dir():
            return

        required_files = {"entrypoint.py", "hook.py", "plugin.py"}
        for plugin_dir in sorted(plugin_root.iterdir()):
            if plugin_dir.is_dir() and plugin_dir.name != "__pycache__" and not plugin_dir.name.startswith("."):
                for req in required_files:
                    if not (plugin_dir / req).exists():
                        self.add_message("missing-plugin-file", node=node, args=(req, plugin_dir.name))

    def visit_importfrom(self, node: nodes.ImportFrom) -> None:
        """
        Detect cross-plugin imports (from ... import ...).

        Responsibility:
            Detect cross-plugin imports (from . It directly owns the observable contract, local decisions, and
            maintenance boundary for this method. That boundary is intentionally stated in prose so maintainers can
            distinguish owned work from collaborators before editing.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd._pylint.checkers.plugin_patterns.PluginPatternsChecker.visit_importfrom` because it keeps the
            nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - self._get_current_plugin_name: collaborator call used by this boundary
            - node.modname.split: collaborator call used by this boundary
            - len: collaborator call used by this boundary
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
            mutates current_plugin, parts, imported_plugin.

        Invariants:
            - `pytest_bdd._pylint.checkers.plugin_patterns.PluginPatternsChecker.visit_importfrom` keeps its documented
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
        current_plugin = self._get_current_plugin_name(node)
        if not current_plugin:
            return

        if node.modname is None:
            return

        parts = node.modname.split(".")
        if len(parts) >= 3 and parts[0] == "pytest_bdd" and parts[1] == "plugin":
            imported_plugin = parts[2]
            if imported_plugin != current_plugin:
                self.add_message("cross-plugin-import", node=node, args=(imported_plugin, current_plugin))

    def visit_import(self, node: nodes.Import) -> None:
        """
        Detect cross-plugin imports (import ...).

        Responsibility:
            Detect cross-plugin imports (import ...). It directly owns the observable contract, local decisions, and
            maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd._pylint.checkers.plugin_patterns.PluginPatternsChecker.visit_import` because it keeps the
            nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - self._get_current_plugin_name: collaborator call used by this boundary
            - name.split: collaborator call used by this boundary
            - len: collaborator call used by this boundary
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
            mutates current_plugin, parts, imported_plugin.

        Invariants:
            - `pytest_bdd._pylint.checkers.plugin_patterns.PluginPatternsChecker.visit_import` keeps its documented
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
        current_plugin = self._get_current_plugin_name(node)
        if not current_plugin:
            return

        for name, _ in node.names:
            parts = name.split(".")
            if len(parts) >= 3 and parts[0] == "pytest_bdd" and parts[1] == "plugin":
                imported_plugin = parts[2]
                if imported_plugin != current_plugin:
                    self.add_message("cross-plugin-import", node=node, args=(imported_plugin, current_plugin))

    def visit_subscript(self, node: nodes.Subscript) -> None:
        """
        Detect direct stash access via subscript (e.g. config.stash[key]).

        Responsibility:
            Detect direct stash access via subscript (e.g. It directly owns the observable contract, local decisions,
            and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd._pylint.checkers.plugin_patterns.PluginPatternsChecker.visit_subscript` because it keeps the
            nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - self._is_in_plugin_file_requiring_stash_check: collaborator call used by this boundary
            - isinstance: collaborator call used by this boundary
            - self.add_message: collaborator call used by this boundary
            - node.root: collaborator call used by this boundary

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
        if not self._is_in_plugin_file_requiring_stash_check(node):
            return

        if isinstance(node.value, nodes.Attribute) and node.value.attrname == "stash":
            self.add_message("direct-stash-access", node=node, args=(node.root().name,))

    def visit_call(self, node: nodes.Call) -> None:
        """
        Detect direct stash access via method call (e.g. config.stash.get(key)).

        Responsibility:
            Detect direct stash access via method call (e.g. It directly owns the observable contract, local decisions,
            and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd._pylint.checkers.plugin_patterns.PluginPatternsChecker.visit_call` because it keeps the nearest
            code, data shape, call signature, and failure knowledge together.

        Delegates:
            - isinstance: collaborator call used by this boundary
            - self._is_in_plugin_file_requiring_stash_check: collaborator call used by this boundary
            - self.add_message: collaborator call used by this boundary
            - node.root: collaborator call used by this boundary

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
        if not self._is_in_plugin_file_requiring_stash_check(node):
            return

        if (
            isinstance(node.func, nodes.Attribute)
            and node.func.attrname == "get"
            and isinstance(node.func.expr, nodes.Attribute)
            and node.func.expr.attrname == "stash"
        ):
            self.add_message("direct-stash-access", node=node, args=(node.root().name,))

    def _get_current_plugin_name(self, node: nodes.NodeNG) -> str | None:
        """
        Responsibility:
            Responsibility: Responsibility:
            `pytest_bdd._pylint.checkers.plugin_patterns.PluginPatternsChecker._get_current_plugin_name` owns documented
            method behavior. It directly owns the observable contract, local decisions, and maintenance boundary for
            this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd._pylint.checkers.plugin_patterns.PluginPatternsChecker._get_current_plugin_name` because it
            keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - node.root: collaborator call used by this boundary
            - name.split: collaborator call used by this boundary
            - len: collaborator call used by this boundary
            - str: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - None found by static import/name scan; verify dynamic use before refactor

        State and side effects:
            mutates name, parts.

        Invariants:
            - `pytest_bdd._pylint.checkers.plugin_patterns.PluginPatternsChecker._get_current_plugin_name` keeps its
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
        name = node.root().name
        if not name:
            return None
        parts = name.split(".")
        if len(parts) >= 3 and parts[0] == "pytest_bdd" and parts[1] == "plugin":
            return str(parts[2])
        return None

    def _is_in_plugin_file_requiring_stash_check(self, node: nodes.NodeNG) -> bool:
        """
        Responsibility:
            Responsibility: Responsibility:
            `pytest_bdd._pylint.checkers.plugin_patterns.PluginPatternsChecker._is_in_plugin_file_requiring_stash_check`
            owns documented method behavior. It directly owns the observable contract, local decisions, and maintenance
            boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd._pylint.checkers.plugin_patterns.PluginPatternsChecker._is_in_plugin_file_requiring_stash_check`
            because it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - self._get_current_plugin_name: collaborator call used by this boundary
            - Path: collaborator call used by this boundary
            - node.root: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - None found by static import/name scan; verify dynamic use before refactor

        State and side effects:
            mutates current_plugin, filename.

        Invariants:
            - `pytest_bdd._pylint.checkers.plugin_patterns.PluginPatternsChecker._is_in_plugin_file_requiring_stash_check`
              keeps its documented import path, ownership boundary, and observable behavior stable for callers.

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
        current_plugin = self._get_current_plugin_name(node)
        if not current_plugin:
            return False

        filename = Path(node.root().file).name
        if filename in {"stash_access.py", "exception.py"}:
            return False

        return True
