"""
Collect test quality evaluation scores for all pytest-cuke test entities.

Responsibility:
    Parses test module and function docstrings, extracts `#test-eval` scores, and compiles a quality report.

Reason for existence:
    Provides visibility into the quality characteristics of our test suite.
"""

from __future__ import annotations

import ast
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

TEST_SCORE_CRITERIA = [
    "isolation",
    "determinism",
    "setup_complexity",
    "assertions_clarity",
]

SCORE_TAG_RE = re.compile(r"#test-eval:(\w+)=(N/A|[1-5])")
TEST_REPORT_JSON = Path(".planning/tmp/test-quality-report.json")

TEMPLATE_FIELDS = (
    "Test target",
    "Test type",
    "Test scenario",
    "BDD reference",
    "Fixtures",
    "Mocks",
    "Side effects",
    "Reduction",
    "Escalation",
    "Atomicity",
    "Autonomy",
)


@dataclass(frozen=True)
class TestQualityEntry:
    file: str
    target: str
    test_type: str
    scores: dict[str, int]

    @property
    def average(self) -> float | None:
        values = [v for v in self.scores.values() if v > 0]
        if not values:
            return None
        return len(values) / sum(1.0 / v for v in values)


def parse_test_eval_tags(docstring: str | None) -> dict[str, int]:
    """Parse #test-eval tags from docstring."""
    if not docstring:
        return {}
    scores: dict[str, int] = {}
    for match in SCORE_TAG_RE.finditer(docstring):
        criterion, val = match.groups()
        if criterion in TEST_SCORE_CRITERIA and val != "N/A":
            scores[criterion] = int(val)
    return scores


def collect_entries(roots: list[Path], exclude_names: set[str] | None = None) -> list[TestQualityEntry]:
    """Collect test quality entries from test files under roots."""
    if exclude_names is None:
        exclude_names = {"__init__.py", "conftest.py"}

    paths: list[Path] = []
    for root in roots:
        if root.exists():
            paths.extend(root.rglob("*.py"))

    entries = []
    for path in sorted(set(paths)):
        if path.name in exclude_names:
            continue
        if "__pycache__" in path.parts:
            continue

        content = path.read_text(encoding="utf-8")
        try:
            tree = ast.parse(content, filename=str(path))
        except Exception:  # noqa: S112
            continue

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith("test_"):
                func_doc = ast.get_docstring(node, clean=False)
                if func_doc:
                    scores = parse_test_eval_tags(func_doc)
                    if scores or "#test-eval:" in func_doc:
                        target = ""
                        test_type = ""
                        for line in func_doc.splitlines():
                            line_str = line.strip()
                            if line_str.startswith("Test target:"):
                                target = func_doc.split("Test target:", 1)[1].splitlines()[1].strip()
                            elif line_str.startswith("Test type:"):
                                test_type = func_doc.split("Test type:", 1)[1].splitlines()[1].strip()
                        entries.append(
                            TestQualityEntry(
                                file=f"{path.as_posix()} ({node.name})",
                                target=target or "unknown",
                                test_type=test_type or "unknown",
                                scores=scores,
                            ),
                        )
    return entries


@dataclass(frozen=True)
class TestStub:
    """A test function whose responsibility template still needs agent analysis."""

    file: str
    line: int
    function: str
    kind: str
    missing_template: bool
    unfilled_text: tuple[str, ...]
    unassessed_criteria: tuple[str, ...]

    @property
    def is_stub(self) -> bool:
        return self.missing_template or bool(self.unfilled_text) or bool(self.unassessed_criteria)


def _unfilled_template_fields(docstring: str) -> tuple[str, ...]:
    """Return template sections whose value is still a placeholder."""
    values: dict[str, str] = {}
    current: str | None = None
    for raw_line in docstring.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        field = next((item for item in TEMPLATE_FIELDS if line.startswith(f"{item}:")), None)
        if field is not None:
            current = field
            values.setdefault(field, "")
            continue
        if current is not None:
            values[current] = line
            current = None
    return tuple(field for field in TEMPLATE_FIELDS if values.get(field, "").startswith("<"))


def find_test_stubs(roots: list[Path], exclude_names: set[str] | None = None) -> list[TestStub]:
    """Find collected test functions whose template or scores still need analysis."""
    if exclude_names is None:
        exclude_names = {"__init__.py", "conftest.py"}

    paths: list[Path] = []
    for root in roots:
        if root.is_dir():
            paths.extend(root.rglob("*.py"))
        elif root.suffix == ".py":
            paths.append(root)

    stubs: list[TestStub] = []
    for path in sorted(set(paths)):
        if path.name in exclude_names or "__pycache__" in path.parts:
            continue
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except (OSError, SyntaxError, UnicodeDecodeError):
            continue

        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            if not node.name.startswith("test_"):
                continue
            doc = ast.get_docstring(node, clean=False)
            missing_template = doc is None or "Test target:" not in doc
            scores = parse_test_eval_tags(doc)
            stub = TestStub(
                file=path.as_posix(),
                line=node.lineno,
                function=node.name,
                kind="async function" if isinstance(node, ast.AsyncFunctionDef) else "function",
                missing_template=missing_template,
                unfilled_text=() if missing_template else _unfilled_template_fields(doc or ""),
                unassessed_criteria=tuple(c for c in TEST_SCORE_CRITERIA if c not in scores),
            )
            if stub.is_stub:
                stubs.append(stub)
    return stubs


def write_report(entries: list[TestQualityEntry]) -> None:
    """Write test quality report JSON."""
    TEST_REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    values = {crit: [entry.scores[crit] for entry in entries if crit in entry.scores] for crit in TEST_SCORE_CRITERIA}
    report_data = {
        "files": [asdict(e) for e in entries],
        "stats": {
            "total_entities": len(entries),
            "averages": {
                crit: sum(scores) / len(scores) if scores else None for crit, scores in values.items()
            },
            "scored_by_criterion": {crit: len(scores) for crit, scores in values.items()},
        },
    }
    TEST_REPORT_JSON.write_text(json.dumps(report_data, indent=2), encoding="utf-8")


def main() -> int:
    """Scan all test files and output a test quality report."""
    entries = collect_entries([Path("tests")])
    write_report(entries)

    print(f"Generated test quality report at {TEST_REPORT_JSON}")
    print("\nTest Quality Statistics:")
    print("--------------------------------------------------")
    print(f"Total documented test entities (modules/functions): {len(entries)}")
    if entries:
        for crit in TEST_SCORE_CRITERIA:
            values = [e.scores[crit] for e in entries if crit in e.scores]
            average_text = f"{sum(values) / len(values):.2f}/5.0" if values else "N/A"
            print(f"Average {crit.replace('_', ' '):<20}: {average_text} ({len(values)}/{len(entries)} scored)")
    print("--------------------------------------------------")

    return 0


if __name__ == "__main__":
    sys.exit(main())
