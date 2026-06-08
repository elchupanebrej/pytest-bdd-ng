"""Contract tests for plugin-to-plugin import boundaries."""

from __future__ import annotations

import ast
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[5]
PLUGIN_ROOT = REPO_ROOT / "src" / "pytest_bdd" / "plugin"
ALLOWED_PLUGIN_OWNERS = {"compatibility", "model", "util"}


def _owner_for_source(source_path: Path) -> str:
    relative = source_path.relative_to(PLUGIN_ROOT)
    if len(relative.parts) == 1:
        return relative.stem
    return relative.parts[0]


def _plugin_import_owner(module_name: str) -> str | None:
    prefix = "pytest_bdd.plugin."
    if not module_name.startswith(prefix):
        return None
    remainder = module_name[len(prefix) :]
    if not remainder:
        return None
    return remainder.split(".", maxsplit=1)[0]


def _imported_modules(tree: ast.AST) -> list[str]:
    modules: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.module == "pytest_bdd.plugin":
                modules.extend(f"{node.module}.{alias.name}" for alias in node.names)
            elif node.module is not None:
                modules.append(node.module)
    return modules


def test_plugin_code_does_not_import_other_plugin_packages() -> None:
    """Verify plugin code communicates through model/util/contracts, not peer plugin internals."""
    violations: list[str] = []
    for source_path in sorted(PLUGIN_ROOT.rglob("*.py")):
        owner = _owner_for_source(source_path)
        tree = ast.parse(source_path.read_text(encoding="utf-8"), filename=str(source_path))
        for module_name in _imported_modules(tree):
            imported_owner = _plugin_import_owner(module_name)
            if imported_owner is None:
                continue
            if imported_owner in {owner, *ALLOWED_PLUGIN_OWNERS}:
                continue
            violations.append(
                f"{source_path.relative_to(REPO_ROOT)} imports {module_name} "
                f"(owner={owner}, imported_owner={imported_owner})",
            )

    assert violations == []
