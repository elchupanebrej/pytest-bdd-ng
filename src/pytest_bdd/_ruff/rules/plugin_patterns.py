"""
Plugin pattern validation for pytest-bdd-ng.

Validates that all plugins follow prescribed internal architecture:
1. Required files: entrypoint.py, hook.py, plugin.py
2. No cross-plugin imports between different plugin packages
3. pytest.config.stash access only via StashBound subclasses or allowed exceptions

CI and pre-commit command:
``uv run python -m pytest_bdd._ruff.rules.plugin_patterns src/pytest_bdd/plugin/``

Exit code 1 means at least one pattern violation was found.
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path
from typing import NamedTuple

REQUIRED_FILES = {"entrypoint.py", "hook.py", "plugin.py"}
STASH_ACCESS_ALLOWED = {"stash_access.py", "exception.py"}
_MIN_MODULE_PARTS = 3


class Violation(NamedTuple):
    """Plugin pattern violation."""

    path: Path
    line: int | None
    message: str


def _get_plugin_directories(plugin_root: Path) -> list[Path]:
    """
    Return all plugin subdirectories, excluding __pycache__ and non-directories.

    Returns:
        Sorted list of plugin directory paths.

    """
    return sorted(
        d for d in plugin_root.iterdir() if d.is_dir() and d.name != "__pycache__" and not d.name.startswith(".")
    )


def check_required_files(plugin_root: Path) -> list[Violation]:
    """
    Check that each plugin directory has entrypoint.py, hook.py, and plugin.py.

    Returns:
        List of violations for missing required files.

    """
    violations: list[Violation] = []
    for plugin_dir in _get_plugin_directories(plugin_root):
        for required in REQUIRED_FILES:
            required_path = plugin_dir / required
            if not required_path.exists():
                violations.append(
                    Violation(
                        plugin_dir,
                        None,
                        f"BLQ1001: missing required file '{required}' in plugin '{plugin_dir.name}'",
                    ),
                )
    return violations


def _is_cross_plugin_import(
    node: ast.ImportFrom | ast.Import,
    current_plugin_name: str,
) -> tuple[bool, str | None, int]:
    """
    Check if an import statement crosses plugin boundaries.

    Returns:
        (is_cross, imported_plugin_name, line_number)

    """
    if isinstance(node, ast.ImportFrom):
        if node.module is None:
            return False, None, node.lineno
        parts = node.module.split(".")
        if len(parts) >= _MIN_MODULE_PARTS and parts[0] == "pytest_bdd" and parts[1] == "plugin":
            imported_plugin = parts[2]
            if imported_plugin != current_plugin_name:
                return True, imported_plugin, node.lineno
    elif isinstance(node, ast.Import):
        for alias in node.names:
            parts = alias.name.split(".")
            if len(parts) >= _MIN_MODULE_PARTS and parts[0] == "pytest_bdd" and parts[1] == "plugin":
                imported_plugin = parts[2]
                if imported_plugin != current_plugin_name:
                    return True, imported_plugin, node.lineno
    return False, None, node.lineno


def check_cross_plugin_imports(plugin_root: Path) -> list[Violation]:
    """
    Check that no plugin imports from another plugin package.

    Intra-plugin imports (within the same plugin package) are permitted.

    Returns:
        List of violations for cross-plugin imports.

    """
    violations: list[Violation] = []
    for plugin_dir in _get_plugin_directories(plugin_root):
        plugin_name = plugin_dir.name
        for py_file in plugin_dir.rglob("*.py"):
            if py_file.name.startswith("."):
                continue
            try:
                source = py_file.read_text(encoding="utf-8")
                tree = ast.parse(source, filename=str(py_file))
            except SyntaxError:
                continue

            for node in ast.walk(tree):
                if isinstance(node, (ast.ImportFrom, ast.Import)):
                    is_cross, imported_plugin, line = _is_cross_plugin_import(
                        node,
                        plugin_name,
                    )
                    if is_cross:
                        violations.append(
                            Violation(
                                py_file,
                                line,
                                f"BLQ1002: cross-plugin import from '{imported_plugin}' "
                                f"in plugin '{plugin_name}' (use hooks for inter-plugin communication)",
                            ),
                        )
    return violations


def _file_has_stash_access(source: str, tree: ast.Module) -> bool:
    """
    Check if the source file contains stash access patterns.

    Returns:
        True if stash access patterns are detected, False otherwise.

    """
    if ".stash[" in source or ".stash.get(" in source:
        return True
    for node in ast.walk(tree):
        if isinstance(node, ast.Subscript) and isinstance(node.value, ast.Attribute) and node.value.attr == "stash":
            return True
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "get"
            and isinstance(node.func.value, ast.Attribute)
            and node.func.value.attr == "stash"
        ):
            return True
    return False


def check_stashbound_coverage(plugin_root: Path) -> list[Violation]:
    """
    Check that pytest.config.stash is only accessed via StashBound or allowed exceptions.

    Returns:
        List of violations for unauthorized stash access.

    """
    violations: list[Violation] = []
    for plugin_dir in _get_plugin_directories(plugin_root):
        for py_file in plugin_dir.rglob("*.py"):
            if py_file.name.startswith("."):
                continue
            if py_file.name in STASH_ACCESS_ALLOWED:
                continue

            try:
                source = py_file.read_text(encoding="utf-8")
                tree = ast.parse(source, filename=str(py_file))
            except SyntaxError:
                continue

            if not _file_has_stash_access(source, tree):
                continue

            violations.append(
                Violation(
                    py_file,
                    None,
                    f"BLQ1003: direct stash access in '{py_file.relative_to(plugin_root.parent)}' "
                    f"— use StashBound subclass for config.stash access",
                ),
            )
    return violations


def check_plugin_patterns(plugin_root: Path) -> list[Violation]:
    """
    Run all plugin pattern checks.

    Returns:
        Combined list of all violations found.

    """
    violations: list[Violation] = []
    violations.extend(check_required_files(plugin_root))
    violations.extend(check_cross_plugin_imports(plugin_root))
    violations.extend(check_stashbound_coverage(plugin_root))
    return violations


def main(argv: list[str] | None = None) -> int:
    """
    Run plugin pattern checks and return process exit code.

    Returns:
        Process exit code. Non-zero means violations were found.

    """
    args = sys.argv[1:] if argv is None else argv
    plugin_root = Path("src/pytest_bdd/plugin") if not args else Path(args[0])

    if not plugin_root.is_dir():
        sys.stdout.write(f"Error: plugin directory '{plugin_root}' does not exist or is not a directory\n")
        return 1

    violations = check_plugin_patterns(plugin_root)
    for violation in violations:
        location = f"{violation.path}"
        if violation.line is not None:
            location += f":{violation.line}"
        sys.stdout.write(f"{location}: {violation.message}\n")

    if violations:
        sys.stdout.write(f"\nFound {len(violations)} plugin pattern violation(s)\n")
        return 1

    sys.stdout.write("All plugin patterns validated successfully\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
