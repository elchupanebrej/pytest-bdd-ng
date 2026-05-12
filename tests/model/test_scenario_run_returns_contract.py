"""Source-level contract tests for scenario run Maybe/Result migration."""

from __future__ import annotations

import ast
from pathlib import Path

SCENARIO_RUN_PATH = Path("src/pytest_bdd/model/scenario_run.py")


def _module() -> ast.Module:
    return ast.parse(SCENARIO_RUN_PATH.read_text(encoding="utf-8"))


def _imports(module: ast.Module) -> set[str]:
    imported: set[str] = set()
    for node in ast.walk(module):
        if isinstance(node, ast.ImportFrom):
            module_name = node.module or ""
            imported.update(f"{module_name}.{alias.name}" for alias in node.names)
    return imported


def _return_annotation(module: ast.Module, function_name: str) -> str:
    for node in ast.walk(module):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == function_name:
            assert node.returns is not None, f"{function_name} must have return annotation"
            return ast.unparse(node.returns)
    message = f"{function_name} not found"
    raise AssertionError(message)


def test_scenario_run_uses_direct_returns_imports() -> None:
    module = _module()

    assert "returns.maybe.Nothing" in _imports(module)
    assert "returns.result.Result" in _imports(module)
    assert "pytest_bdd.types.failure_reasons.ScenarioRunFailure" in _imports(module)


def test_scenario_run_declares_result_contract_type() -> None:
    module = _module()

    assignments = {
        node.targets[0].id: ast.unparse(node.value)
        for node in module.body
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name)
    }
    assert assignments["ScenarioRunResult"].startswith("Result[")


def test_scenario_run_has_no_bare_return_none() -> None:
    for node in ast.walk(_module()):
        if isinstance(node, ast.Return) and isinstance(node.value, ast.Constant) and node.value.value is None:
            message = f"bare return None at line {node.lineno}"
            raise AssertionError(message)
