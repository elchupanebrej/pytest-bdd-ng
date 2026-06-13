"""

Source-level contract tests for scenario run Maybe/Result migration.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

pytestmark = [pytest.mark.unit]

RUN_PATH = Path("src/pytest_bdd/model/run/lifecycle/_run.py")
SCENARIO_RUN_PATH = Path("src/pytest_bdd/model/scenario_run.py")
MOVED_SCENARIO_RUN_SYMBOLS = {
    "ActiveObjectSet",
    "ContextErrorState",
    "ExternalApiCompatibilityRecord",
    "FeatureRuntimeBinding",
    "HookPhase",
    "LifecycleObjectRef",
    "ReferenceResolverState",
    "ReportingContextSnapshot",
    "ReportingLifecycleState",
    "Run",
    "RunStage",
    "RunStatus",
}
ALLOWED_SCENARIO_RUN_SYMBOLS = {"ScenarioRun", "RunNode", "StepRun"}


def _module(path: Path = SCENARIO_RUN_PATH) -> ast.Module:
    return ast.parse(path.read_text(encoding="utf-8"))


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


def test_run_uses_direct_returns_imports() -> None:
    """
    Test target:
    Verify internal unit invariants and correct behavior of individual code components.
    Test type:
    Unit test
    Test scenario:
    Given the relevant preconditions are met, when Verify internal unit invariants and correct behavior of
        individual code components., then the expected outcome is produced.
    BDD reference:
    None
    Fixtures:
    - None
    Mocks:
    - None
    Side effects:
    None
    Reduction:
    Requires real component interaction that cannot be reproduced by mocking alone.
    Escalation:
    Testing at a higher level would not add coverage and would slow down the suite.
    Atomicity:
    All assertions share the same setup and verify a single coherent behavior.
    Autonomy:
    Covers a distinct code path not exercised by any sibling test.
    Test quality score:
    #test-eval:isolation=5
    #test-eval:determinism=5
    #test-eval:setup_complexity=1
    #test-eval:assertions_clarity=5
    """
    module = _module(RUN_PATH)

    assert "returns.maybe.Nothing" in _imports(module)
    assert "returns.result.Result" in _imports(module)
    assert "pytest_bdd.types.failure_reasons.ScenarioRunFailure" in _imports(module)


def test_run_declares_result_contract_type() -> None:
    """
    Test target:
    Verify internal unit invariants and correct behavior of individual code components.
    Test type:
    Unit test
    Test scenario:
    Given the relevant preconditions are met, when Verify internal unit invariants and correct behavior of
        individual code components., then the expected outcome is produced.
    BDD reference:
    None
    Fixtures:
    - None
    Mocks:
    - None
    Side effects:
    None
    Reduction:
    Requires real component interaction that cannot be reproduced by mocking alone.
    Escalation:
    Testing at a higher level would not add coverage and would slow down the suite.
    Atomicity:
    All assertions share the same setup and verify a single coherent behavior.
    Autonomy:
    Covers a distinct code path not exercised by any sibling test.
    Test quality score:
    #test-eval:isolation=5
    #test-eval:determinism=5
    #test-eval:setup_complexity=1
    #test-eval:assertions_clarity=5
    """
    module = _module(RUN_PATH)

    assignments = {
        node.targets[0].id: ast.unparse(node.value)
        for node in module.body
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name)
    }
    assert assignments["ScenarioRunResult"].startswith("Result[")


def test_scenario_run_has_no_bare_return_none() -> None:
    """
    Test target:
    Verify internal unit invariants and correct behavior of individual code components.
    Test type:
    Unit test
    Test scenario:
    Given the relevant preconditions are met, when Verify internal unit invariants and correct behavior of
        individual code components., then the expected outcome is produced.
    BDD reference:
    None
    Fixtures:
    - None
    Mocks:
    - None
    Side effects:
    None
    Reduction:
    Requires real component interaction that cannot be reproduced by mocking alone.
    Escalation:
    Testing at a higher level would not add coverage and would slow down the suite.
    Atomicity:
    All assertions share the same setup and verify a single coherent behavior.
    Autonomy:
    Covers a distinct code path not exercised by any sibling test.
    Test quality score:
    #test-eval:isolation=5
    #test-eval:determinism=5
    #test-eval:setup_complexity=1
    #test-eval:assertions_clarity=5
    """
    for node in ast.walk(_module()):
        if isinstance(node, ast.Return) and isinstance(node.value, ast.Constant) and node.value.value is None:
            message = f"bare return None at line {node.lineno}"
            raise AssertionError(message)


def test_moved_symbols_are_not_imported_from_scenario_run_module() -> None:
    """
    Verify moved runtime symbols use their direct owning modules.

    Test target:
        Verify internal unit invariants and correct behavior of individual code components.
    Test type:
        Unit test
    Test scenario:
        Given the relevant preconditions are met, when Verify internal unit invariants and correct behavior of
        individual code components., then the expected outcome is produced.
    BDD reference:
        None
    Fixtures:
        - None
    Mocks:
        - None
    Side effects:
        None
    Reduction:
        Requires real component interaction that cannot be reproduced by mocking alone.
    Escalation:
        Testing at a higher level would not add coverage and would slow down the suite.
    Atomicity:
        All assertions share the same setup and verify a single coherent behavior.
    Autonomy:
        Covers a distinct code path not exercised by any sibling test.
    Test quality score:
        #test-eval:isolation=5
        #test-eval:determinism=5
        #test-eval:setup_complexity=1
        #test-eval:assertions_clarity=5
    """
    violations: list[str] = []
    for path in [*Path("src").rglob("*.py"), *Path("tests").rglob("*.py")]:
        if path == Path(__file__):
            continue
        module = ast.parse(path.read_text(encoding="utf-8-sig"))
        for node in ast.walk(module):
            if not isinstance(node, ast.ImportFrom) or node.module != "pytest_bdd.model.scenario_run":
                continue
            moved = {alias.name for alias in node.names} & MOVED_SCENARIO_RUN_SYMBOLS
            allowed = {alias.name for alias in node.names} & ALLOWED_SCENARIO_RUN_SYMBOLS
            if moved:
                violations.append(f"{path}:{node.lineno}: moved imports {sorted(moved)}")
            if not moved and not allowed:
                violations.append(f"{path}:{node.lineno}: unexpected scenario_run import")

    assert violations == []
