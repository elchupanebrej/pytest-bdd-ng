"""

Contract tests for Phase 10 pattern unification enforcement.
"""

from __future__ import annotations

import ast
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
SRC_ROOT = REPO_ROOT / "src"


def test_no_dataclass_in_production_code() -> None:
    """
    Verify no stdlib @dataclass decorator usage — attrs must be used instead.

    Test target:
        Enforce framework invariants and stable API contracts.
    Test type:
        E2E/Acceptance test
    Test scenario:
        Given the relevant preconditions are met, when Enforce framework invariants and stable API contracts., then the
        expected outcome is produced.
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
    for py_file in sorted(SRC_ROOT.rglob("*.py")):
        if "pytest_bdd_testing" in py_file.parts:
            continue
        tree = ast.parse(py_file.read_text(encoding="utf-8"), filename=str(py_file))
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                for decorator in node.decorator_list:
                    # Check for bare @dataclass (from dataclasses import dataclass)
                    if isinstance(decorator, ast.Name) and decorator.id == "dataclass":
                        violations.append(
                            f"{py_file.relative_to(REPO_ROOT)}:{node.lineno} uses @dataclass decorator",
                        )
                    # Check for @dataclasses.dataclass
                    if (
                        isinstance(decorator, ast.Attribute)
                        and decorator.attr == "dataclass"
                        and isinstance(decorator.value, ast.Name)
                        and decorator.value.id == "dataclasses"
                    ):
                        violations.append(
                            f"{py_file.relative_to(REPO_ROOT)}:{node.lineno} uses @dataclasses.dataclass",
                        )

    assert violations == [], f"Found @dataclass usage: {violations}"


def test_empty_plugin_directories_removed() -> None:
    """
    Verify cucumber_formatter_support and scenario_runner dirs are removed.

    Test target:
        Enforce framework invariants and stable API contracts.
    Test type:
        E2E/Acceptance test
    Test scenario:
        Given the relevant preconditions are met, when Enforce framework invariants and stable API contracts., then the
        expected outcome is produced.
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
    removed_dirs = [
        SRC_ROOT / "pytest_bdd" / "plugin" / "cucumber_formatter_support",
        SRC_ROOT / "pytest_bdd" / "plugin" / "scenario_runner",
    ]
    for d in removed_dirs:
        assert not d.exists(), f"Directory should not exist: {d.relative_to(REPO_ROOT)}"
