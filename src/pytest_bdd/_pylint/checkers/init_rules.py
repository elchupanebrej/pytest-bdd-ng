"""
Enforces project conventions for `__init__.py` files and import aliases.

Responsibility:
    Enforces project conventions for `__init__.py` files and import aliases. Validates four rules:
    BLQ1401 forbids defining `__all__` in non-`__init__.py` files; BLQ1402 flags `__init__.py` files
    that are empty or contain only classification comments (like `# init: allow`); BLQ1403 requires
    `__init__.py` to contain actual code or an empty `__all__ = []` — fires on docstring-only files
    and non-empty `__all__`; BLQ1404 forbids redundant import aliases where `import x as x` or
    `from y import z as z` (the alias matches the original name). Files containing the
    `# init: no-check` comment are exempt from all rules.

Reason for existence:
    This module is the single authority on `__init__.py` hygiene for the project. The rules encode a specific
    philosophy: `__init__.py` files should either contain real code (imports, function/class definitions) or
    be deleted (PEP 420 namespace packages), never exist as empty shells or docstring-only placeholders. The
    `__all__` prohibition prevents accidental public API surface expansion. The alias rule catches
    copy-paste artifacts like `import os as os`. These rules are tightly coupled — they all operate on the
    same file type (`__init__.py`) and share the same exemption mechanism (`# init: no-check`), making
    co-location logical. Separating them from general quality gates prevents the QualityGatesChecker from
    accumulating unrelated domain rules.

Delegates:
    - Path.read_text: Reads source files to check for `# init: no-check` exemption comments in `_is_exempt`.
    - Path.read_text: Also used in `visit_module` to strip classification comments and detect empty inits.
    - self._is_exempt: Determines whether a file contains the `# init: no-check` exemption marker.
    - self.add_message: Reports BLQ1401-BLQ1404 violations to Pylint.

Cohesion:
    All logic revolves around `__init__.py` validation and import alias checking. The classification
    comments constant (`CLASSIFICATION_COMMENTS`) is shared between `visit_module` and the broader check
    context. The exemption method `_is_exempt` is shared across all visitor methods. Every method
    operates on the same file-type domain and shares the same guard conditions (skip `pytest_bdd_testing`,
    check exemption).

Separation:
    - quality_gates.py: QualityGatesChecker handles code patterns (return None, except, test classes);
      this module handles __init__.py structural rules and import alias hygiene.
    - file_size_rules.py: FileSizeRulesChecker handles quantitative file metrics; this module handles
      init-file content rules.
    - test_import_rules.py: TestImportRulesChecker handles test import path validation; this module
      handles all-file import alias validation.

Main consumers:
    - pytest_bdd._pylint.register(): Loads `InitRulesChecker` into Pylint during plugin startup.
    - Pylint's visitors: Calls `visit_module`, `visit_import`, `visit_importfrom`, and `visit_assign`
      during AST traversal.

State and side effects:
    None, keeps no persistent state. The `_is_exempt` method reads source files from disk on each call
    (not cached). `visit_module` also reads source files for content inspection. All file reads are
    guarded by try/except for OSError and UnicodeDecodeError.

Invariants:
    - `EXEMPT_COMMENT` ("# init: no-check") in a file suppresses ALL init-rules checks for that file.
    - `CLASSIFICATION_COMMENTS` are stripped before checking if an init file is empty (BLQ1402).
    - Files under `pytest_bdd_testing/` in their path are always exempt.
    - `__all__` definitions are flagged regardless of exemption status (the check in `visit_assign` runs
      before exemption is checked, but the exemption IS checked).
    - Import alias checks (BLQ1404) require `asname == name` — the alias must exactly match the original.

Architecture score:
    #arch-eval:reason_for_existence=5
    #arch-eval:owned_responsibility=5
    #arch-eval:delegation_boundary=4
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
    A Pylint `BaseChecker` that enforces four project-specific rules for `__init__.py` files and import
    hygiene: BLQ1401 .

    Responsibility:
    A Pylint `BaseChecker` that enforces four project-specific rules for `__init__.py` files and import
    hygiene: BLQ1401 forbids defining `__all__` in non-`__init__.py` files (detected via `visit_assign` on
    `AssignName` targets named `__all__`); BLQ1402 flags `__init__.py` files that are empty or contain only
    classification comments after stripping known markers; BLQ1403 flags `__init__.py` files that contain
    only a docstring with no imports or code definitions, OR define a non-empty `__all__` list;
    BLQ1404 flags redundant import aliases where the alias matches the original name in both
    `import x as x` and `from y import z as z` forms. Files containing `# init: no-check` are exempt,
    as are files under `pytest_bdd_testing/`.

    Reason for existence:
        This checker encodes the project's opinionated stance on `__init__.py` files: they must either
        contain real code or not exist at all. Empty `__init__.py` files, docstring-only files, and
        `__all__` definitions are all forbidden. These rules are enforced programmatically rather than by
        convention because manual review is unreliable. The checker also catches a common anti-pattern —
        redundant import aliases like `import typing as typing` — that tools like ruff don't flag. The
        exemption mechanism (`# init: no-check`) allows legitimate exceptions (like this checker's own
        module) without weakening the rules globally. This checker is separate from QualityGatesChecker
        because init-file rules are structural/file-level, not code-pattern-level.

    Delegates:
        - self._is_exempt: Checks whether a file contains the `# init: no-check` marker by reading the
          file from disk.
        - Path.read_text: Used by `_is_exempt` and `visit_module` to read file contents.
        - self.add_message: Reports BLQ1401-BLQ1404 violations to Pylint.

    Cohesion:
        Every visitor method and helper in this class relates to `__init__.py` file or import alias
        validation. `visit_module` handles the file-level rules (BLQ1402, BLQ1403), `visit_assign` handles
        `__all__` detection (BLQ1401), `visit_import` and `visit_importfrom` handle alias detection
        (BLQ1404), and `_is_exempt` provides the shared exemption check. All methods share the same guard
        pattern: check filepath exists, skip `pytest_bdd_testing`, check exemption.

    Separation:
        - QualityGatesChecker: Handles code-pattern quality rules (return None, bare except, test classes)
          at the AST statement level; this checker handles structural init-file rules.
        - FileSizeRulesChecker: Handles file size metrics; this checker handles init content rules.
        - TypingRulesChecker: Handles type:ignore comment rules; this checker handles import alias hygiene.

    Main consumers:
        - pytest_bdd._pylint.register(): Instantiates and registers this checker with Pylint.
        - Pylint AST visitors: Calls `visit_module`, `visit_assign`, `visit_import`, `visit_importfrom`.

    State and side effects:
        None, keeps no persistent state. The `_is_exempt` method reads files from disk on every call
        without caching. `visit_module` also reads files for content inspection. All file reads are
        guarded against OSError and UnicodeDecodeError.

    Invariants:
        - `EXEMPT_COMMENT` = "# init: no-check" suppresses ALL checks for the file containing it.
        - `CLASSIFICATION_COMMENTS` are stripped before evaluating emptiness for BLQ1402.
        - Only files named `__init__.py` are checked for BLQ1402 and BLQ1403.
        - BLQ1404 fires only when `asname == name` (exact string match).
        - Files under `pytest_bdd_testing/` are always exempt.

    Architecture score:
        #arch-eval:reason_for_existence=5
        #arch-eval:owned_responsibility=5
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=5
        #arch-eval:consumer_clarity=5
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=5
        #arch-eval:locational_stability=5
    """

    name = "init-rules"

    msgs = {
        "E9051": (
            "BLQ1401: %s defines __all__ outside __init__.py. Remove __all__ list entirely.",
            "all-defined",
            "BLQ1401: Defining __all__ in non-__init__.py files is forbidden.",
        ),
        "E9052": (
            "BLQ1402: %s is empty or metadata-only. Delete this file (PEP 420).",
            "empty-init",
            "BLQ1402: Empty or metadata-only __init__.py files must be deleted.",
        ),
        "E9053": (
            "BLQ1403: %s — add actual code, use __all__ = [], or delete.",
            "init-code-required",
            "BLQ1403: __init__.py must contain actual code or empty __all__ = [].",
        ),
        "E9054": (
            "BLQ1404: imports '%s as %s'. Remove the 'as %s' alias.",
            "redundant-import-alias",
            "BLQ1404: Redundant import aliases are forbidden.",
        ),
    }

    def visit_assign(self, node: nodes.Assign) -> None:
        """
        Visits every assignment statement in the AST and checks if any assignment target is named
        `__all__`.

        Responsibility:
            Visits every assignment statement in the AST and checks if any assignment target is named
            `__all__`. If found in a non-`__init__.py` file that is not exempt (no `# init: no-check`),
            emits BLQ1401 (`all-defined`) to forbid `__all__` definitions outside `__init__.py`. Files
            under `pytest_bdd_testing/` and `__init__.py` files are skipped (`__all__` in `__init__.py`
            is validated by BLQ1403 in `visit_module`). This enforces the project convention that
            `__all__` should only be used as an empty list in `__init__.py`.

        Reason for existence:
            This method is the detection point for BLQ1401. It uses Pylint's `visit_assign` visitor hook
            because `__all__` is defined via assignment (`__all__ = [...]`), not via import or function
            definition. The exemption check via `_is_exempt` is applied after detecting the assignment
            target to allow legitimate exceptions. This separation keeps the `__all__` rule independent of
            the module-level init rules in `visit_module`.

        Delegates:
            - self._is_exempt: Called to check if the file contains `# init: no-check`.
            - self.add_message: Emits BLQ1401 when `__all__` is detected.

        Cohesion:
            This method does exactly one thing: check for `__all__` assignments. It does not inspect other
            assignment targets, import nodes, or module structure — those are handled by other visitor methods.

        Separation:
            - visit_module: Handles empty/docstring-only init checks (BLQ1402/BLQ1403); this method handles
              `__all__` detection (BLQ1401).
            - visit_import / visit_importfrom: Handle redundant alias detection (BLQ1404); this method
              handles assignment-based violations.

        Main consumers:
            - Pylint's AST visitor: Called automatically for every `Assign` node in the linted tree.

        State and side effects:
            Calls `_is_exempt` which reads the source file from disk. Calls `self.add_message()` to emit
            linting diagnostics. Does not cache or retain state between calls.

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
        filepath = node.root().file
        if not filepath or "pytest_bdd_testing" in filepath:
            return

        # __all__ in __init__.py is handled by BLQ1403 in visit_module
        if Path(filepath).name == "__init__.py":
            return

        for target in node.targets:
            if isinstance(target, nodes.AssignName) and target.name == "__all__":
                if not self._is_exempt(filepath):
                    self.add_message("all-defined", node=node, args=(filepath,))

    def visit_import(self, node: nodes.Import) -> None:
        """
        Visits every `import x as y` statement and checks for redundant aliases where `asname == name`
        (e.g., `import os as o.

        Responsibility:
            Visits every `import x as y` statement and checks for redundant aliases where `asname == name`
            (e.g., `import os as os`). If found and the file is not exempt, emits BLQ1404
            (`redundant-import-alias`). Files under `pytest_bdd_testing/` and exempt files are skipped.

        Reason for existence:
            This method catches a specific code smell — import aliases that rename a module to itself —
            which is typically a copy-paste artifact or leftover from a refactor. It operates on
            `nodes.Import` specifically because `import x as x` uses the `Import` AST node type, while
            `from y import z as z` uses `ImportFrom`. Having separate visitors for each import type keeps
            the logic simple and aligned with Pylint's visitor dispatch model.

        Delegates:
            - self._is_exempt: Called to check if the file contains `# init: no-check`.
            - self.add_message: Emits BLQ1404 when a redundant alias is detected.

        Cohesion:
            This method does one thing: iterate over `node.names` tuples and compare `asname` to `name`.
            It shares the exemption logic and message ID with `visit_importfrom`.

        Separation:
            - visit_importfrom: Handles the `from x import y as y` form; this method handles the
              `import x as x` form. Both implement BLQ1404 but for different AST node types.
            - visit_assign: Handles `__all__` detection (BLQ1401); unrelated to import aliases.

        Main consumers:
            - Pylint's AST visitor: Called automatically for every `Import` node.

        State and side effects:
            Calls `_is_exempt` which reads the source file from disk. Calls `self.add_message()` to emit
            diagnostics. No persistent state modifications.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=5
            #arch-eval:cohesion=5
            #arch-eval:separation=4
            #arch-eval:consumer_clarity=5
            #arch-eval:state_invariants=5
            #arch-eval:entity_fullness=2
            #arch-eval:locational_stability=5
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
        Visits every `from x import y as z` statement and checks for redundant aliases where
        `asname == name` (e.g., `from os.

        Responsibility:
            Visits every `from x import y as z` statement and checks for redundant aliases where
            `asname == name` (e.g., `from os import path as path`). If found and the file is not exempt,
            emits BLQ1404 (`redundant-import-alias`). Files under `pytest_bdd_testing/` and exempt files
            are skipped.

        Reason for existence:
            This method mirrors `visit_import` but targets `ImportFrom` nodes, which represent
            `from ... import ...` statements. The alias comparison logic is identical, but the AST node
            type differs, requiring a separate Pylint visitor. Both methods together provide complete
            coverage for redundant aliases across all import forms.

        Delegates:
            - self._is_exempt: Called to check if the file contains `# init: no-check`.
            - self.add_message: Emits BLQ1404 when a redundant alias is detected.

        Cohesion:
            This method does one thing: iterate over `node.names` tuples from an `ImportFrom` node and
            compare `asname` to `name`. It shares the exemption logic, guard conditions, and message ID
            with `visit_import`.

        Separation:
            - visit_import: Handles the `import x as x` form; this method handles the `from x import y as y`
              form. Both implement BLQ1404 but for different AST node types.
            - visit_assign: Handles `__all__` detection (BLQ1401); unrelated to import aliases.

        Main consumers:
            - Pylint's AST visitor: Called automatically for every `ImportFrom` node.

        State and side effects:
            Calls `_is_exempt` which reads the source file from disk. Calls `self.add_message()` to emit
            diagnostics. No persistent state modifications.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=5
            #arch-eval:cohesion=5
            #arch-eval:separation=4
            #arch-eval:consumer_clarity=5
            #arch-eval:state_invariants=5
            #arch-eval:entity_fullness=2
            #arch-eval:locational_stability=5
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
        Validate `__init__.py` files for content rules: BLQ1402 fires when an `__init__.py` file
        is empty or contains only classification comments; BLQ1403 fires when an `__init__.py` file
        contains only a docstring with no actual code, OR defines a non-empty `__all__`.

        Responsibility:
            Validates `__init__.py` files for two content rules: BLQ1402 fires when an `__init__.py` file
            is empty or contains only classification comments (like `# init: allow`, `# init: package-marker`)
            after stripping them; BLQ1403 fires when an `__init__.py` file contains only a docstring with
            no imports or code definitions, OR defines a non-empty `__all__` list (`__all__ = []`
            is allowed and prevents the docstring-only violation). Only files named
            `__init__.py` are checked. Files under `pytest_bdd_testing/` and exempt files are skipped.

        Reason for existence:
            This method implements the project's "no empty __init__.py" policy at the AST level. It
            distinguishes between truly empty files, comment-only files (BLQ1402), docstring-only
            files (BLQ1403), and non-empty `__all__` violations (BLQ1403) by combining AST analysis
            (checking for Import, ImportFrom, FunctionDef, ClassDef, and Assign nodes) with source
            text inspection (stripping classification comments, checking for remaining content after
            stripping). The `__all__` check inspects the value node (List/Tuple.elts) to verify
            emptiness. The dual approach — AST for structural checks, text for comment stripping —
            is necessary because astroid doesn't preserve comment content.

        Delegates:
            - self._is_exempt: Called to check if the file contains `# init: no-check`.
            - Path.read_text: Reads the file content for comment stripping and emptiness detection.
            - self.add_message: Emits BLQ1402 or BLQ1403 when violations are found.

        Cohesion:
            This method logically groups the `__init__.py` content checks (empty, docstring-only, and
            non-empty `__all__`) because they share the same preconditions (must be `__init__.py`,
            must not be exempt) and the same AST inspection logic (scanning `node.body` for
            import/code/assignment nodes). The file read and comment stripping are shared
            infrastructure for all checks.

        Separation:
            - visit_assign: Handles __all__ detection in non-__init__.py files (BLQ1401); this method
              handles __all__ validation within __init__.py via BLQ1403.
            - visit_import / visit_importfrom: Handle alias detection (BLQ1404) as separate visitors.
            - QualityGatesChecker.visit_module: Handles unrelated quality gate checks.

        Main consumers:
            - Pylint's module visitor: Called automatically for every module in the linted tree.

        State and side effects:
            Reads the source file from disk via `Path.read_text()` for content inspection. Calls
            `self.add_message()` to emit diagnostics. Does not cache file contents between visits.

        Architecture score:
            #arch-eval:reason_for_existence=5
            #arch-eval:owned_responsibility=5
            #arch-eval:delegation_boundary=5
            #arch-eval:cohesion=5
            #arch-eval:separation=5
            #arch-eval:consumer_clarity=5
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=3
            #arch-eval:locational_stability=5
        """
        filepath = node.file
        if not filepath or "pytest_bdd_testing" in filepath:
            return
        if self._is_exempt(filepath):
            return

        path = Path(filepath)
        if path.name != "__init__.py":
            return

        has_imports = False
        has_all = False
        all_node = None
        has_code = False

        for child in node.body:
            if isinstance(child, (nodes.Import, nodes.ImportFrom)):
                has_imports = True
            elif isinstance(child, nodes.Assign):
                for target in child.targets:
                    if isinstance(target, nodes.AssignName) and target.name == "__all__":
                        has_all = True
                        all_node = child
                has_code = True
            elif isinstance(child, (nodes.FunctionDef, nodes.AsyncFunctionDef, nodes.ClassDef)):
                has_code = True

        # BLQ1403 (__all__): if __all__ is present in __init__.py, it must be empty
        if has_all:
            if all_node is not None:
                value = all_node.value
                if isinstance(value, (nodes.List, nodes.Tuple)):
                    if len(value.elts) > 0:
                        self.add_message(
                            "init-code-required",
                            node=node,
                            args=(filepath + " defines non-empty __all__",),
                        )
                        return
                else:
                    self.add_message(
                        "init-code-required",
                        node=node,
                        args=(filepath + " defines __all__ with non-list value",),
                    )
                    return
            return

        if has_imports:
            return

        try:
            source = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            return

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
            self.add_message(
                "init-code-required",
                node=node,
                args=(filepath + " contains only docstring",),
            )

    def _is_exempt(self, filepath: str) -> bool:
        """
        Determine whether a file is exempt from init-rules checks by reading the file from disk and
        checking for the presenc.

        Responsibility:
            Determines whether a file is exempt from init-rules checks by reading the file from disk and
            checking for the presence of the `# init: no-check` comment. Returns `True` if the comment
            is found anywhere in the file content, `False` otherwise. If the file cannot be read (any
            `Exception`), returns `False` to default to non-exempt status.

        Reason for existence:
            This method centralizes the exemption check used by all four visitor methods. Without it, each
            visitor would duplicate the file-read-and-search logic. The broad `except Exception` is
            intentional: if the file is unreadable for any reason (permissions, encoding, etc.), the safe
            default is to not suppress checks, ensuring violations in unreadable-but-valid files are still
            reported. The exemption mechanism allows legitimate init files (like this checker's own module)
            to opt out of rules they would otherwise violate.

        Delegates:
            - Path.read_text: Reads the file content from disk to search for the exemption comment.

        Cohesion:
            This method does exactly one thing: return a boolean indicating exemption status. It has no
            side effects beyond a file read, and its logic is not coupled to any specific rule.

        Separation:
            - All four visitor methods: Each calls `_is_exempt` as a precondition; the method itself is
              rule-agnostic and doesn't know which rule is being checked.
            - QualityGatesChecker._has_noqa_for_rule: A different exemption mechanism for quality gates;
              this one checks for a specific file-level comment rather than per-line noqa annotations.

        Main consumers:
            - InitRulesChecker.visit_assign, visit_import, visit_importfrom, visit_module: All four
              visitor methods call this as a guard condition.

        State and side effects:
            Reads the source file from disk via `Path.read_text()`. Does not cache results — each call
            reads the file anew. No mutation of `self` or external state.

        Architecture score:
            #arch-eval:reason_for_existence=5
            #arch-eval:owned_responsibility=5
            #arch-eval:delegation_boundary=5
            #arch-eval:cohesion=5
            #arch-eval:separation=5
            #arch-eval:consumer_clarity=5
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=2
            #arch-eval:locational_stability=5
        """
        try:
            source = Path(filepath).read_text(encoding="utf-8")
            return EXEMPT_COMMENT in source
        except Exception:  # noqa: BLE001  -- defensive read; file may be unreadable or non-Python; absence of comment is safe
            return False
