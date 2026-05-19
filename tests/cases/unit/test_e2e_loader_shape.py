"""Guard E2E scenario loader shape contracts."""

from __future__ import annotations

import ast
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
E2E_ROOTS = (REPO_ROOT / "tests" / "cases" / "e2e",)


def _iter_e2e_test_modules() -> list[Path]:
    modules: list[Path] = []
    for root in E2E_ROOTS:
        if root.exists():
            modules.extend(
                sorted(path for path in root.rglob("test_*.py") if "fixtures" not in path.relative_to(root).parts),
            )
    return modules


def _literal_path_value(node: ast.AST) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.Call) and _call_name(node.func) == "Path" and node.args:
        return _literal_path_value(node.args[0])
    return None


def _call_name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    return ""


def _scenarios_loader_offenses(module: Path) -> list[str]:
    tree = ast.parse(module.read_text(encoding="utf-8"), filename=str(module))
    offenses = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or _call_name(node.func) != "scenarios":
            continue
        if not node.args:
            offenses.append(f"{module.relative_to(REPO_ROOT)}:{node.lineno}: scenarios() has no owned feature file")
            continue
        path_value = _literal_path_value(node.args[0])
        if path_value is None:
            offenses.append(
                f"{module.relative_to(REPO_ROOT)}:{node.lineno}: scenarios() path is not a literal owned feature file",
            )
            continue
        normalized = path_value.replace("\\", "/")
        if normalized in {".", "./", ""}:
            offenses.append(
                f'{module.relative_to(REPO_ROOT)}:{node.lineno}: scenarios("{path_value}") loads a directory',
            )
        elif not normalized.endswith((".feature", ".feature.md")):
            offenses.append(
                f"{module.relative_to(REPO_ROOT)}:{node.lineno}: "
                f"scenarios({path_value!r}) must target .feature or .feature.md",
            )
    return offenses


def test_e2e_modules_bind_owned_feature_files() -> None:
    """Verify E2E scenarios calls bind explicit feature files, not directories."""
    offenses = [offense for module in _iter_e2e_test_modules() for offense in _scenarios_loader_offenses(module)]

    assert offenses == []
