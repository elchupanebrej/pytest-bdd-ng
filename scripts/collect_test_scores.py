"""
Collect test quality evaluation scores for all pytest-bdd test entities.

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


@dataclass(frozen=True)
class TestQualityEntry:
    file: str
    target: str
    test_type: str
    scores: dict[str, int]

    @property
    def average(self) -> float:
        values = [v for v in self.scores.values() if v > 0]
        if not values:
            return 0.0
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
            if isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
                func_doc = ast.get_docstring(node, clean=False)
                if func_doc:
                    scores = parse_test_eval_tags(func_doc)
                    if scores:
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


def write_report(entries: list[TestQualityEntry]) -> None:
    """Write test quality report JSON."""
    TEST_REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    report_data = {
        "files": [asdict(e) for e in entries],
        "stats": {
            "total_entities": len(entries),
            "averages": {
                crit: sum(e.scores.get(crit, 0) for e in entries) / len(entries) if entries else 0.0
                for crit in TEST_SCORE_CRITERIA
            },
        },
    }
    TEST_REPORT_JSON.write_text(json.dumps(report_data, indent=2), encoding="utf-8")


def main() -> int:
    """Scan all test files and output a test quality report."""
    entries = collect_entries([Path("src/pytest_bdd_testing/cases"), Path("tests")])
    write_report(entries)

    print(f"Generated test quality report at {TEST_REPORT_JSON}")
    print("\nTest Quality Statistics:")
    print("--------------------------------------------------")
    print(f"Total documented test entities (modules/functions): {len(entries)}")
    if entries:
        for crit in TEST_SCORE_CRITERIA:
            avg = sum(e.scores.get(crit, 0) for e in entries) / len(entries)
            print(f"Average {crit.replace('_', ' '):<20}: {avg:.2f}/5.0")
    print("--------------------------------------------------")

    return 0


if __name__ == "__main__":
    sys.exit(main())
