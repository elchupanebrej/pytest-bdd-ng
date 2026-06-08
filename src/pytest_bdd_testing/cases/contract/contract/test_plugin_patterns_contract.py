"""Contract tests for Phase 10 pattern unification enforcement."""

from __future__ import annotations

import ast
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[5]
SRC_ROOT = REPO_ROOT / "src"


def test_no_dataclass_in_production_code() -> None:
    """Verify no stdlib @dataclass decorator usage — attrs must be used instead."""
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
    """Verify cucumber_formatter_support and scenario_runner dirs are removed."""
    removed_dirs = [
        SRC_ROOT / "pytest_bdd" / "plugin" / "cucumber_formatter_support",
        SRC_ROOT / "pytest_bdd" / "plugin" / "scenario_runner",
    ]
    for d in removed_dirs:
        assert not d.exists(), f"Directory should not exist: {d.relative_to(REPO_ROOT)}"
