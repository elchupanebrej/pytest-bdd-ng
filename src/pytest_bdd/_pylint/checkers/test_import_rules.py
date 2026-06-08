"""
Responsibility:
    Responsibility: Responsibility: `pytest_bdd._pylint.checkers.test_import_rules` owns documented module behavior. It
    directly owns the observable contract, local decisions, and maintenance boundary for this module.

Reason for existence:
    This entity is the information expert for `pytest_bdd._pylint.checkers.test_import_rules` because it keeps the
    nearest code, data shape, call signature, and failure knowledge together.

Delegates:
    - get_test_paths: owns nested behavior below this boundary
    - get_test_package_prefixes: owns nested behavior below this boundary
    - resolve_import_to_path: owns nested behavior below this boundary
    - TestImportRulesChecker: owns nested behavior below this boundary

Cohesion:
    The implementation stays together because its imports, calls, state writes, and return contract describe one
    maintainable decision unit.

Separation:
    - module peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
      widening caller knowledge.

Main consumers:
    - None found by static import/name scan; verify dynamic use before refactor

State and side effects:
    mutates prefix, prefixes, p_path, p_parts, parts; depends on __future__.annotations, pathlib.Path, typing.cast,
    astroid.nodes, pylint.checkers.BaseChecker.

Invariants:
    - `pytest_bdd._pylint.checkers.test_import_rules` keeps its documented import path, ownership boundary, and
      observable behavior stable for callers.

Architecture score:
    #arch-eval:reason_for_existence=4
    #arch-eval:owned_responsibility=4
    #arch-eval:delegation_boundary=4
    #arch-eval:cohesion=3
    #arch-eval:separation=3
    #arch-eval:consumer_clarity=2
    #arch-eval:state_invariants=4
    #arch-eval:entity_fullness=4
    #arch-eval:locational_stability=2
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
    Read testpaths from pyproject.toml.

    Responsibility:
        Read testpaths from pyproject.toml. It directly owns the observable contract, local decisions, and maintenance
        boundary for this function. That boundary is intentionally stated in prose so maintainers can distinguish owned
        work from collaborators before editing.

    Reason for existence:
        This entity is the information expert for `pytest_bdd._pylint.checkers.test_import_rules.get_test_paths` because
        it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - Path.resolve: collaborator call used by this boundary
        - Path: collaborator call used by this boundary
        - pyproject_path.exists: collaborator call used by this boundary
        - tomllib.loads: collaborator call used by this boundary
        - pyproject_path.read_text: collaborator call used by this boundary
        - pyproject.get.get.get.get: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - None found by static import/name scan; verify dynamic use before refactor

    State and side effects:
        mutates pyproject_path, pyproject, paths; depends on tomllib, tomli.

    Invariants:
        - `pytest_bdd._pylint.checkers.test_import_rules.get_test_paths` keeps its documented import path, ownership
          boundary, and observable behavior stable for callers.

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
        pyproject_path = Path("pyproject.toml").resolve()
        if pyproject_path.exists():
            try:
                import tomllib
            except ImportError:
                import tomli as tomllib  # type: ignore[import-not-found, no-redef]  # fallback for python < 3.11
            pyproject = tomllib.loads(pyproject_path.read_text(encoding="utf-8"))
            paths = (
                pyproject.get("tool", {})
                .get("pytest", {})
                .get("ini_options", {})
                .get("testpaths", ["src/pytest_bdd_testing/cases"])
            )
            return cast("list[str]", paths)
    except Exception:  # noqa: BLE001
        pass
    return ["src/pytest_bdd_testing/cases"]


def get_test_package_prefixes() -> list[str]:
    """
    Get the dotted module prefixes for allowed test imports.

    Responsibility:
        Get the dotted module prefixes for allowed test imports. It directly owns the observable contract, local
        decisions, and maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd._pylint.checkers.test_import_rules.get_test_package_prefixes` because it keeps the nearest code,
        data shape, call signature, and failure knowledge together.

    Delegates:
        - join: collaborator call used by this boundary
        - prefixes.append: collaborator call used by this boundary
        - get_test_paths: collaborator call used by this boundary
        - Path: collaborator call used by this boundary
        - p_path.is_dir: collaborator call used by this boundary
        - p_path.iterdir: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - None found by static import/name scan; verify dynamic use before refactor

    State and side effects:
        mutates prefix, prefixes, p_path, p_parts.

    Invariants:
        - `pytest_bdd._pylint.checkers.test_import_rules.get_test_package_prefixes` keeps its documented import path,
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
    Resolve a dotted import path to a physical file path on disk.

    Responsibility:
        Resolve a dotted import path to a physical file path on disk. It directly owns the observable contract, local
        decisions, and maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd._pylint.checkers.test_import_rules.resolve_import_to_path`
        because it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - Path: collaborator call used by this boundary
        - Path.resolve: collaborator call used by this boundary
        - search_roots.append: collaborator call used by this boundary
        - root.joinpath: collaborator call used by this boundary
        - module_path.split: collaborator call used by this boundary
        - get_test_paths: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - None found by static import/name scan; verify dynamic use before refactor

    State and side effects:
        mutates parts, search_roots, p_path, seen, unique_roots.

    Invariants:
        - `pytest_bdd._pylint.checkers.test_import_rules.resolve_import_to_path` keeps its documented import path,
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
    Checker for test import rules: BLQ1601.

    Responsibility:
        Checker for test import rules: BLQ1601. It directly owns the observable contract, local decisions, and
        maintenance boundary for this class. That boundary is intentionally stated in prose so maintainers can
        distinguish owned work from collaborators before editing.

    Reason for existence:
        This entity is the information expert for `pytest_bdd._pylint.checkers.test_import_rules.TestImportRulesChecker`
        because it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - _resolve_relative_module: owns nested behavior below this boundary
        - _check_test_import: owns nested behavior below this boundary
        - visit_import: owns nested behavior below this boundary
        - visit_importfrom: owns nested behavior below this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/_pylint/__init__.py: imports or references `TestImportRulesChecker`

    State and side effects:
        mutates resolved_file, is_under_test_paths, prefix, module_path, name.

    Invariants:
        - `pytest_bdd._pylint.checkers.test_import_rules.TestImportRulesChecker` keeps its documented import path,
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
        Responsibility:
            Responsibility: Responsibility:
            `pytest_bdd._pylint.checkers.test_import_rules.TestImportRulesChecker._resolve_relative_module` owns
            documented method behavior. It directly owns the observable contract, local decisions, and maintenance
            boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd._pylint.checkers.test_import_rules.TestImportRulesChecker._resolve_relative_module` because it
            keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - current_module.split: collaborator call used by this boundary
            - range: collaborator call used by this boundary
            - parts.pop: collaborator call used by this boundary
            - parts.append: collaborator call used by this boundary
            - join: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - None found by static import/name scan; verify dynamic use before refactor

        State and side effects:
            mutates parts, adjust.

        Invariants:
            - `pytest_bdd._pylint.checkers.test_import_rules.TestImportRulesChecker._resolve_relative_module` keeps its
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
        Responsibility:
            Responsibility: Responsibility:
            `pytest_bdd._pylint.checkers.test_import_rules.TestImportRulesChecker._check_test_import` owns documented
            method behavior. It directly owns the observable contract, local decisions, and maintenance boundary for
            this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd._pylint.checkers.test_import_rules.TestImportRulesChecker._check_test_import` because it keeps
            the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - join: collaborator call used by this boundary
            - full_path.startswith: collaborator call used by this boundary
            - Path: collaborator call used by this boundary
            - get_test_paths: collaborator call used by this boundary
            - any: collaborator call used by this boundary
            - resolve_import_to_path: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - None found by static import/name scan; verify dynamic use before refactor

        State and side effects:
            mutates resolved_file, is_under_test_paths, prefix, full_path, prefixes.

        Invariants:
            - `pytest_bdd._pylint.checkers.test_import_rules.TestImportRulesChecker._check_test_import` keeps its
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
        Check direct import statements.

        Responsibility:
            Check direct import statements. It directly owns the observable contract, local decisions, and maintenance
            boundary for this method. That boundary is intentionally stated in prose so maintainers can distinguish
            owned work from collaborators before editing.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd._pylint.checkers.test_import_rules.TestImportRulesChecker.visit_import` because it keeps the
            nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - self._check_test_import: collaborator call used by this boundary

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
        for alias in node.names:
            self._check_test_import(node, "", alias[0])

    def visit_importfrom(self, node: nodes.ImportFrom) -> None:
        """
        Check import-from statements.

        Responsibility:
            Check import-from statements. It directly owns the observable contract, local decisions, and maintenance
            boundary for this method. That boundary is intentionally stated in prose so maintainers can distinguish
            owned work from collaborators before editing.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd._pylint.checkers.test_import_rules.TestImportRulesChecker.visit_importfrom` because it keeps the
            nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - node.root: collaborator call used by this boundary
            - getattr: collaborator call used by this boundary
            - self._resolve_relative_module: collaborator call used by this boundary
            - self._check_test_import: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - None found by static import/name scan; verify dynamic use before refactor

        State and side effects:
            mutates module_path, current_module, is_package.

        Invariants:
            - `pytest_bdd._pylint.checkers.test_import_rules.TestImportRulesChecker.visit_importfrom` keeps its
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
