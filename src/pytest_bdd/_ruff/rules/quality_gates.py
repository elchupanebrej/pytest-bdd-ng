"""
Enforce pytest-bdd quality gates.

CI and pre-commit command:
``uv run python -m pytest_bdd._ruff.rules.quality_gates src/pytest_bdd/``

Exit code 1 means at least one hard-blocking quality gate violation was found.
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path
from typing import TYPE_CHECKING, NamedTuple

if TYPE_CHECKING:
    from collections.abc import Iterable

from .plugin_patterns import check_plugin_patterns as _check_plugin_patterns

DEFAULT_PATH = Path("src/pytest_bdd")
RETURN_NONE_MESSAGE = (
    "BLQ901: `return None` in non-hook function - use `Nothing` (Maybe) or `Failure(reason)` (Result) instead"
)
EXCEPT_EXCEPTION_MESSAGE = (
    "BLQ902: bare `except Exception:` without logging - add `logger.warning(exc_info=True)` or `# noqa: BLE001`"
)


class Violation(NamedTuple):
    """Quality gate violation."""

    path: Path
    line: int
    message: str


class QualityGateVisitor(ast.NodeVisitor):
    """Find quality gate violations in a Python syntax tree."""

    def __init__(self, path: Path, lines: list[str]) -> None:
        """Initialize visitor with source location metadata."""
        self.path = path
        self.lines = lines
        self.violations: list[Violation] = []
        self._function_stack: list[str] = []

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Visit function body with hook exemption context."""
        self._function_stack.append(node.name)
        self.generic_visit(node)
        self._function_stack.pop()

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        """Visit async function body with hook exemption context."""
        self._function_stack.append(node.name)
        self.generic_visit(node)
        self._function_stack.pop()

    def visit_Return(self, node: ast.Return) -> None:
        """Detect explicit return None outside pytest hooks."""
        if self._is_none_return(node) and not self._current_function_is_hook():
            self.violations.append(Violation(self.path, node.lineno, RETURN_NONE_MESSAGE))
        self.generic_visit(node)

    def visit_ExceptHandler(self, node: ast.ExceptHandler) -> None:
        """Detect unlogged except Exception handlers."""
        if self._is_exception_handler(node) and not self._has_noqa(node) and not self._has_exception_logging(node):
            self.violations.append(Violation(self.path, node.lineno, EXCEPT_EXCEPTION_MESSAGE))
        self.generic_visit(node)

    def _current_function_is_hook(self) -> bool:
        function_name = self._function_stack[-1] if self._function_stack else ""
        return function_name.startswith(("pytest_", "_pytest_"))

    @staticmethod
    def _is_none_return(node: ast.Return) -> bool:
        return isinstance(node.value, ast.Constant) and node.value.value is None

    @staticmethod
    def _is_exception_handler(node: ast.ExceptHandler) -> bool:
        return isinstance(node.type, ast.Name) and node.type.id == "Exception"

    def _has_noqa(self, node: ast.ExceptHandler) -> bool:
        current_line = self._line_at(node.lineno)
        previous_line = self._line_at(node.lineno - 1)
        return self._line_has_noqa(current_line) or self._line_has_noqa(previous_line)

    @staticmethod
    def _line_has_noqa(line: str) -> bool:
        if "noqa" not in line:
            return False
        if "noqa:" not in line:
            return True
        return any(rule in line for rule in ("BLE001", "BLQ902"))

    def _line_at(self, line_number: int) -> str:
        if line_number < 1 or line_number > len(self.lines):
            return ""
        return self.lines[line_number - 1]

    def _has_exception_logging(self, node: ast.ExceptHandler) -> bool:
        return any(
            isinstance(child, ast.Call) and self._is_supported_logging_call(child)
            for statement in node.body
            for child in ast.walk(statement)
        )

    def _is_supported_logging_call(self, node: ast.Call) -> bool:
        if not isinstance(node.func, ast.Attribute):
            return False
        if not self._is_logger_object(node.func.value):
            return False
        if node.func.attr == "exception":
            return True
        if node.func.attr != "warning":
            return False
        return any(keyword.arg == "exc_info" and self._keyword_is_true(keyword.value) for keyword in node.keywords)

    @staticmethod
    def _is_logger_object(node: ast.AST) -> bool:
        return isinstance(node, ast.Name) and node.id in {"logger", "logging"}

    @staticmethod
    def _keyword_is_true(node: ast.AST) -> bool:
        return isinstance(node, ast.Constant) and node.value is True


def iter_python_files(paths: Iterable[Path]) -> Iterable[Path]:
    """
    Yield Python files from file or directory arguments.

    Yields:
        Python source files under each requested path.

    """
    for path in paths:
        if path.is_file() and path.suffix == ".py":
            yield path
        if path.is_dir():
            yield from sorted(child for child in path.rglob("*.py") if child.is_file())


def check_file(path: Path) -> list[Violation]:
    """
    Return quality gate violations for one Python file.

    Returns:
        Violations found in the file.

    """
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(path))
    visitor = QualityGateVisitor(path, source.splitlines())
    visitor.visit(tree)
    return visitor.violations


def check_paths(paths: Iterable[Path]) -> list[Violation]:
    """
    Return quality gate violations for all Python files under paths.

    Returns:
        Violations found under all paths.

    """
    violations: list[Violation] = []
    for path in iter_python_files(paths):
        violations.extend(check_file(path))
    return violations


def main(argv: list[str] | None = None) -> int:
    """
    Run quality gate checks and return process exit code.

    Returns:
        Process exit code. Non-zero means violations were found.

    """
    args = sys.argv[1:] if argv is None else argv
    paths = [Path(arg) for arg in args] if args else [DEFAULT_PATH]
    violations = check_paths(paths)

    plugin_root = Path("src/pytest_bdd/plugin")
    if plugin_root.is_dir():
        violations.extend(_check_plugin_patterns(plugin_root))

    for violation in violations:
        sys.stdout.write(f"{violation.path}:{violation.line}: {violation.message}\n")
    return 1 if violations else 0


if __name__ == "__main__":
    raise SystemExit(main())
