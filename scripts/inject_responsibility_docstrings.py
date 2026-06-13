"""Inject responsibility contracts into pytest-bdd source docstrings."""

from __future__ import annotations

import argparse
import ast
import json
import re
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path("src/pytest_bdd")
REPORT_PATH = Path(".planning/tmp/responsibility-docstrings-report.json")
TEMPLATE_MARKER = "Responsibility:"
MIN_LONG_SECTION = 140
_DEFAULT_SUMMARY_RE = re.compile(
    r"^`?[a-zA-Z0-9_\.]*`?\s+owns\s+documented\s+(?:module|class|function|method|async\s+function|async\s+method)\s+behavior\.$",
    re.IGNORECASE,
)
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


@dataclass(frozen=True)
class Entity:
    path: Path
    module: str
    qualname: str
    name: str
    kind: str
    node: ast.AST
    parent: str | None
    children: tuple[str, ...]
    calls: tuple[str, ...]
    imports: tuple[str, ...]
    state_writes: tuple[str, ...]
    raises: tuple[str, ...]
    existing_docstring: str | None


@dataclass
class SourceIndex:
    import_consumers: dict[str, set[str]] = field(default_factory=lambda: defaultdict(set))
    name_consumers: dict[str, set[str]] = field(default_factory=lambda: defaultdict(set))
    module_consumers: dict[str, set[str]] = field(default_factory=lambda: defaultdict(set))


class LocalFacts(ast.NodeVisitor):
    """Collect local calls, imports, writes, and raises."""

    def __init__(self) -> None:
        self.calls: Counter[str] = Counter()
        self.imports: list[str] = []
        self.state_writes: Counter[str] = Counter()
        self.raises: Counter[str] = Counter()

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            self.imports.append(alias.name)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        module = "." * node.level + (node.module or "")
        for alias in node.names:
            self.imports.append(f"{module}.{alias.name}".strip("."))

    def visit_Call(self, node: ast.Call) -> None:
        name = dotted_name(node.func)
        if name:
            self.calls[name] += 1
        self.generic_visit(node)

    def visit_Assign(self, node: ast.Assign) -> None:
        for target in node.targets:
            self._record_target(target)
        self.generic_visit(node)

    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        self._record_target(node.target)
        self.generic_visit(node)

    def visit_AugAssign(self, node: ast.AugAssign) -> None:
        self._record_target(node.target)
        self.generic_visit(node)

    def visit_Raise(self, node: ast.Raise) -> None:
        if node.exc is None:
            self.raises["re-raise"] += 1
        else:
            self.raises[dotted_name(node.exc) or type(node.exc).__name__] += 1
        self.generic_visit(node)

    def _record_target(self, target: ast.AST) -> None:
        if isinstance(target, ast.Attribute):
            name = dotted_name(target)
            if name:
                self.state_writes[name] += 1
        elif isinstance(target, ast.Name):
            self.state_writes[target.id] += 1
        elif isinstance(target, (ast.Tuple, ast.List)):
            for elt in target.elts:
                self._record_target(elt)


def dotted_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        base = dotted_name(node.value)
        return f"{base}.{node.attr}" if base else node.attr
    if isinstance(node, ast.Call):
        return dotted_name(node.func)
    return None


def module_name(path: Path, root: Path) -> str:
    relative = path.relative_to(root)
    parts = list(relative.parts)
    parts[-1] = parts[-1].removesuffix(".py")
    if parts[-1] == "__init__":
        parts = parts[:-1]
    return "pytest_bdd" + (f".{'.'.join(parts)}" if parts else "")


def iter_python_files(root: Path, exclude: tuple[str, ...] = ()) -> list[Path]:
    def _excluded(path: Path) -> bool:
        parts = path.parts
        return any(ex in parts for ex in exclude)

    return [path for path in sorted(root.rglob("*.py")) if "__pycache__" not in path.parts and not _excluded(path)]


def collect_source_index(root: Path, exclude: tuple[str, ...] = ()) -> SourceIndex:
    index = SourceIndex()
    for scan_root in (root, Path("tests")):
        if not scan_root.exists():
            continue
        for path in iter_python_files(scan_root, exclude):
            try:
                tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            except (OSError, SyntaxError, UnicodeDecodeError):
                continue
            consumer = path.as_posix()
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if alias.name.startswith("pytest_bdd"):
                            index.module_consumers[alias.name].add(consumer)
                            index.import_consumers[alias.name.rsplit(".", 1)[-1]].add(consumer)
                elif isinstance(node, ast.ImportFrom):
                    if node.module and node.module.startswith("pytest_bdd"):
                        index.module_consumers[node.module].add(consumer)
                    for alias in node.names:
                        index.import_consumers[alias.name].add(consumer)
                elif isinstance(node, ast.Name):
                    index.name_consumers[node.id].add(consumer)
                elif isinstance(node, ast.Attribute):
                    index.name_consumers[node.attr].add(consumer)
    return index


def facts_for(node: ast.AST) -> LocalFacts:
    facts = LocalFacts()
    facts.visit(node)
    return facts


def collect_entities(path: Path, root: Path) -> tuple[list[Entity], list[str]]:
    try:
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(path))
    except (OSError, SyntaxError, UnicodeDecodeError) as exc:
        return [], [f"{path}: {exc}"]

    mod = module_name(path, root)
    entities: list[Entity] = []

    def make_entity(node: ast.AST, qualname: str, name: str, kind: str, parent: str | None) -> Entity:
        facts = facts_for(node)
        children = tuple(
            child.name
            for child in getattr(node, "body", [])
            if isinstance(child, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef))
        )
        return Entity(
            path=path,
            module=mod,
            qualname=qualname,
            name=name,
            kind=kind,
            node=node,
            parent=parent,
            children=children,
            calls=tuple(name for name, _ in facts.calls.most_common(8)),
            imports=tuple(facts.imports[:8]),
            state_writes=tuple(name for name, _ in facts.state_writes.most_common(6)),
            raises=tuple(name for name, _ in facts.raises.most_common(4)),
            existing_docstring=ast.get_docstring(node),
        )

    entities.append(make_entity(tree, mod, mod.rsplit(".", 1)[-1], "module", None))

    def walk(body: list[ast.stmt], parent: str, class_stack: list[str]) -> None:
        for node in body:
            if isinstance(node, ast.ClassDef):
                qualname = f"{parent}.{node.name}"
                entities.append(make_entity(node, qualname, node.name, "class", parent))
                walk(node.body, qualname, [*class_stack, node.name])
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if any(
                    (isinstance(dec, ast.Name) and dec.id == "overload")
                    or (isinstance(dec, ast.Attribute) and dec.attr == "overload")
                    for dec in node.decorator_list
                ):
                    continue
                qualname = f"{parent}.{node.name}"
                if isinstance(node, ast.AsyncFunctionDef):
                    kind = "async method" if class_stack else "async function"
                else:
                    kind = "method" if class_stack else "function"
                entities.append(make_entity(node, qualname, node.name, kind, parent))
                walk(node.body, qualname, class_stack)
            else:
                for nested in getattr(node, "body", []):
                    if isinstance(nested, ast.stmt):
                        walk([nested], parent, class_stack)
                for nested in getattr(node, "orelse", []):
                    if isinstance(nested, ast.stmt):
                        walk([nested], parent, class_stack)
                for nested in getattr(node, "finalbody", []):
                    if isinstance(nested, ast.stmt):
                        walk([nested], parent, class_stack)
                for handler in getattr(node, "handlers", []):
                    walk(list(getattr(handler, "body", [])), parent, class_stack)

    walk(tree.body, mod, [])
    return entities, []


def consumers_for(entity: Entity, index: SourceIndex) -> list[str]:
    consumers = set(index.import_consumers.get(entity.name, set()))
    consumers.update(index.name_consumers.get(entity.name, set()))
    consumers.update(index.module_consumers.get(entity.module, set()))
    consumers.discard(entity.path.as_posix())
    return sorted(consumers)[:5]


def first_sentence(text: str | None, fallback: str) -> str:
    if not text:
        return fallback
    summary = " ".join(text.strip().split())
    if not summary:
        return fallback
    return summary.split(". ")[0].rstrip(".") + "."


def pad_minimum(text: str, extra: str) -> str:
    if len(text) >= MIN_LONG_SECTION:
        return text
    return f"{text} {extra}"


_SCORE_DESCRIPTIONS = {
    "reason_for_existence": "Motivation / information-expert fitness (1-5, or N/A)",
    "owned_responsibility": "Clean boundary and clear ownership (1-5, or N/A)",
    "delegation_boundary": "Sub-task encapsulation quality (1-5, or N/A)",
    "cohesion": "Internal logic focus (1-5, or N/A)",
    "separation": "Distinctness from peers (1-5, or N/A)",
    "consumer_clarity": "Clarity of public API / usage contract (1-5, or N/A)",
    "state_invariants": "Control of state mutations (1-5, or N/A)",
    "entity_fullness": "Content richness vs empty shell (1-5, or N/A)",
    "locational_stability": "Resistance to hierarchical moves (1-5, or N/A)",
}


def make_stub_template(entity: Entity) -> str:
    """Create a blank responsibility skeleton for agent-driven filling.

    Every section is a placeholder to be filled by an architecture-aware agent
    that has read the full source file and analyzed the project structure.
    """
    kind = entity.kind
    kind_map = {
        "module": "module",
        "class": "class",
        "function": "function",
        "method": "method",
        "async function": "async function",
        "async method": "async method",
    }
    kind_text = kind_map.get(kind, kind)

    lines = [
        "",
        "Responsibility:",
        f"    <Describe the single primary job, contract, or behavior this {kind_text} directly implements and owns. This defines the boundary for where changes to this logic belong. Must be at least 140 characters.>",
        "",
        "Reason for existence:",
        f"    <Explain why this code is kept together in this specific {kind_text} rather than being merged elsewhere. Why is it the information expert for this logical boundary? Analyze: imports, call signature, owned data, and failure knowledge. Must be at least 140 characters.>",
        "",
        "Delegates:",
        "    - <collaborator/sub-entity>: <Describe what sub-task or helper role this collaborator performs to support this boundary. Use actual names of children or called functions found in the source. Add more bullet points as needed.>",
        "",
        "Cohesion:",
        "    <Explain why all logic inside this entity belongs together. Analyze the actual source: do all functions operate on same local state? Share same imports and control flow? Or is it a bag of unrelated utilities?>",
        "",
        "Separation:",
        "    - <peer/sibling entity>: <Explain why this entity is kept separate from this sibling, to prevent callers from coupling to too much knowledge at once. Name the actual peer entity. Add more bullet points as needed.>",
        "",
        "Main consumers:",
        "    - <importer/caller/workflow>: <Describe how this consumer utilizes this entity, defining the public API contract we must keep stable. Use actual import paths from the codebase. Add more bullet points as needed.>",
        "",
        "State and side effects:",
        "    <Describe any local mutable state, file/network I/O, configuration access, or pytest stash reads/writes this entity performs. Analyze the actual source code. If stateless, specify 'None, keeps no persistent state'.>",
    ]
    if entity.kind in {"module", "class"}:
        lines.extend(
            [
                "",
                "Invariants:",
                "    - <State the assumptions, data constraints, or execution rules that must always hold true for this entity and can never be broken. Analyze the actual source for implicit contracts.>",
            ],
        )
    if entity.raises:
        lines.extend(
            [
                "",
                "Failure semantics:",
                f"    <Describe what errors this entity raises ({', '.join(entity.raises[:3])}) and how callers should handle them. Analyze the actual raise statements in the source.>",
            ],
        )
    extra_note = ""
    if entity.kind == "module" and entity.path.name == "__init__.py":
        extra_note = " — evaluate the entire package, not just this __init__.py file"
    lines.extend(
        [
            "",
            "Architecture score:",
            f"    # Use 1-5 for each criterion, or N/A if the criterion does not apply to this entity{extra_note}",
            "    # (N/A criteria are excluded from the harmonic mean calculation)",
        ],
    )
    for criterion in SCORE_CRITERIA:
        desc = _SCORE_DESCRIPTIONS.get(criterion, f"{criterion} score (1-5 or N/A)")
        lines.append(f"    #arch-eval:{criterion}=<1-5 or N/A>  # {desc}")
    return "\n".join(lines)


def cleaned_docstring(existing: str | None) -> str:
    if not existing:
        return ""
    if TEMPLATE_MARKER not in existing:
        return existing.rstrip()
    return existing[: existing.index(TEMPLATE_MARKER)].rstrip()


def quote_docstring(content: str, indent: str) -> list[str]:
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


def docstring_stmt(node: ast.AST) -> ast.Expr | None:
    body = getattr(node, "body", None)
    if not body:
        return None
    first = body[0]
    if isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant) and isinstance(first.value.value, str):
        return first
    return None


def header_insertion(node: ast.AST, lines: list[str], doc_lines: list[str]) -> tuple[int, int, list[str]]:
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


def rewrite_file(
    path: Path,
    entities: list[Entity],
    *,
    check_mode: bool = False,
) -> tuple[str, Counter[str], list[str]]:
    source = path.read_text(encoding="utf-8")
    lines = source.splitlines()
    replacements: list[tuple[int, int, list[str]]] = []
    counts: Counter[str] = Counter()
    errors: list[str] = []
    for entity in sorted(entities, key=lambda item: getattr(item.node, "lineno", 1), reverse=True):
        stmt = docstring_stmt(entity.node)
        if stmt is not None:
            indent = re.match(r"\s*", lines[stmt.lineno - 1]).group(0)
        elif isinstance(entity.node, ast.Module):
            indent = ""
        else:
            node_idx = getattr(entity.node, "lineno", 1) - 1
            if node_idx < len(lines):
                node_indent = re.match(r"\s*", lines[node_idx]).group(0)
            else:
                node_indent = ""
            indent = node_indent + "    "

        if check_mode:
            existing = entity.existing_docstring
            if existing and (
                "<1-5>" in existing or "<0-5>" in existing or "<Describe" in existing or "<Explain" in existing
            ):
                counts["pending_fill"] += 1
            elif existing and TEMPLATE_MARKER in existing:
                counts["already_present"] += 1
            else:
                counts["missing"] += 1
            continue

        # Stub mode: always replace with fresh blank template
        template = make_stub_template(entity)
        qualname = entity.qualname
        if len(qualname) > 60:
            parts = qualname.split(".")
            qualname = ".".join(parts[-2:]) if len(parts) > 2 else qualname
        summary = f"<One-line summary in imperative mood (e.g. 'Return', 'Parse', 'Validate', 'Provide') — what this {entity.kind} does, not how>"
        new_doc = summary + "\n\n" + template.lstrip("\n")

        try:  # noqa: PLW0717
            if stmt is not None:
                replacements.append((stmt.lineno - 1, stmt.end_lineno or stmt.lineno, quote_docstring(new_doc, indent)))
                counts["docstrings_updated"] += 1
            elif isinstance(entity.node, ast.Module):
                replacements.append((0, 0, quote_docstring(new_doc, "")))
                counts["docstrings_added"] += 1
            else:
                replacements.append(header_insertion(entity.node, lines, quote_docstring(new_doc, "")))
                counts["docstrings_added"] += 1
        except (IndexError, AttributeError) as exc:
            errors.append(f"{path}:{entity.qualname}: {exc}")
            counts["skipped"] += 1
    for start, end, replacement in sorted(replacements, reverse=True):
        lines[start:end] = replacement
    return "\n".join(lines) + ("\n" if source.endswith("\n") else ""), counts, errors


def build_report(
    root: Path,
    *,
    check: bool = False,
    write_stubs: bool = False,
    exclude: tuple[str, ...] = (),
) -> tuple[dict[str, object], bool]:
    collect_source_index(root, exclude)
    all_entities: list[Entity] = []
    errors: list[str] = []
    for path in iter_python_files(root, exclude):
        entities, file_errors = collect_entities(path, root)
        all_entities.extend(entities)
        errors.extend(file_errors)
    by_file: dict[Path, list[Entity]] = defaultdict(list)
    for entity in all_entities:
        by_file[entity.path].append(entity)
    totals: Counter[str] = Counter()
    changed = False
    for path, entities in by_file.items():
        try:
            original = path.read_text(encoding="utf-8")
            rewritten, counts, rewrite_errors = rewrite_file(path, entities, check_mode=check)
        except OSError as exc:
            errors.append(f"{path}: {exc}")
            continue
        totals.update(counts)
        errors.extend(rewrite_errors)
        if rewritten != original:
            changed = True
            if write_stubs:
                path.write_text(rewritten, encoding="utf-8")
    report: dict[str, object] = {
        "files_scanned": len(by_file),
        "modules_seen": sum(1 for entity in all_entities if entity.kind == "module"),
        "classes_seen": sum(1 for entity in all_entities if entity.kind == "class"),
        "functions_seen": sum(1 for entity in all_entities if "function" in entity.kind),
        "methods_seen": sum(1 for entity in all_entities if "method" in entity.kind),
        "docstrings_added": totals["docstrings_added"],
        "docstrings_updated": totals["docstrings_updated"],
        "already_present": totals["already_present"],
        "pending_fill": totals["pending_fill"],
        "missing": totals["missing"],
        "skipped": totals["skipped"],
        "errors": errors,
    }
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report, changed


def main() -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true", help="Check if stubs are filled (CI mode)")
    mode.add_argument("--stub", action="store_true", help="Inject blank templates for agent-driven filling")
    parser.add_argument("root", nargs="?", default=str(ROOT))
    parser.add_argument("--exclude", action="append", default=[], help="Directory name to exclude (can be repeated)")
    args = parser.parse_args()
    exclude = tuple(args.exclude)
    report, changed = build_report(
        Path(args.root),
        check=args.check,
        write_stubs=args.stub,
        exclude=exclude,
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    if args.check and changed:
        print("Responsibility docstrings are not up to date.", file=sys.stderr)
        return 1
    return 0 if not report["errors"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
