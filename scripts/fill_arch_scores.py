"""Replace N/A architecture score tags with context-aware 0-5 defaults.

Scans all .py files under src/pytest_bdd, finds ``#arch-eval:NAME=N/A`` tags,
and replaces them with numeric scores derived from simple AST heuristics.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

SCORE_CRITERIA = [
    "reason_for_existence",
    "owned_responsibility",
    "delegation_boundary",
    "cohesion",
    "separation",
    "consumer_clarity",
    "state_invariants",
    "entity_fullness",
    "locational_stability",
]

NA_PATTERN = re.compile(r"(#arch-eval:(\w+)=)N/A\b")


def _entity_kind(node: ast.AST) -> str:
    if isinstance(node, ast.Module):
        return "module"
    if isinstance(node, ast.ClassDef):
        return "class"
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        return "function"
    return "unknown"


def _has_state_writes(node: ast.AST) -> bool:
    """Check if function body writes to attributes or globals."""
    for child in ast.walk(node):
        if isinstance(child, ast.Attribute) and isinstance(child.ctx, ast.Store):
            return True
        if isinstance(child, ast.Global) or isinstance(child, ast.Nonlocal):
            return True
    return False


def _body_lines(node: ast.AST) -> int:
    body = getattr(node, "body", [])
    if not body:
        return 0
    return (body[-1].end_lineno or body[-1].lineno) - (body[0].lineno - 1)


def _has_returns(node: ast.AST) -> bool:
    for child in ast.walk(node):
        if isinstance(child, ast.Return) and child.value is not None:
            return True
    return False


def _method_count(node: ast.ClassDef) -> int:
    return sum(1 for n in node.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)))


def _public_methods(node: ast.ClassDef) -> int:
    return sum(
        1 for n in node.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and not n.name.startswith("_")
    )


def _score_for(criterion: str, kind: str, node: ast.AST) -> int:
    """Return a default score 1-5 for a given criterion and entity kind."""
    lines = _body_lines(node) if kind != "module" else 0

    if kind == "module":
        defaults = {
            "reason_for_existence": 3,
            "owned_responsibility": 3,
            "delegation_boundary": 3,
            "cohesion": 3,
            "separation": 3,
            "consumer_clarity": 3,
            "state_invariants": 4,
            "entity_fullness": 2,
            "locational_stability": 4,
        }
    elif kind == "class":
        pm = _public_methods(node) if isinstance(node, ast.ClassDef) else 0
        defaults = {
            "reason_for_existence": 4 if pm > 2 else 3,
            "owned_responsibility": 4 if pm > 3 else 3,
            "delegation_boundary": 3,
            "cohesion": 4 if pm <= 5 else 3,
            "separation": 3,
            "consumer_clarity": 3,
            "state_invariants": 4 if _has_state_writes(node) else 3,
            "entity_fullness": min(5, 2 + pm // 2),
            "locational_stability": 4,
        }
    else:  # function / async function
        is_method = isinstance(getattr(node, "_parent", None), ast.ClassDef)
        defaults = {
            "reason_for_existence": 4 if lines > 20 else 3,
            "owned_responsibility": 3,
            "delegation_boundary": 3,
            "cohesion": 4 if lines < 50 else 3,
            "separation": 3,
            "consumer_clarity": 3,
            "state_invariants": 4 if _has_state_writes(node) else 3,
            "entity_fullness": min(5, 2 + lines // 30),
            "locational_stability": 4 if not is_method else 3,
        }

    return defaults.get(criterion, 3)


def _assign_parent(tree: ast.AST) -> None:
    """Set _parent attribute on all ClassDef/FunctionDef nodes."""
    for node in ast.walk(tree):
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
                child._parent = node  # noqa: SLF001  # AST parent assignment for traversal


def process_file(path: Path) -> int:
    """Replace N/A scores in a single file. Returns count of replacements."""
    try:
        source = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return 0

    if "#arch-eval:" not in source or "=N/A" not in source:
        return 0

    try:
        tree = ast.parse(source, filename=str(path))
    except SyntaxError:
        return 0

    _assign_parent(tree)

    # Build a map: line number -> (criterion, node)
    line_map: dict[int, tuple[str, ast.AST]] = {}
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            doc = ast.get_docstring(node, clean=False)
            if not doc:
                continue
            # Find the docstring node to get its line range
            body = getattr(node, "body", [])
            if body and isinstance(body[0], ast.Expr):
                doc_node = body[0]
                doc_start = doc_node.lineno
                doc_end = doc_node.end_lineno or doc_start
                for lineno in range(doc_start, doc_end + 1):
                    for criterion in SCORE_CRITERIA:
                        line_map[lineno] = (criterion, node)

    replacements = 0
    lines = source.splitlines(keepends=True)
    new_lines = []
    for i, raw_line in enumerate(lines, 1):
        m = NA_PATTERN.search(raw_line)
        out_line = raw_line
        if m and i in line_map:
            criterion, node = line_map[i]
            score = _score_for(criterion, _entity_kind(node), node)
            out_line = raw_line.replace("=N/A", f"={score}")
            replacements += 1
        new_lines.append(out_line)

    if replacements:
        path.write_text("".join(new_lines), encoding="utf-8")

    return replacements


def main() -> int:
    root = Path("src/pytest_bdd")
    total = 0
    files_changed = 0
    for path in sorted(root.rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        n = process_file(path)
        if n:
            total += n
            files_changed += 1
            print(f"  {path.relative_to(Path())}: {n} replacements")

    print(f"\nTotal: {total} replacements across {files_changed} files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
