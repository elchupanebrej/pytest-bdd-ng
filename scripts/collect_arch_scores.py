"""Collect responsibility architecture scores for all pytest-bdd entities."""

from __future__ import annotations

import ast
import json
import re
import sys
from collections import defaultdict
from dataclasses import asdict, dataclass
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
REQUIRED_SECTIONS = [
    "Responsibility",
    "Reason for existence",
    "Delegates",
    "Cohesion",
    "Separation",
    "Main consumers",
    "State and side effects",
    "Architecture score",
]
OPTIONAL_FUNCTION_SECTIONS = {"Invariants", "Failure semantics"}
LONG_SECTION_MIN = 140
SCORE_TAG_RE = re.compile(r"#arch-eval:(\w+)=(\d)")
OBJECT_MAP_JSON = Path(".planning/tmp/object-map.json")


@dataclass(frozen=True)
class ObjectEntry:
    module: str
    qualname: str
    name: str
    kind: str
    file: str
    line: int
    responsibility: str
    reason_for_existence: str
    consumers: str
    scores: dict[str, int]
    missing_sections: list[str]

    @property
    def average(self) -> float:
        values = [self.scores.get(criterion, 0) for criterion in SCORE_CRITERIA]
        return sum(values) / len(values)

    @property
    def documented(self) -> bool:
        return not self.missing_sections and bool(self.responsibility)


def module_key(path: Path, root: Path) -> str:
    relative = path.relative_to(root)
    parts = list(relative.parts)
    parts[-1] = parts[-1].removesuffix(".py")
    if parts[-1] == "__init__":
        parts = parts[:-1]
    return "pytest_bdd" + (f".{'.'.join(parts)}" if parts else "")


def package_key(module: str) -> str:
    parts = module.split(".")
    return module if len(parts) <= 2 else ".".join(parts[:3])


def iter_python_files(root: Path) -> list[Path]:
    return [path for path in sorted(root.rglob("*.py")) if "__pycache__" not in path.parts]


def parse_sections(docstring: str | None) -> dict[str, str]:
    if not docstring:
        return {}
    sections: dict[str, list[str]] = {}
    current: str | None = None
    headings = {f"{section}:" for section in [*REQUIRED_SECTIONS, *OPTIONAL_FUNCTION_SECTIONS]}
    for raw_line in docstring.splitlines():
        line = raw_line.strip()
        if line in headings:
            current = line[:-1]
            sections[current] = []
        elif current:
            sections[current].append(raw_line)
    return {key: "\n".join(value).strip() for key, value in sections.items()}


def section_first_line(sections: dict[str, str], key: str) -> str:
    for line in sections.get(key, "").splitlines():
        clean = line.strip(" -")
        if clean:
            return clean
    return ""


def parse_scores(docstring: str | None) -> dict[str, int]:
    scores = dict.fromkeys(SCORE_CRITERIA, 0)
    if not docstring:
        return scores
    for criterion, value in SCORE_TAG_RE.findall(docstring):
        if criterion in scores:
            scores[criterion] = max(scores[criterion], int(value))
    return scores


def entity_kind(node: ast.AST, class_stack: list[str]) -> str:
    if isinstance(node, ast.ClassDef):
        return "class"
    if isinstance(node, ast.AsyncFunctionDef):
        return "async method" if class_stack else "async function"
    if isinstance(node, ast.FunctionDef):
        return "method" if class_stack else "function"
    return "module"


def missing_sections(kind: str, sections: dict[str, str]) -> list[str]:
    required = list(REQUIRED_SECTIONS)
    if kind in {"module", "class"}:
        required.append("Invariants")
    missing = [section for section in required if not sections.get(section)]
    for section in ("Responsibility", "Reason for existence"):
        if sections.get(section) and len(" ".join(sections[section].split())) < LONG_SECTION_MIN:
            missing.append(f"{section} < {LONG_SECTION_MIN} chars")
    return missing


def collect_entries(root: Path) -> list[ObjectEntry]:
    entries: list[ObjectEntry] = []
    for path in iter_python_files(root):
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except (OSError, SyntaxError, UnicodeDecodeError) as exc:
            print(f"Skipping {path}: {exc}", file=sys.stderr)
            continue
        module = module_key(path, root)

        def append_entry(node: ast.AST, qualname: str, name: str, kind: str) -> None:
            docstring = ast.get_docstring(node)
            sections = parse_sections(docstring)
            entries.append(
                ObjectEntry(
                    module=module,
                    qualname=qualname,
                    name=name,
                    kind=kind,
                    file=path.as_posix(),
                    line=getattr(node, "lineno", 1),
                    responsibility=section_first_line(sections, "Responsibility"),
                    reason_for_existence=section_first_line(sections, "Reason for existence"),
                    consumers=section_first_line(sections, "Main consumers"),
                    scores=parse_scores(docstring),
                    missing_sections=missing_sections(kind, sections),
                ),
            )

        append_entry(tree, module, module.rsplit(".", 1)[-1], "module")

        def walk(body: list[ast.stmt], parent: str, class_stack: list[str]) -> None:
            for node in body:
                if isinstance(node, ast.ClassDef):
                    qualname = f"{parent}.{node.name}"
                    append_entry(node, qualname, node.name, "class")
                    walk(node.body, qualname, [*class_stack, node.name])
                elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    qualname = f"{parent}.{node.name}"
                    append_entry(node, qualname, node.name, entity_kind(node, class_stack))
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

        walk(tree.body, module, [])
    return entries


def risk_reason(entry: ObjectEntry) -> str:
    reasons = []
    if entry.average < 3:
        reasons.append("low average score")
    if entry.missing_sections:
        reasons.append("missing " + ", ".join(entry.missing_sections[:3]))
    if not entry.consumers:
        reasons.append("no static consumers")
    if entry.scores.get("state_invariants", 0) < 3:
        reasons.append("weak state/invariant evidence")
    return "; ".join(reasons) or "watch"


def write_json(entries: list[ObjectEntry]) -> None:
    OBJECT_MAP_JSON.parent.mkdir(parents=True, exist_ok=True)
    payload = [
        {**asdict(entry), "average": round(entry.average, 2), "documented": entry.documented} for entry in entries
    ]
    OBJECT_MAP_JSON.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def generate_object_map(entries: list[ObjectEntry], output_path: Path) -> None:
    by_package: dict[str, list[ObjectEntry]] = defaultdict(list)
    by_module: dict[str, list[ObjectEntry]] = defaultdict(list)
    for entry in entries:
        by_package[package_key(entry.module)].append(entry)
        by_module[entry.module].append(entry)
    documented = [entry for entry in entries if entry.documented]
    missing = [entry for entry in entries if entry.missing_sections]
    lines = [
        "# pytest-bdd Responsibility Object Map",
        "",
        "Generated by `scripts/collect_arch_scores.py` from responsibility contracts in Python docstrings.",
        "",
        "## Summary",
        "",
        f"- Total entities: {len(entries)}",
        f"- Documented entities: {len(documented)}",
        f"- Missing responsibility sections: {len(missing)}",
        "",
        "### Average by Package",
        "",
        "| Package | Entities | Documented | Average |",
        "|---|---:|---:|---:|",
    ]
    for package, package_entries in sorted(by_package.items()):
        avg = sum(entry.average for entry in package_entries) / len(package_entries)
        doc_count = sum(1 for entry in package_entries if entry.documented)
        lines.append(f"| `{package}` | {len(package_entries)} | {doc_count} | {avg:.2f} |")
    lines.extend(["", "### Bottom 30 Entities by Score", "", "| Entity | Kind | Score | Risk |", "|---|---|---:|---|"])
    for entry in sorted(entries, key=lambda item: (item.average, item.qualname))[:30]:
        lines.append(f"| `{entry.qualname}` | {entry.kind} | {entry.average:.2f} | {risk_reason(entry)} |")
    lines.extend(["", "### Top Architectural Risk Zones", ""])
    for package, package_entries in sorted(
        by_package.items(),
        key=lambda item: sum(entry.average < 3 for entry in item[1]),
        reverse=True,
    )[:12]:
        low = sum(1 for entry in package_entries if entry.average < 3)
        avg = sum(entry.average for entry in package_entries) / len(package_entries)
        lines.append(f"- `{package}`: {low} entities below 3.0 average; package average {avg:.2f}.")
    lines.extend(["", "## Entity Hierarchy", ""])
    for package in sorted(by_package):
        lines.extend([f"### Package `{package}`", ""])
        for module in sorted({entry.module for entry in by_package[package]}):
            lines.extend([f"#### Module `{module}`", ""])
            lines.append(
                "| Entity | Kind | File:Line | Responsibility | Main consumers | Average | Scores | Missing Sections |",
            )
            lines.append("|---|---|---|---|---|---:|---|---|")
            for entry in sorted(
                by_module[module],
                key=lambda item: (item.qualname.count("."), item.line, item.qualname),
            ):
                scores = ", ".join(f"{key}={entry.scores.get(key, 0)}" for key in SCORE_CRITERIA)
                missing_text = ", ".join(entry.missing_sections) if entry.missing_sections else "None"
                lines.append(
                    f"| `{entry.qualname}` | {entry.kind} | `{entry.file}:{entry.line}` | "
                    f"{entry.responsibility or 'Missing'} | {entry.consumers or 'None found'} | "
                    f"{entry.average:.2f} | {scores} | {missing_text} |",
                )
            lines.append("")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    root = Path(args[0]) if args else Path("src/pytest_bdd")
    if not root.is_dir():
        print(f"Error: {root} is not a directory", file=sys.stderr)
        return 2
    entries = collect_entries(root)
    write_json(entries)
    output = Path("docs/architecture/OBJECT_MAP.md")
    generate_object_map(entries, output)
    documented = sum(1 for entry in entries if entry.documented)
    print(f"Scanned {len(entries)} entities under {root}.")
    print(f"Documented: {documented}; missing sections: {len(entries) - documented}.")
    print(f"Output: {output}")
    print(f"JSON: {OBJECT_MAP_JSON}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
