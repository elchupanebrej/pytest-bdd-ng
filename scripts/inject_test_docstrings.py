"""
pytest-synchronized test docstring injection script.

Responsibility:
    Collects all test files via pytest's native collection and injects the Test Responsibility Template
    into test functions only. Module-level docstrings are left untouched (any legacy module-level
    templates are cleaned up).

Reason for existence:
    Automates docstring bootstrapping while remaining aligned with pytest's collection configuration.

Delegates:
    - pytest.main: Native pytest test collection.
"""

from __future__ import annotations

import argparse
import ast
import re
import sys
from pathlib import Path

import pytest

TEMPLATE_STR = """Test target:
    <behavior/invariant/contract this test protects — Why the test exists, not How it is implemented, do not repeat test name>
Test type:
    <Unit | Integration | E2E | Contract | Compat>
Test scenario:
    <Given [preconditions], when [action], then [expected outcome]>
BDD reference:
    <path/to/file.feature.md :: Scenario title | None>
Fixtures:
    - None
Mocks:
    - None
Side effects:
    None
Reduction:
    <why this test cannot be moved to a lower level>
Escalation:
    <why this test cannot be moved to a higher level>
Atomicity:
    <why this test cannot be split into smaller tests>
Autonomy:
    <why this test cannot be merged with another test>
Test quality score:
    #test-eval:isolation=5
    #test-eval:determinism=5
    #test-eval:setup_complexity=1
    #test-eval:assertions_clarity=5"""


class TestCollectorPlugin:
    """pytest plugin to collect test file paths during pytest collection modify items."""

    def __init__(self) -> None:
        self.test_files: set[Path] = set()

    def pytest_collection_modifyitems(self, items: list[pytest.Item]) -> None:
        """Collect the absolute paths of all test files containing test items."""
        for item in items:
            if hasattr(item, "fspath") and item.fspath:
                self.test_files.add(Path(item.fspath).resolve())


def quote_docstring(content: str, indent: str) -> list[str]:
    """Format and quote the docstring content with unified PEP-257 quotes and indentation."""
    body = content.splitlines()
    has_backslash = "\\" in content
    if has_backslash:
        escaped_body = [line.replace('"""', '\\"\\"\\"') for line in body]
        return [
            f'{indent}r"""',
            *(f"{indent}{line.rstrip()}" if line.rstrip() else "" for line in escaped_body),
            f'{indent}"""',
        ]
    escaped_body = [line.replace("\\", "\\\\").replace('"""', '\\"\\"\\"') for line in body]
    return [
        f'{indent}"""',
        *(f"{indent}{line.rstrip()}" if line.rstrip() else "" for line in escaped_body),
        f'{indent}"""',
    ]


def header_insertion(node: ast.AST, lines: list[str], doc_lines: list[str]) -> tuple[int, int, list[str]]:
    """Determine where to insert the docstring in the node body lines."""
    start = getattr(node, "lineno", 1) - 1
    end = min(getattr(node, "end_lineno", start + 1), len(lines))
    depth = 0
    for index in range(start, end):
        line = lines[index]
        code = line.split("#", 1)[0]
        depth += code.count("(") + code.count("[") + code.count("{")
        depth -= code.count(")") + code.count("]") + code.count("}")
        colon = code.rfind(":")
        if colon == -1 or depth > 0:
            continue
        head = line[: colon + 1].rstrip()
        tail = line[colon + 1 :].strip()
        indent = re.match(r"\s*", line).group(0) + "    "
        body_doc = [(indent + item.lstrip()).rstrip() for item in doc_lines]
        if tail:
            return index, index + 1, [head, *body_doc, indent + tail]
        return index + 1, index + 1, body_doc
    indent = re.match(r"\s*", lines[start]).group(0) + "    "
    return start + 1, start + 1, [(indent + item.lstrip()).rstrip() for item in doc_lines]


def cleanup_module_docstring(path: Path) -> bool:
    """
    Remove the Test Responsibility Template from a test file's module docstring.
    """
    content = path.read_text(encoding="utf-8")
    try:
        tree = ast.parse(content, filename=str(path))
    except Exception as e:
        print(f"Skipping cleanup for {path} due to syntax error: {e}")
        return False

    doc = ast.get_docstring(tree, clean=False)
    if doc is None or "Test target:" not in doc:
        return False

    # Find the docstring node
    doc_node = None
    if tree.body and isinstance(tree.body[0], ast.Expr):
        val = tree.body[0].value
        if isinstance(val, ast.Constant) and isinstance(val.value, str):
            doc_node = tree.body[0]

    if not doc_node:
        return False

    lines = content.splitlines()
    prefix = doc.split("Test target:", 1)[0].strip()

    if not prefix:
        # The entire docstring was the template. We can remove it and any trailing empty lines.
        del lines[doc_node.lineno - 1 : doc_node.end_lineno]
        while lines and not lines[0].strip():
            del lines[0]
    else:
        quoted = quote_docstring(prefix, "")
        lines[doc_node.lineno - 1 : doc_node.end_lineno] = quoted

    path.write_text("\n".join(lines) + ("\n" if content.endswith("\n") else ""), encoding="utf-8")
    return True


def strip_template_from_function_docstring(path: Path) -> int:
    """
    Strip the Test Responsibility Template block from every test function docstring.

    Removes everything from the first occurrence of 'Test target:' to the end of the docstring,
    leaving any original description that preceded the template intact.
    Returns the number of functions modified.
    """
    content = path.read_text(encoding="utf-8")
    try:
        tree = ast.parse(content, filename=str(path))
    except Exception as e:
        print(f"Skipping strip for {path} due to syntax error: {e}")
        return 0

    lines = content.splitlines()
    test_funcs = [
        node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef) and node.name.startswith("test_")
    ]
    test_funcs.sort(key=lambda n: getattr(n, "lineno", 1), reverse=True)

    modified_count = 0
    for node in test_funcs:
        if not node.body:
            continue
        if not (isinstance(node.body[0], ast.Expr)):
            continue
        val = node.body[0].value
        if not (isinstance(val, ast.Constant) and isinstance(val.value, str)):
            continue
        doc_node = node.body[0]
        doc = ast.get_docstring(node, clean=False)
        if doc is None or "Test target:" not in doc:
            continue

        prefix = doc.split("Test target:", 1)[0].strip()

        first_stmt_line = lines[doc_node.lineno - 1]
        raw_indent = first_stmt_line[: len(first_stmt_line) - len(first_stmt_line.lstrip())]
        indent = raw_indent or "    "

        if not prefix:
            del lines[doc_node.lineno - 1 : doc_node.end_lineno]
        else:
            quoted = quote_docstring(prefix, indent)
            lines[doc_node.lineno - 1 : doc_node.end_lineno] = quoted
        modified_count += 1

    if modified_count > 0:
        path.write_text("\n".join(lines) + ("\n" if content.endswith("\n") else ""), encoding="utf-8")
    return modified_count


def inject_templates_to_test_functions(path: Path, *, force: bool = False) -> int:
    """
    Inject or append the Test Responsibility Template to each test function's docstring.
    """
    content = path.read_text(encoding="utf-8")
    try:
        tree = ast.parse(content, filename=str(path))
    except Exception as e:
        print(f"Skipping function docstrings for {path} due to syntax error: {e}")
        return 0

    lines = content.splitlines()

    # Collect all test functions
    test_funcs = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
            test_funcs.append(node)

    # Sort in reverse order of line numbers to preserve offsets
    test_funcs.sort(key=lambda n: getattr(n, "lineno", 1), reverse=True)

    modified_count = 0
    for node in test_funcs:
        if not node.body:
            continue

        doc = ast.get_docstring(node, clean=False)

        # Check if already has template
        if not force and doc is not None and "Test target:" in doc:
            continue

        # Check if first body element is a docstring
        has_doc_node = False
        doc_node = None
        if node.body and isinstance(node.body[0], ast.Expr):
            val = node.body[0].value
            if isinstance(val, ast.Constant) and isinstance(val.value, str):
                has_doc_node = True
                doc_node = node.body[0]

        # Determine indentation
        if doc_node:
            first_stmt_line = lines[doc_node.lineno - 1]
        else:
            first_stmt_line = lines[node.body[0].lineno - 1]
        indent = first_stmt_line[: len(first_stmt_line) - len(first_stmt_line.lstrip())]
        if not indent:
            indent = "    "

        if has_doc_node and doc_node:
            base_description = ""
            if doc:
                base_description = doc.split("Test target:", 1)[0].strip()

            if base_description:
                new_doc = base_description + "\n\n" + TEMPLATE_STR
            else:
                new_doc = TEMPLATE_STR

            quoted = quote_docstring(new_doc, indent)
            lines[doc_node.lineno - 1 : doc_node.end_lineno] = quoted
            modified_count += 1
        else:
            quoted = quote_docstring(TEMPLATE_STR, indent)
            start, end, replacement = header_insertion(node, lines, quoted)
            lines[start:end] = replacement
            modified_count += 1

    if modified_count > 0:
        path.write_text("\n".join(lines) + ("\n" if content.endswith("\n") else ""), encoding="utf-8")
        return modified_count
    return 0


def process_roots(roots: list[Path], exclude_names: set[str] | None = None, *, force: bool = False) -> int:
    """Programmatic entry point: inject templates into test files under roots."""
    if exclude_names is None:
        exclude_names = {"conftest.py", "test_pylint_checkers.py"}

    print("Collecting test files via pytest...")
    plugin = TestCollectorPlugin()
    pytest.main(["--collect-only", "-q"], plugins=[plugin])

    for folder in roots:
        if folder.exists():
            for p in folder.rglob("*.py"):
                if "__pycache__" in p.parts:
                    continue
                if any(ex in p.parts for ex in exclude_names):
                    continue
                if p.name.startswith("test_") or p.name.endswith("_test.py"):
                    plugin.test_files.add(p.resolve())

    print(f"Collected {len(plugin.test_files)} test files.")

    injected_funcs = 0
    cleaned_modules = 0
    stripped_funcs = 0
    for path in sorted(plugin.test_files):
        if path.suffix != ".py":
            continue
        if path.name in exclude_names:
            continue

        if cleanup_module_docstring(path):
            cleaned_modules += 1

        if force:
            stripped_funcs += strip_template_from_function_docstring(path)

        funcs_modified = inject_templates_to_test_functions(path, force=force)
        if funcs_modified > 0:
            injected_funcs += funcs_modified

    action = "re-injected" if force else "injected"
    print(
        f"Template injection complete. Cleaned {cleaned_modules} modules, "
        f"stripped {stripped_funcs} functions, {action} {injected_funcs} functions.",
    )
    return 0


def main() -> int:
    """Run test collection and perform template injection."""
    parser = argparse.ArgumentParser(description="Inject test responsibility templates into test functions.")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Strip and re-inject templates even when already present (use after template changes).",
    )
    parser.add_argument("--exclude", action="append", default=[], help="Directory name to exclude (repeatable)")
    parser.add_argument("--root", action="append", default=[], help="Root directory to scan (repeatable)")
    args = parser.parse_args()
    roots = [Path(r) for r in args.root] if args.root else [Path("src/pytest_bdd_testing"), Path("tests")]
    exclude_names = set(args.exclude) if args.exclude else {"conftest.py", "test_pylint_checkers.py"}
    return process_roots(roots, exclude_names, force=args.force)


if __name__ == "__main__":
    sys.exit(main())
