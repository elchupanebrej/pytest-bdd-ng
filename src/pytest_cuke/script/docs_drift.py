"""Fail when the checked-in generated feature pages drift from their sources.

Regenerates the pages into a temporary directory, applies the same
trailing-whitespace normalization the pre-commit hook applies, then diffs the
result against the checked-in tree. The generator's own exit status is
unusable here: it compares trimmed checked-in files with untrimmed fresh
output and exits 1 on a synced tree by construction.

Usage:
    python -m pytest_cuke.script.docs_drift <features_dir> <docs_features_dir>
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

from pytest_cuke.script.bdd_tree_to_rst import convert

TRAILING_WHITESPACE = re.compile(r"[ \t]+$", re.MULTILINE)


def normalize_trailing_whitespace(root: Path) -> None:
    for path in root.rglob("*.rst"):
        path.write_text(TRAILING_WHITESPACE.sub("", path.read_text(encoding="utf-8")), encoding="utf-8")


def drift(committed: Path, generated: Path) -> list[str]:
    committed_paths = {path.relative_to(committed) for path in committed.rglob("*.rst")}
    generated_paths = {path.relative_to(generated) for path in generated.rglob("*.rst")}
    problems = [
        f"checked in but not generated: {path.as_posix()}" for path in sorted(committed_paths - generated_paths)
    ]
    problems += [
        f"generated but not checked in: {path.as_posix()}" for path in sorted(generated_paths - committed_paths)
    ]
    problems += [
        f"generated page differs from its source: {path.as_posix()}"
        for path in sorted(committed_paths & generated_paths)
        if (committed / path).read_bytes() != (generated / path).read_bytes()
    ]
    return problems


def check(features: Path, docs: Path) -> list[str]:
    with TemporaryDirectory() as temp_dirname:
        generated = Path(temp_dirname)
        convert(features.resolve(), docs.resolve(), generated)
        normalize_trailing_whitespace(generated)
        return drift(docs.resolve(), generated)


def main(argv: list[str]) -> int:
    if len(argv) != 3:
        print(f"usage: {argv[0]} <features_dir> <docs_features_dir>", file=sys.stderr)
        return 2
    features, docs = Path(argv[1]), Path(argv[2])
    if problems := check(features, docs):
        print("Generated feature pages drift from their sources:")
        print("\n".join(f"  {problem}" for problem in problems))
        print("\nRegenerate with: python src/pytest_cuke/script/bdd_tree_to_rst.py features docs/features")
        return 1
    print(f"{docs.as_posix()} matches a fresh generation from {features.as_posix()}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
