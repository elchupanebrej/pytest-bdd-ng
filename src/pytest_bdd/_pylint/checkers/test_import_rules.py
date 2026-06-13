"""
Enforces that test modules are only imported from configured test collection paths.

Responsibility:
    Enforces that test modules are only imported from configured test collection paths. The
    primary rule BLQ1601 (test-import-outside-cases) fires when a `test_*` module import
    resolves to a file that is neither under the `src/pytest_bdd` library directory nor under
    any of the configured test collection paths (from `pyproject.toml`'s `tool.pytest.ini_options.testpaths`,
    defaulting to `["src/pytest_bdd_testing/cases"]`). Three module-level helper functions
    support the checker: `get_test_paths` reads the configured test paths from pyproject.toml,
    `get_test_package_prefixes` builds a list of dotted package prefixes from those paths for
    namespace matching, and `resolve_import_to_path` converts a dotted module name to a
    filesystem Path by searching under `src/` and configured test directories. Only imports
    whose full path starts with `test_` or contains `.test_` are checked, and only if the
    imported package is recognized as a project test package.

Reason for existence:
    This module prevents test code from being accidentally imported into production code or
    vice versa by ensuring test imports stay within designated test directories. The
    configurable test paths (via pyproject.toml) allow the enforcement to adapt to different
    project layouts without code changes. The three module-level helper functions are separate
    from the checker class because they represent reusable lookup logic (config reading, path
    resolution, prefix building) that could theoretically be used by other tooling. The
    checker itself handles the AST-traversal concern of detecting import statements and
    validating them against the configured paths. This module is separate from
    `layer_rules.py` because it enforces a different architectural concern: test isolation
    vs layer boundaries.

Delegates:
    - get_test_paths: Reads `pyproject.toml` to get configured test collection paths, falling
      back to `["src/pytest_bdd_testing/cases"]`.
    - get_test_package_prefixes: Builds dotted package prefix strings from test paths for
      namespace matching (e.g., `pytest_bdd_testing.cases.`).
    - resolve_import_to_path: Converts a dotted module name to a filesystem Path by searching
      under `src/` and test directories.
    - self._resolve_relative_module: Converts relative `ImportFrom` nodes to absolute module
      name strings.
    - self._check_test_import: The core validation method that checks whether a resolved import
      path is under a configured test path.
    - self.add_message: Reports BLQ1601 violations.

Cohesion:
    All logic in this module serves the single purpose of test import path enforcement. The
    three module-level functions provide the configuration-reading and path-resolution
    infrastructure. The checker class provides the AST-traversal and validation logic. The
    `_resolve_relative_module` and `_check_test_import` methods are supporting utilities
    for the two visitor methods (`visit_import`, `visit_importfrom`). No element of this
    module deals with non-test-import concerns.

Separation:
    - layer_rules.py: LayerRulesChecker enforces architectural layer boundaries for all
      imports; this module enforces test-to-production import isolation, a different
      architectural concern.
    - plugin_patterns.py: PluginPatternsChecker enforces cross-plugin import rules; this
      module enforces test import path rules.
    - init_rules.py: InitRulesChecker handles import alias rules; this module handles
      import location rules.

Main consumers:
    - pytest_bdd._pylint.register(): Loads `TestImportRulesChecker` into Pylint during
      plugin startup.
    - Pylint import visitors: Calls `visit_import` and `visit_importfrom` during AST traversal.
    - CI/CD: Ensures test imports don't leak outside configured test paths.

State and side effects:
    The checker class has no persistent state. The module-level functions `get_test_paths`
    and `get_test_package_prefixes` read `pyproject.toml` from disk on each call (no caching).
    `resolve_import_to_path` performs filesystem searches for module files.
    `_check_test_import` calls `resolve_import_to_path` which accesses the filesystem.
    All filesystem operations are read-only.

Invariants:
    - Default test paths: `["src/pytest_bdd_testing/cases"]` when pyproject.toml is absent or
      unreadable.
    - Only imports whose full dotted path starts with `test_` or contains `.test_` are checked.
    - Imports resolving to files under `src/pytest_bdd` (the library directory) are always allowed.
    - Imports under configured test paths (from `testpaths`) are always allowed.
    - Imports that resolve to unrecognized paths trigger BLQ1601.
    - Relative imports are resolved against the current module name with package-awareness.
    - `get_test_paths` wraps the entire pyproject.toml read in a broad try/except; any failure
      returns the default paths.
    - Package prefix matching is used as a secondary check when file resolution fails
      (the import's dotted path is compared against dotted test path prefixes).

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
# pylint: disable=file-too-long
from __future__ import annotations

from pathlib import Path
from typing import cast

from astroid import nodes
from pylint.checkers import BaseChecker


def get_test_paths() -> list[str]:
    """
    Read the configured test collection paths from `pyproject.toml`'s
    `[tool.pytest.ini_options]` section under the `tes.

    Responsibility:
        Reads the configured test collection paths from `pyproject.toml`'s
        `[tool.pytest.ini_options]` section under the `testpaths` key. If the file exists
        and is readable as TOML, returns the configured paths; otherwise returns the default
        `["src/pytest_bdd_testing/cases"]`. Uses `tomllib` (Python 3.11+) or `tomli` as a
        fallback for TOML parsing. The entire function is wrapped in a broad try/except so
        that any failure (missing file, malformed TOML, missing key) gracefully falls back
        to the default.

    Reason for existence:
        This function is the single source of truth for test path configuration. It
        centralizes the config-reading logic so that both `get_test_package_prefixes` and
        `resolve_import_to_path` (and potentially future consumers) can get consistent test
        paths without duplicating the TOML-read-and-fallback logic. The broad exception
        handling ensures the checker never crashes due to config issues — it degrades
        gracefully to the project's standard test path.

    Delegates:
        - Path.resolve / Path.exists: Filesystem operations to find and verify pyproject.toml.
        - tomllib.loads / tomli.loads: Parses the TOML content into Python dicts.
        - Path.read_text: Reads pyproject.toml from disk.

    Cohesion:
        This function does exactly one thing: return a list of test path strings. All the
        config-reading, parsing, and fallback logic serves this single purpose.

    Separation:
        - get_test_package_prefixes: Consumes the paths returned here to build dotted prefixes.
        - resolve_import_to_path: Consumes the paths to determine search roots.
        - TestImportRulesChecker._check_test_import: Consumes the paths via `get_test_paths()`
          to validate import locations.

    Main consumers:
        - get_test_package_prefixes: Builds package prefixes from these paths.
        - resolve_import_to_path: Uses these paths as search roots for file resolution.
        - TestImportRulesChecker._check_test_import: Uses these paths to validate if a
          resolved file is under a test directory.

    State and side effects:
        Reads `pyproject.toml` from disk via `Path.read_text()`. No caching — each call
        re-reads the file. No mutations of external state.

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
    try:
        pyproject_path = Path("pyproject.toml").resolve()
        if pyproject_path.exists():
            try:
                import tomllib
            except ImportError:
                import tomli as tomllib  # type: ignore[import-not-found, no-redef]  # fallback for python < 3.11
            pyproject = tomllib.loads(pyproject_path.read_text(encoding="utf-8"))
            paths = (
                pyproject
                .get("tool", {})
                .get("pytest", {})
                .get("ini_options", {})
                .get("testpaths", ["src/pytest_bdd_testing/cases"])
            )
            return cast("list[str]", paths)
    except Exception:  # noqa: BLE001  -- config read is best-effort; fall back to project default test paths
        pass
    return ["src/pytest_bdd_testing/cases"]


def get_test_package_prefixes() -> list[str]:
    """
    Build a list of dotted Python package prefix strings from the configured test paths.

    Responsibility:
        Builds a list of dotted Python package prefix strings from the configured test paths.
        Starts with the hardcoded prefixes `["pytest_bdd.", "pytest_bdd_testing."]`. For
        each path from `get_test_paths()`, converts the filesystem path to a dotted prefix
        (stripping `src/` if present), adds it with a trailing dot, and also scans immediate
        subdirectories (non-hidden, non-dunder) to add shorter prefixes. Returns the combined
        list for use in namespace matching.

    Reason for existence:
        This function translates filesystem paths into the Python import namespace prefixes
        needed for identifying test imports. For example, `src/pytest_bdd_testing/cases` becomes
        `pytest_bdd_testing.cases.`. The subdirectory scanning adds shorter prefixes like
        `cases.` so that both `from cases.test_x import y` and `from pytest_bdd_testing.cases.test_x import y`
        are recognized as test imports. This translation layer is necessary because Python
        imports use dotted names while `pyproject.toml` uses filesystem paths.

    Delegates:
        - get_test_paths: Provides the test path strings to convert.
        - Path.iterdir: Scans immediate subdirectories of test paths.

    Cohesion:
        This function does one thing: convert test filesystem paths to Python package prefixes.
        The hardcoded additions, path-to-dotted conversion, and subdirectory scanning all
        serve this single purpose.

    Separation:
        - get_test_paths: Provides the raw paths; this function translates them.
        - resolve_import_to_path: Does the reverse operation (module name → filesystem path).
        - TestImportRulesChecker._check_test_import: Consumes the prefixes for namespace matching.

    Main consumers:
        - TestImportRulesChecker._check_test_import: Uses the prefix list to determine if an
          imported module belongs to a test package.

    State and side effects:
        Calls `get_test_paths()` which reads `pyproject.toml` from disk. Scans directories
        via `Path.iterdir()`. No caching or persistent state.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=5
        #arch-eval:cohesion=5
        #arch-eval:separation=5
        #arch-eval:consumer_clarity=5
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=3
        #arch-eval:locational_stability=5
    """
    prefixes = ["pytest_bdd.", "pytest_bdd_testing."]
    for p in get_test_paths():
        p_path = Path(p)
        p_parts = p_path.parts
        if p_parts and p_parts[0] == "src":
            prefix = ".".join(p_parts[1:])
        else:
            prefix = ".".join(p_parts)
        if prefix:
            prefixes.append(prefix + ".")

        if p_path.is_dir():
            for sub in p_path.iterdir():
                if sub.is_dir() and not sub.name.startswith((".", "__")):
                    prefixes.append(sub.name + ".")
    return prefixes


def resolve_import_to_path(module_path: str) -> Path | None:
    """
    Resolve a dotted Python module name to a filesystem `Path` by searching under
    `src/` and all configured test directo.

    Responsibility:
        Resolves a dotted Python module name to a filesystem `Path` by searching under
        `src/` and all configured test directories. Splits the module path into parts and
        tries two file forms for each search root: `<root>/<parts>.py` (single-file module)
        and `<root>/<parts>/__init__.py` (package). Returns the first matching Path found,
        or `None` if the module cannot be resolved to any existing file. Deduplicates
        search roots to avoid redundant filesystem checks.

    Reason for existence:
        This function bridges the gap between Python's import namespace and the filesystem.
        When the checker encounters `from tests.unit.test_x import y`, it needs to verify
        that `tests/unit/test_x.py` actually exists and is under a configured test path.
        The search-root approach handles the fact that imports can resolve relative to
        multiple roots (src/ and test directories). The deduplication prevents redundant
        file-existence checks when the same root appears in multiple forms.

    Delegates:
        - get_test_paths: Provides the test directory paths for search roots.
        - Path.joinpath / Path.with_suffix / Path.is_file: Filesystem operations for
          constructing and checking candidate file paths.

    Cohesion:
        This function does one thing: convert a module name to a file path. The search-root
        construction, deduplication, and file-existence checking all serve this single purpose.

    Separation:
        - get_test_package_prefixes: Does the reverse (path → dotted name); this function
          does dotted name → path.
        - TestImportRulesChecker._check_test_import: Consumes the resolved path to validate
          its location.

    Main consumers:
        - TestImportRulesChecker._check_test_import: Called to resolve imported module names
          to filesystem paths for location validation.

    State and side effects:
        Calls `get_test_paths()` which reads `pyproject.toml`. Performs filesystem searches
        via `Path.is_file()`. No caching or state mutations.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=5
        #arch-eval:cohesion=5
        #arch-eval:separation=5
        #arch-eval:consumer_clarity=5
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=3
        #arch-eval:locational_stability=5
    """
    if not module_path:
        return None
    parts = module_path.split(".")

    search_roots = [Path("src").resolve()]
    for p in get_test_paths():
        search_roots.append(Path(p).resolve())

        p_path = Path(p)
        if len(p_path.parts) > 1:
            for parent in p_path.parents:
                if parent.name and parent.name != "src":
                    search_roots.append(parent.resolve())

    seen = set()
    unique_roots = []
    for r in search_roots:
        if r not in seen:
            seen.add(r)
            unique_roots.append(r)

    for root in unique_roots:
        candidate_file = root.joinpath(*parts).with_suffix(".py")
        if candidate_file.is_file():
            return candidate_file
        candidate_init = root.joinpath(*parts, "__init__.py")
        if candidate_init.is_file():
            return candidate_init

    return None


class TestImportRulesChecker(BaseChecker):
    """
    A Pylint `BaseChecker` that enforces test import isolation by validating that all
    imports of test modules (`test_*`) .

    Responsibility:
        A Pylint `BaseChecker` that enforces test import isolation by validating that all
        imports of test modules (`test_*`) resolve to files under configured test collection
        paths. The single rule BLQ1601 (test-import-outside-cases) fires when a test module
        import resolves to a file outside both `src/pytest_bdd/` (the library) and the
        configured test paths. Handles both absolute imports (`import test_x`) and relative
        imports (`from . import test_y`) via `_resolve_relative_module`. Only checks imports
        that are recognized as project test packages via namespace prefix matching.

    Reason for existence:
        This checker prevents accidental coupling between test code and production code by
        ensuring test modules are only imported from designated test directories. Without
        this enforcement, a developer might import a test utility into production code,
        creating a hidden dependency on test infrastructure. The checker uses a two-tier
        validation strategy: first, try to resolve the import to a filesystem path and
        check if it's under a test directory; second, if resolution fails, compare the
        dotted module name against test path prefixes. This handles both resolvable and
        unresolvable imports.

    Delegates:
        - get_test_paths: Provides the configured test directory paths for validation.
        - get_test_package_prefixes: Provides dotted package prefixes for namespace matching.
        - resolve_import_to_path: Converts module names to filesystem paths for location checks.
        - self._resolve_relative_module: Converts relative imports to absolute module names.
        - self._check_test_import: Core validation logic for a single import.
        - self.add_message: Reports BLQ1601 violations.

    Cohesion:
        All methods serve test import validation. The visitor methods (`visit_import`,
        `visit_importfrom`) are thin adapters that call `_check_test_import`. The
        `_resolve_relative_module` helper handles the relative-import case for
        `visit_importfrom`. The entire class is focused on one rule (BLQ1601) with one
        validation pipeline.

    Separation:
        - LayerRulesChecker: Enforces architectural layer boundaries for all imports using
          a DAG model; this checker enforces test isolation using filesystem path checks.
        - PluginPatternsChecker: Enforces cross-plugin import rules; this checker enforces
          test import location rules.
        - InitRulesChecker: Enforces import alias rules; this checker enforces import
          location rules.

    Main consumers:
        - pytest_bdd._pylint.register(): Instantiates and registers this checker.
        - Pylint import visitors: Calls `visit_import` and `visit_importfrom`.

    State and side effects:
        None, keeps no persistent state. Each visitor call is stateless. The `_check_test_import`
        method calls `resolve_import_to_path` which performs filesystem searches.
        Calls `get_test_paths` and `get_test_package_prefixes` which read `pyproject.toml`
        from disk (no caching). Messages emitted via `self.add_message()`.

    Invariants:
        - Only module names starting with `test_` or containing `.test_` are checked.
        - Imports resolving to files under `src/pytest_bdd/` (the library directory) are
          always allowed.
        - Imports resolving to files under any configured test path are always allowed.
        - Two special top-level packages `test_messages` and `test_init_rules` are always
          recognized as test packages.
        - Unresolvable imports are checked via dotted prefix matching against test paths.
        - Relative import resolution handles the `is_package` flag for correct level calculation.

    Architecture score:
        #arch-eval:reason_for_existence=5
        #arch-eval:owned_responsibility=5
        #arch-eval:delegation_boundary=5
        #arch-eval:cohesion=5
        #arch-eval:separation=5
        #arch-eval:consumer_clarity=5
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=5
        #arch-eval:locational_stability=5
    """

    name = "test-import-rules"

    msgs = {
        "E9071": (
            "BLQ1601: imported test '%s' resolves to '%s' which is not under configured collection path %s.",
            "test-import-outside-cases",
            "BLQ1601: Tests must only be imported from configured collection paths.",
        ),
    }

    def _resolve_relative_module(
        self,
        current_module: str | None,
        level: int,
        module: str | None = None,
        is_package: bool = False,
    ) -> str:
        """
        Convert a relative import to an absolute dotted module name.

        Responsibility:
            Converts a relative import to an absolute dotted module name. Starting from the
            current module's dotted name, pops one part for each relative level (adjusted
            by 1 if the current module is a package), then appends the optional module name
            if provided. For example, with `current_module="pytest_bdd_testing.cases.unit.test_x"`,
            `level=2`, `module="helpers"`, and `is_package=False`: pops `.test_x` and `.unit`,
            appends `helpers`, yielding `"pytest_bdd_testing.cases.helpers"`. Returns the
            resulting string, or the empty string if `current_module` is None.

        Reason for existence:
            This method handles the relative import resolution needed for `visit_importfrom`.
            Pylint's `ImportFrom` nodes represent relative imports via `level` (number of
            dots) and `modname`, but the checker needs absolute module names for path
            resolution. The `is_package` adjustment accounts for Python's import semantics
            where package `__init__.py` files are at a different level than regular modules.

        Delegates:
            - (none): Pure string/list manipulation with no external dependencies.

        Cohesion:
            This method does exactly one thing: convert relative import specs to absolute
            module names. The level adjustment, popping, and appending are all steps in
            this single conversion.

        Separation:
            - visit_importfrom: Calls this method when `node.level > 0` (relative import).
            - _check_test_import: Consumes the absolute module name this method produces.
            - LayerRulesChecker._resolve_imported_modules: Similar relative import resolution
              but for layer checking; this method is specific to test import validation.

        Main consumers:
            - TestImportRulesChecker.visit_importfrom: Called for relative `from ... import`
              statements.

        State and side effects:
            None, pure function. Takes strings and numbers, returns a string. No I/O, no
            mutations.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=3
            #arch-eval:cohesion=5
            #arch-eval:separation=5
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=5
            #arch-eval:entity_fullness=2
            #arch-eval:locational_stability=5
        """
        if not current_module:
            return ""
        parts = current_module.split(".")
        adjust = 1 if is_package else 0
        for _ in range(level - adjust):
            if parts:
                parts.pop()
        if module:
            parts.append(module)
        return ".".join(parts)

    def _check_test_import(self, node: nodes.NodeNG, module_path: str, imported_name: str | None = None) -> None:
        """
        Provide the core validation method for a single import.

        Responsibility:
            The core validation method for a single import. Constructs the full dotted path
            from `module_path` and `imported_name`. Skips the check if the path doesn't
            start with `test_` or contain `.test_`. Verifies the module belongs to a
            recognized test package (via `get_test_package_prefixes` prefix matching, plus
            the hardcoded `test_messages` and `test_init_rules` names). Attempts to resolve
            the full path to a filesystem Path via `resolve_import_to_path`; if the path is
            under `src/pytest_bdd/`, it's allowed. If the resolved file is not under any
            configured test path, emits BLQ1601. If the module can't be resolved to a file
            at all, checks via dotted prefix matching against test paths and emits BLQ1601
            if no match is found.

        Reason for existence:
            This method is the decision engine for test import validation. It implements a
            multi-tier check: first, is this even a test import? (name check). Second, is it
            our test package? (prefix check). Third, can we find the file? (resolution).
            Fourth, is the file in the right place? (path check). Fifth, if we can't find
            the file, does the dotted name still look like it belongs? (prefix fallback).
            This complexity warrants its own method separate from the visitor methods.

        Delegates:
            - get_test_package_prefixes: Provides dotted prefixes for namespace matching.
            - resolve_import_to_path: Converts the dotted module name to a filesystem Path.
            - get_test_paths: Provides test directory paths for location validation.
            - self.add_message: Emits BLQ1601 when the import is outside allowed paths.

        Cohesion:
            This method does one thing: determine if a test import is in the right location.
            All the checks (name filter, package filter, file resolution, path comparison,
            prefix fallback) are sequential steps in this single determination.

        Separation:
            - visit_import / visit_importfrom: Thin adapters that extract module/name info
              and call this method.
            - _resolve_relative_module: Handles relative-to-absolute conversion before this
              method is called for `ImportFrom` nodes.

        Main consumers:
            - TestImportRulesChecker.visit_import, visit_importfrom: Both call this method
              for each imported name.

        State and side effects:
            Calls `get_test_package_prefixes()` and `get_test_paths()` which may read
            `pyproject.toml`. Calls `resolve_import_to_path()` which searches the filesystem.
            Calls `self.add_message()` for violations. No persistent state changes.

        Architecture score:
            #arch-eval:reason_for_existence=5
            #arch-eval:owned_responsibility=5
            #arch-eval:delegation_boundary=5
            #arch-eval:cohesion=5
            #arch-eval:separation=5
            #arch-eval:consumer_clarity=5
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=5
        """
        full_path = (
            f"{module_path}.{imported_name}" if module_path and imported_name else (module_path or imported_name or "")
        )

        if not (full_path.startswith("test_") or ".test_" in full_path):
            return

        prefixes = get_test_package_prefixes()
        is_our_package = any(full_path.startswith(pref) for pref in prefixes) or full_path.split(".")[0] in {
            "test_messages",
            "test_init_rules",
        }
        if not is_our_package:
            return

        resolved_file = resolve_import_to_path(full_path)
        if not resolved_file:
            resolved_file = resolve_import_to_path(module_path)

        test_paths = [Path(p).resolve() for p in get_test_paths()]
        allowed_paths_str = ", ".join(str(p) for p in get_test_paths())

        if resolved_file:
            library_dir = Path("src/pytest_bdd").resolve()
            try:
                resolved_file.resolve().relative_to(library_dir)
                return
            except ValueError:
                pass

            is_under_test_paths = False
            for cases_dir in test_paths:
                try:
                    resolved_file.resolve().relative_to(cases_dir)
                    is_under_test_paths = True
                    break
                except ValueError:
                    pass

            if not is_under_test_paths:
                self.add_message(
                    "test-import-outside-cases",
                    node=node,
                    args=(full_path, resolved_file, allowed_paths_str),
                )
        else:
            dotted_prefixes = []
            for p in get_test_paths():
                p_parts = Path(p).parts
                if p_parts and p_parts[0] == "src":
                    prefix = ".".join(p_parts[1:])
                else:
                    prefix = ".".join(p_parts)
                dotted_prefixes.append(prefix)

            if not any(full_path.startswith(prefix) for prefix in dotted_prefixes):
                allowed_prefixes_str = ", ".join(dotted_prefixes)
                self.add_message(
                    "test-import-outside-cases",
                    node=node,
                    args=(full_path, "None", allowed_prefixes_str),
                )

    def visit_import(self, node: nodes.Import) -> None:
        """
        Pylint visitor for `import x` statements.

        Responsibility:
            Pylint visitor for `import x` statements. Iterates over each imported name
            (from `node.names`) and calls `_check_test_import(node, "", alias[0])` with
            an empty module path since `import` statements use absolute names directly.
            This covers imports like `import test_helpers` or `import pytest_bdd_testing.cases.test_x`.

        Reason for existence:
            This method is the Pylint visitor adapter for `Import` nodes. It extracts the
            imported name from each alias and passes it to `_check_test_import` with no
            module path prefix (since absolute imports don't need one). The empty string
            for `module_path` signals that the imported name is the full path.

        Delegates:
            - self._check_test_import: Performs the actual test import validation.

        Cohesion:
            Single-purpose adapter: iterate import names and dispatch to `_check_test_import`.
            The per-name loop handles multiple imports in one statement (`import a, b, c`).

        Separation:
            - visit_importfrom: Handles `from ... import ...` with module path extraction;
              this method handles `import ...` with direct name usage.

        Main consumers:
            - Pylint's import visitor: Called automatically for every `Import` node.

        State and side effects:
            Delegates to `_check_test_import` which may access the filesystem and emit
            messages. No direct side effects.

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
        for alias in node.names:
            self._check_test_import(node, "", alias[0])

    def visit_importfrom(self, node: nodes.ImportFrom) -> None:
        """
        Pylint visitor for `from x import y` statements.

        Responsibility:
            Pylint visitor for `from x import y` statements. Resolves the module path:
            if the import is relative (`node.level > 0`), delegates to
            `_resolve_relative_module` to convert to an absolute path using the current
            module name and package flag; otherwise uses `node.modname` directly. Then
            iterates over each imported name and calls `_check_test_import(node, module_path, alias[0])`
            with the resolved module path and each imported name.

        Reason for existence:
            This method handles the more complex `ImportFrom` case where the module path may
            be relative or absolute, and the imported name is separate from the module path.
            The relative import resolution is specific to this visitor — `visit_import`
            doesn't need it because `import` statements are always absolute without a level.

        Delegates:
            - self._resolve_relative_module: Converts relative imports to absolute paths.
            - self._check_test_import: Performs the actual test import validation.

        Cohesion:
            This method does two related things: resolve the module path (absolute or
            relative), then dispatch each imported name for validation. Both serve the
            single purpose of test import checking for `from ... import` statements.

        Separation:
            - visit_import: Handles `import ...` with simpler name extraction; this method
              handles the module + name split of `from ... import`.
            - _resolve_relative_module: Handles the relative-path math; this method
              orchestrates when to call it.

        Main consumers:
            - Pylint's import visitor: Called automatically for every `ImportFrom` node.

        State and side effects:
            Delegates to `_check_test_import` which may access filesystem and emit messages.
            Reads `node.root().name` and `node.root().package` for relative import resolution.
            No other side effects.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=5
            #arch-eval:cohesion=5
            #arch-eval:separation=5
            #arch-eval:consumer_clarity=5
            #arch-eval:state_invariants=5
            #arch-eval:entity_fullness=2
            #arch-eval:locational_stability=5
        """
        current_module = node.root().name
        is_package = getattr(node.root(), "package", False)
        if node.level and node.level > 0:
            module_path = self._resolve_relative_module(
                current_module,
                node.level,
                node.modname,
                is_package=is_package,
            )
        else:
            module_path = node.modname or ""

        for alias in node.names:
            self._check_test_import(node, module_path, alias[0])
