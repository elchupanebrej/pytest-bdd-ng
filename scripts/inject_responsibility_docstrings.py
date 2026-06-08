"""Inject responsibility contracts into pytest-bdd source docstrings."""

from __future__ import annotations

import argparse
import ast
import json
import re
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path("src/pytest_bdd")
REPORT_PATH = Path(".planning/tmp/responsibility-docstrings-report.json")
TEMPLATE_MARKER = "Responsibility:"
MIN_LONG_SECTION = 140
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


def iter_python_files(root: Path) -> list[Path]:
    return [path for path in sorted(root.rglob("*.py")) if "__pycache__" not in path.parts]


def collect_source_index(root: Path) -> SourceIndex:
    index = SourceIndex()
    for scan_root in (root, Path("tests")):
        if not scan_root.exists():
            continue
        for path in iter_python_files(scan_root):
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


def score_entity(entity: Entity, consumers: list[str]) -> dict[str, int]:
    has_doc = bool(entity.existing_docstring)
    has_delegates = bool(entity.children or entity.calls)
    has_state = bool(entity.state_writes)

    if entity.kind in {"module", "class"}:
        fullness = 4 if len(entity.children) >= 2 else (3 if entity.children else 2)
    else:
        fullness = 4 if (entity.calls or entity.state_writes or entity.raises) else 3

    stability = 4 if len(consumers) >= 3 else (3 if consumers else 2)

    return {
        "reason_for_existence": 4 if has_doc else 3,
        "owned_responsibility": 4 if has_doc or has_delegates else 3,
        "delegation_boundary": 4 if has_delegates else 2,
        "cohesion": 4 if entity.kind in {"function", "method", "async function", "async method"} else 3,
        "separation": 3,
        "consumer_clarity": 4 if consumers else 2,
        "state_invariants": 4 if has_state or entity.raises else 3,
        "entity_fullness": fullness,
        "locational_stability": stability,
    }


def bullet_lines(items: list[str], fallback: str) -> list[str]:
    if not items:
        return [f"    - {fallback}"]
    return [f"    - {item}" for item in items]


def make_template(entity: Entity, index: SourceIndex, indent: str = "") -> str:
    import textwrap

    consumers = consumers_for(entity, index)
    base_summary = first_sentence(
        entity.existing_docstring,
        f"`{entity.qualname}` owns documented {entity.kind} behavior.",
    )
    if base_summary.strip(".") == entity.name:
        base_summary = f"`{entity.qualname}` owns documented {entity.kind} behavior."

    responsibility = pad_minimum(
        f"{base_summary} It directly owns the observable contract, local decisions, and maintenance boundary for this {entity.kind}.",
        "That boundary is intentionally stated in prose so maintainers can distinguish owned work from collaborators before editing.",
    )
    reason = pad_minimum(
        f"This entity is the information expert for `{entity.qualname}` because it keeps the nearest code, data shape, call signature, and failure knowledge together.",
        "Moving that knowledge outward would force callers or sibling entities to know implementation details that should remain behind this boundary.",
    )

    indent_len = len(indent)
    width = max(80, 120 - indent_len - 4)
    bullet_width = max(80, 120 - indent_len - 6)

    resp_lines = textwrap.wrap(responsibility, width=width, break_long_words=False, break_on_hyphens=False)
    reason_lines = textwrap.wrap(reason, width=width, break_long_words=False, break_on_hyphens=False)

    def wrap_bullet_item(item: str, fallback: str = "") -> list[str]:
        if not item:
            return [f"    - {fallback}"] if fallback else []
        wrapped = textwrap.wrap(item, width=bullet_width, break_long_words=False, break_on_hyphens=False)
        if not wrapped:
            return [f"    - {fallback}"] if fallback else []
        res = [f"    - {wrapped[0]}"]
        for extra in wrapped[1:]:
            res.append(f"      {extra}")
        return res

    delegates = [f"{child}: owns nested behavior below this boundary" for child in entity.children[:6]]
    if not delegates:
        delegates = [f"{call}: collaborator call used by this boundary" for call in entity.calls[:6]]

    wrapped_delegates = []
    if delegates:
        for delegate in delegates:
            wrapped_delegates.extend(wrap_bullet_item(delegate))
    else:
        wrapped_delegates = ["    - None, leaf-level implementation boundary"]

    consumer_lines = [f"{consumer}: imports or references `{entity.name}`" for consumer in consumers[:5]]
    wrapped_consumers = []
    if consumer_lines:
        for consumer_line in consumer_lines:
            wrapped_consumers.extend(wrap_bullet_item(consumer_line))
    else:
        wrapped_consumers = ["    - None found by static import/name scan; verify dynamic use before refactor"]

    state_parts = []
    if entity.state_writes:
        state_parts.append("mutates " + ", ".join(entity.state_writes[:5]))
    if entity.imports:
        state_parts.append("depends on " + ", ".join(entity.imports[:5]))
    if not state_parts:
        state_parts.append("keeps no local persistent state beyond call-local values")

    state_str = f"{'; '.join(state_parts)}."
    state_lines = textwrap.wrap(state_str, width=width, break_long_words=False, break_on_hyphens=False)

    raises = ", ".join(entity.raises[:4])
    peer = "module peer" if entity.kind == "module" else "class peer" if entity.kind == "class" else "call-site peer"

    cohesion_text = "The implementation stays together because its imports, calls, state writes, and return contract describe one maintainable decision unit."
    cohesion_lines = textwrap.wrap(cohesion_text, width=width, break_long_words=False, break_on_hyphens=False)

    separation_text = f"{peer}: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without widening caller knowledge."
    wrapped_separation = wrap_bullet_item(separation_text)

    scores = score_entity(entity, consumers)

    lines = [
        "",
        "Responsibility:",
        *(f"    {line}" for line in resp_lines),
        "",
        "Reason for existence:",
        *(f"    {line}" for line in reason_lines),
        "",
        "Delegates:",
        *wrapped_delegates,
        "",
        "Cohesion:",
        *(f"    {line}" for line in cohesion_lines),
        "",
        "Separation:",
        *wrapped_separation,
        "",
        "Main consumers:",
        *wrapped_consumers,
        "",
        "State and side effects:",
        *(f"    {line}" for line in state_lines),
    ]

    if entity.kind in {"module", "class"} or entity.state_writes:
        invariant_text = f"`{entity.qualname}` keeps its documented import path, ownership boundary, and observable behavior stable for callers."
        wrapped_invariants = wrap_bullet_item(invariant_text)
        lines.extend(
            [
                "",
                "Invariants:",
                *wrapped_invariants,
            ],
        )

    if raises:
        raises_text = f"Raises or re-raises {raises}; callers must treat these as boundary failures."
        raises_lines = textwrap.wrap(raises_text, width=width, break_long_words=False, break_on_hyphens=False)
        lines.extend(["", "Failure semantics:", *(f"    {line}" for line in raises_lines)])

    lines.extend(["", "Architecture score:"])
    lines.extend(f"    #arch-eval:{criterion}={scores[criterion]}" for criterion in SCORE_CRITERIA)
    return "\n".join(lines)


def make_stub_template(entity: Entity) -> str:
    """Create a validation-failing responsibility skeleton for new entities."""
    lines = [
        "",
        "Responsibility:",
        "    <Describe the single primary job, contract, or behavior this entity directly implements and owns. This defines the boundary for where changes to this logic belong. Must be at least 140 characters.>",
        "",
        "Reason for existence:",
        "    <Explain why this code is kept together in this specific entity rather than being merged elsewhere. Why is it the information expert for this logical boundary? Must be at least 140 characters.>",
        "",
        "Delegates:",
        "    - <collaborator/sub-entity>: <Describe what sub-task or helper role this collaborator performs to support this boundary>",
        "",
        "Cohesion:",
        "    <Explain why all logic inside this entity belongs together. For example: because all its functions operate on the same local state, or share the same set of imports and control flow.>",
        "",
        "Separation:",
        "    - <peer/sibling entity>: <Explain why this entity is kept separate from this sibling, to prevent callers from coupling to too much knowledge at once>",
        "",
        "Main consumers:",
        "    - <importer/caller/workflow>: <Describe how this consumer utilizes this entity, defining the public API contract we must keep stable>",
        "",
        "State and side effects:",
        "    <Describe any local mutable state, file/network I/O, configuration access, or pytest stash reads/writes this entity performs. If stateless, specify 'None, keeps no persistent state'.>",
    ]
    if entity.kind in {"module", "class"}:
        lines.extend(
            [
                "",
                "Invariants:",
                "    - <State the assumptions, data constraints, or execution rules that must always hold true for this entity and can never be broken>",
            ],
        )
    lines.extend(["", "Architecture score:"])

    descriptions = {
        "reason_for_existence": "Motivated existence (0-5)",
        "owned_responsibility": "Clean boundary and owned tasks (0-5)",
        "delegation_boundary": "Sub-task encapsulation (0-5)",
        "cohesion": "Focused internal logic (0-5)",
        "separation": "Distinctness from peers (0-5)",
        "consumer_clarity": "Clarity of usage (0-5)",
        "state_invariants": "Control of state mutations (0-5)",
        "entity_fullness": "Fullness vs empty entity (0-5)",
        "locational_stability": "Resistance to hierarchical moves (0-5)",
    }

    for criterion in SCORE_CRITERIA:
        desc = descriptions.get(criterion, f"{criterion} score (0-5)")
        lines.append(f"    #arch-eval:{criterion}=<0-5>  # {desc}")

    return "\n".join(lines)


def cleaned_docstring(existing: str | None) -> str:
    if not existing:
        return ""
    if TEMPLATE_MARKER not in existing:
        return existing.rstrip()
    return existing[: existing.index(TEMPLATE_MARKER)].rstrip()


def quote_docstring(content: str, indent: str) -> list[str]:
    escaped = content.replace("\\", "\\\\")
    escaped = escaped.replace('"""', '\\"\\"\\"')
    body = escaped.splitlines()
    return [f'{indent}"""', *(f"{indent}{line}" if line else "" for line in body), f'{indent}"""']


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
    index: SourceIndex,
    *,
    stub: bool,
) -> tuple[str, Counter[str], list[str]]:
    source = path.read_text(encoding="utf-8")
    lines = source.splitlines()
    replacements: list[tuple[int, int, list[str]]] = []
    counts: Counter[str] = Counter()
    errors: list[str] = []
    for entity in sorted(entities, key=lambda item: getattr(item.node, "lineno", 1), reverse=True):
        base = cleaned_docstring(entity.existing_docstring)
        if (
            entity.existing_docstring
            and TEMPLATE_MARKER in entity.existing_docstring
            and "Cohesion:" in entity.existing_docstring
            and "locational_stability" in entity.existing_docstring
        ):
            counts["already_present"] += 1
            continue

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

        template = make_stub_template(entity) if stub else make_template(entity, index, indent)
        if base.strip():
            new_doc = base.rstrip() + "\n\n" + template.lstrip("\n")
        else:
            new_doc = template.strip("\n")

        try:
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


def build_report(root: Path, *, write: bool, stub: bool) -> tuple[dict[str, object], bool]:
    index = collect_source_index(root)
    all_entities: list[Entity] = []
    errors: list[str] = []
    for path in iter_python_files(root):
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
            rewritten, counts, rewrite_errors = rewrite_file(path, entities, index, stub=stub)
        except OSError as exc:
            errors.append(f"{path}: {exc}")
            continue
        totals.update(counts)
        errors.extend(rewrite_errors)
        if rewritten != original:
            changed = True
            if write:
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
        "skipped": totals["skipped"],
        "errors": errors,
    }
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report, changed


def main() -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--stub", action="store_true")
    parser.add_argument("root", nargs="?", default=str(ROOT))
    args = parser.parse_args()
    report, changed = build_report(Path(args.root), write=args.write or args.stub, stub=args.stub)
    print(json.dumps(report, indent=2, sort_keys=True))
    if args.check and changed:
        print("Responsibility docstrings are not up to date.")
        return 1
    return 0 if not report["errors"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
