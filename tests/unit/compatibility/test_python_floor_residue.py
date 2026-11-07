"""
Residue guard asserting no Python <3.11 version branching or retired backport imports
exist in src/pytest_cuke outside the documented keep-list.
"""

from __future__ import annotations

import ast
from pathlib import Path
from typing import NamedTuple

import pytest
from pytest import mark

pytestmark = mark.unit

# Deliberate keep-list: modules allowed to contain above-floor checks (e.g. 3.13),
# pytest-version logic, or product matrix compatibility data.
KEEP_LIST: frozenset[str] = frozenset(
    {
        "src/pytest_cuke/compatibility/pathlib.py",
        "src/pytest_cuke/compatibility/pytest.py",
        "src/pytest_cuke/compatibility/matrix.py",
        "src/pytest_cuke/compatibility/runtime_compat.py",
        "src/pytest_cuke/compatibility/environment_matrix.py",
        "src/pytest_cuke/compatibility/parser.py",
        "src/pytest_cuke/compatibility/struct_bdd.py",
        "src/pytest_cuke/compatibility/allure.py",
        "src/pytest_cuke/compatibility/path.py",
    }
)

DISALLOWED_MODULES: frozenset[str] = frozenset(
    {
        # Retired external backports:
        "tomli",
        "strenum",
        "importlib_resources",
        "importlib_metadata",
        "typing_extensions",
        # Deleted internal compatibility shims:
        "pytest_cuke.compatibility.tomllib",
        "pytest_cuke.compatibility.enum",
        "pytest_cuke.compatibility.importlib",
        "pytest_cuke.compatibility.sys",
        "pytest_cuke.compatibility.typing",
    }
)


class ResidueViolation(NamedTuple):
    file_path: str
    line: int
    rule: str
    message: str


def _extract_version_tuple(node: ast.AST) -> tuple[int, ...] | None:
    """Extract a literal integer tuple like (3, 11) or (3, 10)."""
    if isinstance(node, ast.Tuple):
        vals: list[int] = []
        for elt in node.elts:
            if isinstance(elt, ast.Constant) and isinstance(elt.value, int):
                vals.append(elt.value)
            else:
                return None
        return tuple(vals)
    return None


def _is_sys_version_info(node: ast.AST) -> bool:
    """Check if node refers to sys.version_info or version_info."""
    if isinstance(node, ast.Attribute):
        return isinstance(node.value, ast.Name) and node.value.id == "sys" and node.attr == "version_info"
    if isinstance(node, ast.Name) and node.id == "version_info":
        return True
    return bool(isinstance(node, ast.Subscript) and _is_sys_version_info(node.value))


def _is_sys_version_info_minor(node: ast.AST) -> bool:
    """Check if node refers to sys.version_info.minor."""
    return isinstance(node, ast.Attribute) and node.attr == "minor" and _is_sys_version_info(node.value)


class ResidueVisitor(ast.NodeVisitor):
    def __init__(self, file_path: str) -> None:
        self.file_path = file_path
        self.violations: list[ResidueViolation] = []

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            name = alias.name
            for disallowed in DISALLOWED_MODULES:
                if name == disallowed or name.startswith(disallowed + "."):
                    self.violations.append(
                        ResidueViolation(
                            file_path=self.file_path,
                            line=node.lineno,
                            rule="DISALLOWED_IMPORT",
                            message=f"Disallowed import: '{name}'",
                        )
                    )
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        module = node.module or ""
        for disallowed in DISALLOWED_MODULES:
            if module == disallowed or module.startswith(disallowed + "."):
                self.violations.append(
                    ResidueViolation(
                        file_path=self.file_path,
                        line=node.lineno,
                        rule="DISALLOWED_IMPORT",
                        message=f"Disallowed from-import from: '{module}'",
                    )
                )
        self.generic_visit(node)

    def visit_Compare(self, node: ast.Compare) -> None:
        # Check: sys.version_info <op> <comparator>
        if _is_sys_version_info(node.left):
            for op, comp in zip(node.ops, node.comparators, strict=False):
                version = _extract_version_tuple(comp)
                if version is not None and len(version) >= 2 and version[0] == 3:
                    minor = version[1]
                    if minor < 11:
                        self.violations.append(
                            ResidueViolation(
                                file_path=self.file_path,
                                line=node.lineno,
                                rule="PRE_311_VERSION_CHECK",
                                message=f"Python <3.11 version guard detected: comparison against {version}",
                            )
                        )
                    elif minor == 11 and isinstance(op, (ast.Lt, ast.GtE, ast.LtE, ast.Gt, ast.Eq, ast.NotEq)):
                        self.violations.append(
                            ResidueViolation(
                                file_path=self.file_path,
                                line=node.lineno,
                                rule="FLOOR_311_VERSION_CHECK",
                                message=f"Redundant 3.11 floor guard detected: comparison against {version}",
                            )
                        )

        # Check: <comparator> <op> sys.version_info
        for op, comp in zip(node.ops, node.comparators, strict=False):
            if _is_sys_version_info(comp):
                version = _extract_version_tuple(node.left)
                if version is not None and len(version) >= 2 and version[0] == 3:
                    minor = version[1]
                    if minor < 11:
                        self.violations.append(
                            ResidueViolation(
                                file_path=self.file_path,
                                line=node.lineno,
                                rule="PRE_311_VERSION_CHECK",
                                message=f"Python <3.11 version guard detected: comparison against {version}",
                            )
                        )
                    elif minor == 11 and isinstance(op, (ast.Lt, ast.GtE, ast.LtE, ast.Gt, ast.Eq, ast.NotEq)):
                        self.violations.append(
                            ResidueViolation(
                                file_path=self.file_path,
                                line=node.lineno,
                                rule="FLOOR_311_VERSION_CHECK",
                                message=f"Redundant 3.11 floor guard detected: comparison against {version}",
                            )
                        )

        # Check: sys.version_info.minor <op> int
        if _is_sys_version_info_minor(node.left):
            for op, comp in zip(node.ops, node.comparators, strict=False):
                if isinstance(comp, ast.Constant) and isinstance(comp.value, int):
                    if comp.value < 11:
                        self.violations.append(
                            ResidueViolation(
                                file_path=self.file_path,
                                line=node.lineno,
                                rule="PRE_311_VERSION_CHECK",
                                message=f"Python <3.11 version guard detected: minor < {comp.value}",
                            )
                        )
                    elif comp.value == 11 and isinstance(op, (ast.Lt, ast.GtE, ast.LtE, ast.Gt, ast.Eq, ast.NotEq)):
                        self.violations.append(
                            ResidueViolation(
                                file_path=self.file_path,
                                line=node.lineno,
                                rule="FLOOR_311_VERSION_CHECK",
                                message="Redundant 3.11 floor guard detected: minor comparison with 11",
                            )
                        )

        self.generic_visit(node)


def check_source_residue(source: str, file_path: str = "<string>") -> list[ResidueViolation]:
    """Parse source string and return all residue violations found."""
    tree = ast.parse(source, filename=file_path)
    visitor = ResidueVisitor(file_path=file_path)
    visitor.visit(tree)
    return visitor.violations


def test_no_python_below_311_residue_in_source() -> None:
    """Verify that no file in src/pytest_cuke (outside keep-list) contains <3.11 residue."""
    repo_root = Path(__file__).resolve().parents[3]
    src_dir = repo_root / "src" / "pytest_cuke"

    assert src_dir.is_dir(), f"Source directory not found: {src_dir}"

    all_violations: list[ResidueViolation] = []
    scanned_count = 0

    for py_file in sorted(src_dir.rglob("*.py")):
        rel_path = py_file.relative_to(repo_root).as_posix()
        if rel_path in KEEP_LIST:
            continue

        scanned_count += 1
        source_code = py_file.read_text(encoding="utf-8")
        violations = check_source_residue(source_code, file_path=rel_path)
        all_violations.extend(violations)

    assert scanned_count > 0, "No files were scanned"

    if all_violations:
        formatted = "\n".join(
            f"  {v.file_path}:{v.line} [{v.rule}] {v.message}"
            for v in all_violations
        )
        pytest.fail(
            f"Found {len(all_violations)} Python <3.11 residue violations:\n{formatted}"
        )


def test_keep_list_integrity() -> None:
    """Verify that every file declared in KEEP_LIST exists on disk."""
    repo_root = Path(__file__).resolve().parents[3]
    for rel_path in KEEP_LIST:
        target = repo_root / rel_path
        assert target.is_file(), f"Keep-list entry does not exist on disk: {rel_path}"


@pytest.mark.parametrize(
    ("snippet", "expected_rule"),
    [
        ("import tomli", "DISALLOWED_IMPORT"),
        ("import strenum", "DISALLOWED_IMPORT"),
        ("from importlib_resources import files", "DISALLOWED_IMPORT"),
        ("from importlib_metadata import version", "DISALLOWED_IMPORT"),
        ("from typing_extensions import Self", "DISALLOWED_IMPORT"),
        ("from pytest_cuke.compatibility.tomllib import tomllib", "DISALLOWED_IMPORT"),
        ("from pytest_cuke.compatibility.enum import StrEnum", "DISALLOWED_IMPORT"),
        ("from pytest_cuke.compatibility.sys import _getframe", "DISALLOWED_IMPORT"),
        ("from pytest_cuke.compatibility.typing import TypeAlias", "DISALLOWED_IMPORT"),
        ("import pytest_cuke.compatibility.importlib.resources", "DISALLOWED_IMPORT"),
        ("if sys.version_info < (3, 11): pass", "FLOOR_311_VERSION_CHECK"),
        ("if sys.version_info >= (3, 11): pass", "FLOOR_311_VERSION_CHECK"),
        ("if (3, 11) > sys.version_info: pass", "FLOOR_311_VERSION_CHECK"),
        ("if sys.version_info < (3, 10): pass", "PRE_311_VERSION_CHECK"),
        ("if sys.version_info < (3, 9): pass", "PRE_311_VERSION_CHECK"),
        ("if sys.version_info.minor < 11: pass", "FLOOR_311_VERSION_CHECK"),
        ("if sys.version_info.minor < 10: pass", "PRE_311_VERSION_CHECK"),
    ],
)
def test_residue_guard_detects_violations(snippet: str, expected_rule: str) -> None:
    """Verify that synthetic violations are caught by the residue checker."""
    violations = check_source_residue(snippet)
    assert len(violations) >= 1, f"Expected violation for: {snippet}"
    assert any(v.rule == expected_rule for v in violations)


@pytest.mark.parametrize(
    "snippet",
    [
        "import tomllib",
        "from enum import StrEnum",
        "from typing import Self, TypeAlias",
        "from importlib.resources import files, as_file",
        "from importlib.metadata import version",
        "if sys.version_info < (3, 13): pass",
        "if sys.version_info >= (3, 12): pass",
        "if sys.platform == 'win32': pass",
    ],
)
def test_residue_guard_allows_valid_code(snippet: str) -> None:
    """Verify that modern Python standard constructs and above-floor checks pass."""
    violations = check_source_residue(snippet)
    assert violations == [], f"Unexpected violations for valid snippet: {violations}"
