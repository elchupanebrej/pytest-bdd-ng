"""
Enforces structural and import conventions for pytest-bdd-ng plugins located under
`pytest_bdd.plugin.*`.

Responsibility:
    Enforces structural and import conventions for pytest-bdd-ng plugins located under
    `pytest_bdd.plugin.*`. Validates three rules: BLQ1001 (missing-plugin-file) fires when a plugin
    directory is missing any of the three required files — `entrypoint.py`, `hook.py`, or `plugin.py`;
    BLQ1002 (cross-plugin-import) fires when a plugin module imports from a different plugin package
    (e.g., a reporting plugin importing directly from another reporting plugin) — inter-plugin
    communication must use hooks instead; BLQ1003 (direct-stash-access) fires when code in plugin
    files accesses `config.stash[...]` or calls `config.stash.get(...)` directly instead of through
    a `StashBound` subclass, with `stash_access.py` and `exception.py` exempted from this check.

Reason for existence:
    This module is the programmatic enforcement of the project's plugin architecture conventions.
    The required-file check ensures every plugin has a consistent structure (entrypoint, hooks,
    plugin implementation). The cross-plugin import prohibition prevents tight coupling between
    sibling plugins — the reporting layer must not have horizontal dependencies. The stash access
    rule enforces that `config.stash` is only accessed through `StashBound` subclasses, which
    provide typed, validated access patterns. These three rules are co-located because they all
    govern plugin-level conventions, but they operate on different AST nodes (module-level for
    file checks, import nodes for cross-plugin, subscript/call nodes for stash access), requiring
    multiple Pylint visitor methods within the same checker class.

Delegates:
    - self._check_missing_files: Walks the `plugin/` directory tree and checks each subdirectory
      for the presence of `entrypoint.py`, `hook.py`, and `plugin.py` (BLQ1001).
    - self._get_current_plugin_name: Extracts the plugin name (third dotted part) from the current
      module's fully qualified name, returning `None` for non-plugin modules.
    - self._is_in_plugin_file_requiring_stash_check: Returns `False` for `stash_access.py` and
      `exception.py` files where direct stash access is intentional; `True` for all other plugin files.
    - self.add_message: Reports BLQ1001, BLQ1002, or BLQ1003 violations.

Cohesion:
    All logic in this module serves plugin convention enforcement. The three rules (required files,
    cross-plugin imports, stash access) share the common concept of "plugin context" — they only
    apply to files under `pytest_bdd.plugin.*`. The `_get_current_plugin_name` helper is used by
    all three rule implementations. The `_is_in_plugin_file_requiring_stash_check` helper provides
    fine-grained exemptions for the stash rule. Despite operating on different AST node types, the
    rules are thematically unified.

Separation:
    - layer_rules.py: LayerRulesChecker also checks cross-plugin imports but at the architectural
      layer level (BLQ1302) using the DAG model; this checker enforces a simpler, convention-based
      rule (BLQ1002) at the plugin-name level without TOML configuration.
    - quality_gates.py: QualityGatesChecker handles code-pattern quality rules unrelated to plugin
      structure.
    - init_rules.py: InitRulesChecker handles __init__.py conventions unrelated to plugin structure.

Main consumers:
    - pytest_bdd._pylint.register(): Loads `PluginPatternsChecker` into Pylint during plugin startup.
    - Pylint visitors: Calls `visit_module`, `visit_importfrom`, `visit_import`, `visit_subscript`,
      and `visit_call` during AST traversal.

State and side effects:
    Holds a single mutable flag `self._checked_missing_files` (bool) to ensure the directory-scanning
    BLQ1001 check runs only once per Pylint session, regardless of how many modules are visited.
    The `_check_missing_files` method walks the filesystem via `Path.iterdir()` and checks file
    existence. No other persistent state. Visitor methods call `self.add_message()` to emit diagnostics.

Invariants:
    - BLQ1001 (missing file check) runs exactly once per Pylint session (guarded by `_checked_missing_files`).
    - Required files are `{"entrypoint.py", "hook.py", "plugin.py"}` — all three must exist.
    - Plugin root is discovered by walking up from the current file until a parent directory named
      `pytest_bdd` with a `plugin/` subdirectory is found.
    - BLQ1002 fires only when the imported plugin name (third dotted part of `pytest_bdd.plugin.X`)
      differs from the current plugin name.
    - BLQ1003 fires for `config.stash[...]` (subscript access) and `config.stash.get(...)` (call access)
      but is suppressed for files named `stash_access.py` or `exception.py`.
    - `__pycache__` and dot-prefixed directories are skipped in the missing-file check.

Architecture score:
    #arch-eval:reason_for_existence=5
    #arch-eval:owned_responsibility=5
    #arch-eval:delegation_boundary=5
    #arch-eval:cohesion=4
    #arch-eval:separation=5
    #arch-eval:consumer_clarity=5
    #arch-eval:state_invariants=4
    #arch-eval:entity_fullness=5
    #arch-eval:locational_stability=5
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
    A Pylint `BaseChecker` that enforces three plugin-level conventions for all modules under
    `pytest_bdd.plugin.*`.

    Responsibility:
        A Pylint `BaseChecker` that enforces three plugin-level conventions for all modules under
        `pytest_bdd.plugin.*`. First, BLQ1001 ensures each plugin subdirectory contains the three
        required files (`entrypoint.py`, `hook.py`, `plugin.py`) — checked once per session via
        `_check_missing_files` during the first `visit_module`. Second, BLQ1002 prevents cross-plugin
        imports by checking that `visit_importfrom` and `visit_import` do not import from a different
        plugin package (e.g., `cucumber_json` importing from `cucumber_pretty`). Third, BLQ1003
        prevents direct `config.stash` access in plugin files by intercepting `visit_subscript` for
        `config.stash[...]` patterns and `visit_call` for `config.stash.get(...)` patterns, exempting
        `stash_access.py` and `exception.py` where such access is intentional.

    Reason for existence:
        This checker enforces the architectural principle that pytest-bdd plugins should be
        self-contained with well-defined interfaces. The required-file convention ensures every
        plugin has a standard structure discoverable by tooling. The cross-plugin import prohibition
        prevents the reporting layer from developing hidden dependencies between sibling plugins —
        all inter-plugin communication must go through pytest hooks, which are the documented
        extension point. The stash access rule enforces that `config.stash` (pytest's key-value
        store) is only accessed through `StashBound` subclasses, which provide typed access and
        prevent key-name typos. These three rules are co-located because they share the common
        concept of "plugin context" and the `_get_current_plugin_name` helper, but each rule
        requires a different Pylint visitor method.

    Delegates:
        - self._check_missing_files: Walks the plugin directory tree to find missing required files.
        - self._get_current_plugin_name: Extracts the plugin name from the module's dotted path.
        - self._is_in_plugin_file_requiring_stash_check: Determines if stash checks should apply
          (excludes `stash_access.py` and `exception.py`).
        - self.add_message: Reports violations for all three rules.

    Cohesion:
        All methods serve the single theme of plugin convention enforcement. The three rules
        (file structure, import boundaries, stash access) are different facets of the same
        architectural concern: plugins should be well-structured, loosely coupled, and use
        approved access patterns. The shared helpers (`_get_current_plugin_name`,
        `_is_in_plugin_file_requiring_stash_check`) reinforce this cohesion.

    Separation:
        - LayerRulesChecker: Also checks cross-plugin imports (BLQ1302) but via the formal
          layer DAG with TOML configuration; this checker uses a simpler plugin-name comparison
          (BLQ1002) without external configuration.
        - QualityGatesChecker: Handles general code quality rules unrelated to plugin architecture.
        - InitRulesChecker: Handles __init__.py content rules unrelated to plugin structure.

    Main consumers:
        - pytest_bdd._pylint.register(): Instantiates and registers this checker.
        - Pylint visitors: Dispatches `visit_module`, `visit_importfrom`, `visit_import`,
          `visit_subscript`, and `visit_call`.

    State and side effects:
        Holds `self._checked_missing_files` (bool, initially `False`) to ensure the filesystem
        walk for BLQ1001 runs exactly once. The `_check_missing_files` method performs directory
        iteration via `Path.iterdir()`. Visitor methods call `self.add_message()` to emit
        diagnostics. No file reading beyond directory listing.

    Invariants:
        - BLQ1001 runs only on the first `visit_module` call (`_checked_missing_files` guard).
        - Required files: `{"entrypoint.py", "hook.py", "plugin.py"}`.
        - Plugin root is found by walking up parent directories to find `pytest_bdd/plugin/`.
        - BLQ1002 fires when `imported_plugin != current_plugin` for `pytest_bdd.plugin.*` modules.
        - BLQ1003 fires for `config.stash[...]` and `config.stash.get(...)` in non-exempt plugin files.
        - `stash_access.py` and `exception.py` are permanently exempt from BLQ1003.
        - `__pycache__` and dot-prefixed directories are skipped in the missing-file check.

    Architecture score:
        #arch-eval:reason_for_existence=5
        #arch-eval:owned_responsibility=5
        #arch-eval:delegation_boundary=5
        #arch-eval:cohesion=4
        #arch-eval:separation=5
        #arch-eval:consumer_clarity=5
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=5
        #arch-eval:locational_stability=5
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
        Initialize the checker by calling the parent `BaseChecker.__init__` and setting the
        `_checked_missing_files` flag to.

        Responsibility:
            Initializes the checker by calling the parent `BaseChecker.__init__` and setting the
            `_checked_missing_files` flag to `False`. This flag ensures the filesystem-scanning
            BLQ1001 check (missing plugin files) runs exactly once per Pylint session, on the
            first `visit_module` call, rather than redundantly on every module visited.

        Reason for existence:
            This constructor exists to initialize the one-time guard flag. Without it, the missing-
            file check would run on every module visit, performing redundant filesystem operations.
            The flag pattern is necessary because Pylint's visitor model calls `visit_module` for
            every file in the project, but the plugin directory structure only needs to be validated
            once per linting run.

        Delegates:
            - super().__init__: Standard Pylint BaseChecker initialization.

        Cohesion:
            This method does exactly one initialization step: set the guard flag. Nothing else.

        Separation:
            - _check_missing_files: Uses the flag set here; the constructor doesn't know what the
              flag controls, only that it needs to start as `False`.

        Main consumers:
            - pytest_bdd._pylint.register(): Instantiates the checker during plugin registration.

        State and side effects:
            Sets `self._checked_missing_files = False`. No I/O, no external mutations.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=5
            #arch-eval:cohesion=5
            #arch-eval:separation=5
            #arch-eval:consumer_clarity=5
            #arch-eval:state_invariants=5
            #arch-eval:entity_fullness=3
            #arch-eval:locational_stability=5
        """
        super().__init__(linter)
        self._checked_missing_files = False

    def visit_module(self, node: nodes.Module) -> None:
        """
        Delegate to `_check_missing_files(node)` on every module visit.

        Responsibility:
            Delegates to `_check_missing_files(node)` on every module visit. The actual check is
            guarded by `_checked_missing_files` inside `_check_missing_files`, so the filesystem
            scan runs only on the first call. Subsequent calls are no-ops.

        Reason for existence:
            This method is the Pylint visitor hook that triggers the plugin file structure check.
            It exists as a thin adapter because Pylint dispatches `visit_module` for every file
            in the project, but the underlying check only needs to run once. The `_checked_missing_files`
            guard inside `_check_missing_files` prevents redundant work.

        Delegates:
            - self._check_missing_files: Performs the actual plugin directory scan and missing-file
              detection.

        Cohesion:
            Single-line delegation. Its only purpose is to connect Pylint's `visit_module` hook to
            the once-per-session file check.

        Separation:
            - visit_importfrom / visit_import / visit_subscript / visit_call: These handle other
              plugin rules (cross-plugin imports, stash access) that must run on every relevant node.

        Main consumers:
            - Pylint's module visitor: Called automatically for every module.

        State and side effects:
            Indirectly triggers `_check_missing_files` which may walk the filesystem and call
            `self.add_message()`. The `_checked_missing_files` flag may be set to `True`.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=5
            #arch-eval:cohesion=5
            #arch-eval:separation=4
            #arch-eval:consumer_clarity=5
            #arch-eval:state_invariants=5
            #arch-eval:entity_fullness=3
            #arch-eval:locational_stability=5
        """
        self._check_missing_files(node)

    def _check_missing_files(self, node: nodes.Module) -> None:
        """
        Perform a one-time filesystem scan of the `pytest_bdd/plugin/` directory tree to
        verify that every plugin subdirecto.

        Responsibility:
            Performs a one-time filesystem scan of the `pytest_bdd/plugin/` directory tree to
            verify that every plugin subdirectory contains the three required files:
            `entrypoint.py`, `hook.py`, and `plugin.py`. The check is guarded by
            `self._checked_missing_files` to run only once per Pylint session. The plugin root
            is discovered by walking up from the current file's path until a parent directory
            named `pytest_bdd` with a `plugin/` subdirectory is found. Skips `__pycache__` and
            dot-prefixed directories. For each missing required file, emits BLQ1001.

        Reason for existence:
            This method enforces the project's plugin structure convention: every plugin must have
            a standard layout with three specific files. The filesystem walk approach is used
            because this is a structural check (what files exist on disk) rather than a code-content
            check. The once-per-session guard prevents redundant filesystem operations across
            potentially hundreds of module visits. The parent-directory walk for finding the plugin
            root handles the case where Pylint is run from a subdirectory.

        Delegates:
            - Path.resolve / Path.parents: Filesystem operations to locate the plugin root.
            - plugin_root.iterdir: Iterates plugin subdirectories.
            - Path.exists: Checks for the presence of each required file.
            - self.add_message: Emits BLQ1001 for each missing file.

        Cohesion:
            Every line in this method serves the single goal of finding plugin directories and
            checking for required files. The root-finding logic, directory iteration, file
            existence checks, and message emission are all steps in this single pipeline.

        Separation:
            - visit_importfrom / visit_import: Handle cross-plugin import detection via AST;
              this method handles filesystem-level structure validation. They share the plugin
              concept but operate on different data sources (filesystem vs AST).
            - LayerRulesChecker._init_config: Also performs filesystem operations to find a
              config file, but for a different purpose (loading layers.toml vs scanning plugins).

        Main consumers:
            - PluginPatternsChecker.visit_module: The sole caller, invoked on the first module visit.

        State and side effects:
            Sets `self._checked_missing_files = True` (mutation). Walks the filesystem via
            `Path.iterdir()` and checks file existence. Calls `self.add_message()` for violations.
            No other state changes.

        Architecture score:
            #arch-eval:reason_for_existence=5
            #arch-eval:owned_responsibility=5
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=5
            #arch-eval:separation=5
            #arch-eval:consumer_clarity=5
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=5
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
        Detect cross-plugin imports from `from .

        Responsibility:
            Detects cross-plugin imports from `from ... import ...` statements. Extracts the current
            plugin name via `_get_current_plugin_name`, then checks if the imported module's path
            (from `node.modname`) is under `pytest_bdd.plugin.*` with a different third-level name
            than the current plugin. If so, emits BLQ1002 (cross-plugin-import). Returns early if
            the current file is not in a plugin, or if `node.modname` is `None`.

        Reason for existence:
            This method enforces the rule that plugin modules must not import directly from sibling
            plugins. The `ImportFrom` node type covers `from pytest_bdd.plugin.other import ...`
            statements. The plugin name extraction (at dotted position [2] of `pytest_bdd.plugin.X`)
            is the key comparison: if the imported plugin name differs from the current, it is a
            cross-plugin import. This is separate from `visit_import` because Pylint dispatches
            `import` and `from ... import` to different visitor methods.

        Delegates:
            - self._get_current_plugin_name: Extracts the current file's plugin name from its
              module path.
            - self.add_message: Emits BLQ1002 when a cross-plugin import is detected.

        Cohesion:
            This method does exactly one thing: check if a `from ... import` statement crosses
            plugin boundaries. The plugin name extraction and string comparison are straightforward.

        Separation:
            - visit_import: Handles the `import pytest_bdd.plugin.X` form; identical logic for a
              different AST node type.
            - visit_subscript / visit_call: Handle stash access rules (BLQ1003), unrelated to imports.

        Main consumers:
            - Pylint's import visitor: Called automatically for every `ImportFrom` node.

        State and side effects:
            Calls `_get_current_plugin_name` which reads `node.root().name`. Calls
            `self.add_message()` for violations. No persistent state changes.

        Architecture score:
            #arch-eval:reason_for_existence=5
            #arch-eval:owned_responsibility=5
            #arch-eval:delegation_boundary=5
            #arch-eval:cohesion=5
            #arch-eval:separation=4
            #arch-eval:consumer_clarity=5
            #arch-eval:state_invariants=5
            #arch-eval:entity_fullness=2
            #arch-eval:locational_stability=5
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
        Detect cross-plugin imports from `import ...` statements.

        Responsibility:
            Detects cross-plugin imports from `import ...` statements. For each imported name in
            `node.names`, splits the dotted path and checks if it is under `pytest_bdd.plugin.*`
            with a different third-level name than the current plugin. If so, emits BLQ1002
            (cross-plugin-import). Returns early if the current file is not in a plugin.

        Reason for existence:
            This method mirrors `visit_importfrom` but handles the `import pytest_bdd.plugin.X`
            form. Both methods implement BLQ1002 for different AST node types. The per-name loop
            handles cases like `import pytest_bdd.plugin.a, pytest_bdd.plugin.b`.

        Delegates:
            - self._get_current_plugin_name: Extracts the current file's plugin name.
            - self.add_message: Emits BLQ1002 for cross-plugin imports.

        Cohesion:
            Single-purpose method: check `import` statements for cross-plugin boundaries. The logic
            is nearly identical to `visit_importfrom` but adapted for the `Import` node structure.

        Separation:
            - visit_importfrom: Handles the `from ... import ...` form; identical rule for a
              different AST node type.
            - visit_subscript / visit_call: Handle stash access rules, unrelated to imports.

        Main consumers:
            - Pylint's import visitor: Called automatically for every `Import` node.

        State and side effects:
            Calls `_get_current_plugin_name`. Calls `self.add_message()` for violations. No
            persistent state changes.

        Architecture score:
            #arch-eval:reason_for_existence=5
            #arch-eval:owned_responsibility=5
            #arch-eval:delegation_boundary=5
            #arch-eval:cohesion=5
            #arch-eval:separation=4
            #arch-eval:consumer_clarity=5
            #arch-eval:state_invariants=5
            #arch-eval:entity_fullness=2
            #arch-eval:locational_stability=5
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
        Detect direct `config.stash[...]` subscript access in plugin files.

        Responsibility:
            Detects direct `config.stash[...]` subscript access in plugin files. Checks if the
            current file is in a plugin (via `_is_in_plugin_file_requiring_stash_check`), then
            inspects the subscript's value node: if it is an `Attribute` node whose `attrname` is
            `"stash"`, emits BLQ1003 (direct-stash-access). This catches patterns like
            `config.stash["key"]` and `self.config.stash["key"]`.

        Reason for existence:
            This method enforces the rule that `config.stash` must only be accessed through
            `StashBound` subclasses, which provide typed, validated access. Direct subscript
            access bypasses the type safety and validation that `StashBound` provides. The
            subscript visit is necessary because `config.stash["key"]` is represented as a
            `Subscript` node in the AST, not a `Call` node. The exemption check
            (`_is_in_plugin_file_requiring_stash_check`) excludes files like `stash_access.py`
            where direct access is the intended implementation.

        Delegates:
            - self._is_in_plugin_file_requiring_stash_check: Determines if the file should be
              checked (excludes `stash_access.py` and `exception.py`).
            - self.add_message: Emits BLQ1003 when direct stash access is detected.

        Cohesion:
            This method does one thing: check if a subscript operation accesses `config.stash`.
            It complements `visit_call` which checks for `config.stash.get(...)` patterns.

        Separation:
            - visit_call: Detects `config.stash.get(...)` patterns; this method detects
              `config.stash[...]` patterns. Together they cover both stash access forms.
            - visit_importfrom / visit_import: Handle cross-plugin import rules, unrelated.

        Main consumers:
            - Pylint's subscript visitor: Called automatically for every `Subscript` node.

        State and side effects:
            Calls `_is_in_plugin_file_requiring_stash_check` and `_get_current_plugin_name`
            (read-only). Calls `self.add_message()` for violations. No state changes.

        Architecture score:
            #arch-eval:reason_for_existence=5
            #arch-eval:owned_responsibility=5
            #arch-eval:delegation_boundary=5
            #arch-eval:cohesion=5
            #arch-eval:separation=5
            #arch-eval:consumer_clarity=5
            #arch-eval:state_invariants=5
            #arch-eval:entity_fullness=2
            #arch-eval:locational_stability=5
        """
        if not self._is_in_plugin_file_requiring_stash_check(node):
            return

        if isinstance(node.value, nodes.Attribute) and node.value.attrname == "stash":
            self.add_message("direct-stash-access", node=node, args=(node.root().name,))

    def visit_call(self, node: nodes.Call) -> None:
        """
        Detect direct `config.stash.get(...)` call access in plugin files.

        Responsibility:
            Detects direct `config.stash.get(...)` call access in plugin files. Checks if the
            current file is in a plugin (via `_is_in_plugin_file_requiring_stash_check`), then
            inspects the call's function node: if it is an `Attribute` node with `attrname == "get"`
            whose expression is itself an `Attribute` node with `attrname == "stash"`, emits
            BLQ1003. This catches patterns like `config.stash.get("key", default)`.

        Reason for existence:
            This method complements `visit_subscript` by detecting the method-call form of stash
            access. While `config.stash["key"]` is a subscript, `config.stash.get("key")` is a
            call, requiring a separate Pylint visitor. The two-level attribute check
            (`stash.get`) ensures we only flag the specific `config.stash.get(...)` pattern,
            not arbitrary `.get()` calls on other objects.

        Delegates:
            - self._is_in_plugin_file_requiring_stash_check: Determines if the file should be
              checked (excludes `stash_access.py` and `exception.py`).
            - self.add_message: Emits BLQ1003 when direct stash access is detected.

        Cohesion:
            Single-purpose: detect `config.stash.get(...)` calls. Complements `visit_subscript`
            for complete stash access coverage.

        Separation:
            - visit_subscript: Detects `config.stash[...]` patterns; this method detects
              `config.stash.get(...)` patterns. Together they cover both access forms.
            - visit_importfrom / visit_import: Handle cross-plugin import rules, unrelated.

        Main consumers:
            - Pylint's call visitor: Called automatically for every `Call` node.

        State and side effects:
            Calls `_is_in_plugin_file_requiring_stash_check`. Calls `self.add_message()` for
            violations. No persistent state changes.

        Architecture score:
            #arch-eval:reason_for_existence=5
            #arch-eval:owned_responsibility=5
            #arch-eval:delegation_boundary=5
            #arch-eval:cohesion=5
            #arch-eval:separation=5
            #arch-eval:consumer_clarity=5
            #arch-eval:state_invariants=5
            #arch-eval:entity_fullness=2
            #arch-eval:locational_stability=5
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
        Extract the plugin name from the current file's fully qualified module name.

        Responsibility:
            Extracts the plugin name from the current file's fully qualified module name. Splits
            the module name (from `node.root().name`) on dots and returns the third part (index 2)
            if the module path starts with `pytest_bdd.plugin.`. For example, for module
            `pytest_bdd.plugin.cucumber_json.reporter`, returns `"cucumber_json"`. Returns `None`
            if the module name is empty or the path doesn't have the expected structure.

        Reason for existence:
            This method is the shared helper for determining whether a file belongs to a plugin
            and which plugin it belongs to. It is used by all cross-plugin import checks and
            stash access checks to establish the "current plugin" context. The simple dotted-path
            parsing is sufficient because the project's plugin naming convention is consistent:
            all plugins are at `pytest_bdd.plugin.<name>.*`.

        Delegates:
            - node.root().name: Accesses the module's fully qualified name from the AST root.

        Cohesion:
            This method does exactly one thing: parse the module name to extract the plugin name.
            It has no knowledge of what the plugin name will be used for.

        Separation:
            - _is_in_plugin_file_requiring_stash_check: Uses the result to determine if stash
              checks apply; this method doesn't know about stash rules.
            - LayerRulesChecker._resolve_package: Similar module-name parsing but for layer
              resolution; this method is specific to plugin naming.

        Main consumers:
            - visit_importfrom, visit_import: Use it to get the current plugin for cross-plugin
              import detection.
            - _is_in_plugin_file_requiring_stash_check: Uses it as a precondition for stash checks.

        State and side effects:
            None, pure function. Reads `node.root().name` (immutable AST property) and returns
            a string or None.

        Architecture score:
            #arch-eval:reason_for_existence=5
            #arch-eval:owned_responsibility=5
            #arch-eval:delegation_boundary=5
            #arch-eval:cohesion=5
            #arch-eval:separation=5
            #arch-eval:consumer_clarity=5
            #arch-eval:state_invariants=5
            #arch-eval:entity_fullness=2
            #arch-eval:locational_stability=5
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
        Determine whether the current file should be subject to stash access checks (BLQ1003).

        Responsibility:
            Determines whether the current file should be subject to stash access checks (BLQ1003).
            First checks if the file belongs to a plugin via `_get_current_plugin_name`; returns
            `False` if not. Then checks the filename: if it is `stash_access.py` or `exception.py`,
            returns `False` because these files legitimately need direct stash access (they implement
            the `StashBound` base class and exception handling). All other plugin files return `True`.

        Reason for existence:
            This method provides the exemption mechanism for the stash access rule. The two exempted
            files (`stash_access.py` and `exception.py`) are the canonical places where direct stash
            access is intentional: `stash_access.py` defines the `StashBound` base class that wraps
            stash access, and `exception.py` may need direct access for error handling. Without this
            exemption, the stash rule would fire on its own implementation files.

        Delegates:
            - self._get_current_plugin_name: Determines if the file is in a plugin at all.
            - Path(node.root().file).name: Gets the base filename for exemption checking.

        Cohesion:
            This method does one thing: decide whether stash checks apply to a given file. It combines
            two criteria (is it a plugin file? is it an exempt file?) into a single boolean.

        Separation:
            - visit_subscript / visit_call: Both call this as a precondition; the method doesn't
              know which specific stash access pattern is being checked.

        Main consumers:
            - PluginPatternsChecker.visit_subscript, visit_call: Both use this as a guard before
              checking for stash access patterns.

        State and side effects:
            None, pure function. Reads AST properties and returns a boolean.

        Architecture score:
            #arch-eval:reason_for_existence=5
            #arch-eval:owned_responsibility=5
            #arch-eval:delegation_boundary=5
            #arch-eval:cohesion=5
            #arch-eval:separation=5
            #arch-eval:consumer_clarity=5
            #arch-eval:state_invariants=5
            #arch-eval:entity_fullness=2
            #arch-eval:locational_stability=5
        """
        current_plugin = self._get_current_plugin_name(node)
        if not current_plugin:
            return False

        filename = Path(node.root().file).name
        if filename in {"stash_access.py", "exception.py"}:
            return False

        return True
