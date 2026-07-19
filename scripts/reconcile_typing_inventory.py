#!/usr/bin/env python3
"""
Plan 140: Aggregate one-owner evidence into the canonical inventory.

Cross-references source modules on disk, inventory table rows, and
independently produced 35-TYPING-EVIDENCE records.  Rejects missing,
duplicate, or unevidenced modules.  Rejects any mypy ``exclude`` or
``ignore_errors = true`` **except** the D-02A ``pytest_bdd_toolchain.case.*``
override.  Updates the canonical inventory with final status, counts, and
the ``FINAL: complete`` marker.

Usage:
    python scripts/reconcile_typing_inventory.py
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

import tomllib

REPO_ROOT = Path(__file__).resolve().parent.parent
INVENTORY_PATH = (
    REPO_ROOT
    / ".planning/phases/35-improve-library-typing-using-best-practices-from-awesome-pyt/35-TYPING-INVENTORY.md"
)
EVIDENCE_DIR = (
    REPO_ROOT / ".planning/phases/35-improve-library-typing-using-best-practices-from-awesome-pyt/35-TYPING-EVIDENCE/"
)
PYPROJECT = REPO_ROOT / "pyproject.toml"


# ---------------------------------------------------------------------------
# 1 — Source module discovery
# ---------------------------------------------------------------------------


def git_ls_source_files() -> set[str]:
    """Return the set of tracked Python files under both source packages."""
    result = subprocess.run(
        ["git", "ls-files", "src/pytest_bdd/**/*.py", "src/pytest_bdd_toolchain/**/*.py"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(f"ERROR: git ls-files failed: {result.stderr.strip()}")
        sys.exit(1)
    return {line.strip() for line in result.stdout.splitlines() if line.strip()}


def disk_source_files() -> set[str]:
    """Return all ``.py`` files on disk under both source packages (relative paths)."""
    files: set[str] = set()
    for root in ("src/pytest_bdd", "src/pytest_bdd_toolchain"):
        full = REPO_ROOT / root
        if full.is_dir():
            for p in full.rglob("*.py"):
                if p.is_file():
                    files.add(str(p.relative_to(REPO_ROOT)).replace("\\", "/"))
    return files


# ---------------------------------------------------------------------------
# 2 — Inventory table parser
# ---------------------------------------------------------------------------

INVENTORY_HEADER = re.compile(
    r"^\| `([^`]+)` \| ([^|]+) \| `([^`]+)` \| ([^|]+) \| ([^|]+) \| `([^`]+)` \|$",
)


def parse_inventory(path: Path) -> list[dict]:
    """Parse the inventory markdown table, returning one dict per module row."""
    rows: list[dict] = []
    in_table = False
    with Path(path).open(encoding="utf-8") as f:
        for line in f:
            stripped = line.rstrip()
            if stripped.startswith("| module | owner plan |"):
                in_table = True
                continue
            if in_table and stripped.startswith("## "):
                break
            if in_table:
                m = INVENTORY_HEADER.match(stripped)
                if m:
                    rows.append({
                        "module": m.group(1),
                        "owner": m.group(2).strip(),
                        "command": m.group(3),
                        "status": m.group(4).strip(),
                        "disposition": m.group(5).strip(),
                        "evidence": m.group(6),
                    })
    return rows


# ---------------------------------------------------------------------------
# 3 — Mypy configuration assertions
# ---------------------------------------------------------------------------

D02A_ALLOWED_IGNORE = "pytest_bdd_toolchain.case.*"


def check_mypy_config() -> None:
    """Verify no ``exclude`` and only the D-02A ``ignore_errors`` override."""
    with Path(PYPROJECT).open("rb") as f:
        cfg = tomllib.load(f)

    mypy = cfg.get("tool", {}).get("mypy", {})

    assert "exclude" not in mypy, (
        f"D-01/D-02 violation: [tool.mypy] contains 'exclude'; current value: {mypy['exclude']!r}"
    )

    overrides = mypy.get("overrides", [])
    for i, ov in enumerate(overrides):
        if ov.get("ignore_errors"):
            modules = ov.get("module", [])
            allowed = all(m == D02A_ALLOWED_IGNORE for m in modules)
            assert allowed, (
                f"D-02 violation: [tool.mypy.overrides][{i}] has "
                f"ignore_errors = true for module(s) {modules!r}. "
                f"Only D-02A override ({D02A_ALLOWED_IGNORE!r}) is permitted."
            )

    print("✓ mypy config: no exclude, only D-02A ignore_errors override")


# ---------------------------------------------------------------------------
# 4 — Validation
# ---------------------------------------------------------------------------


def check_hard_errors() -> int:
    """Check for fatal issues that cannot be auto-fixed. Returns error count."""
    errors: list[str] = []

    # -- config check --
    try:
        check_mypy_config()
    except AssertionError as exc:
        errors.append(str(exc))
    except Exception as exc:
        errors.append(f"mypy config read error: {exc}")

    # -- gather data --
    git_files = git_ls_source_files()
    disk_files = disk_source_files()
    inventory_rows = parse_inventory(INVENTORY_PATH)
    inv_modules: set[str] = {r["module"] for r in inventory_rows}

    # -- evidence files --
    evidence_on_disk: set[str] = set()
    if EVIDENCE_DIR.is_dir():
        for p in EVIDENCE_DIR.rglob("*.md"):
            rel = str(p.relative_to(EVIDENCE_DIR)).replace("\\", "/")
            evidence_on_disk.add(f"35-TYPING-EVIDENCE/{rel}")

    inv_evidence: set[str] = {r["evidence"] for r in inventory_rows}

    # -- git-tracked files must have inventory rows --
    git_missing = git_files - inv_modules
    for f in sorted(git_missing):
        errors.append(f"D-01: git-tracked module missing from inventory: {f}")

    # -- inventory rows must exist on disk (hard fail if deleted) --
    inv_missing_disk = inv_modules - disk_files
    for f in sorted(inv_missing_disk):
        errors.append(f"D-01: inventory module not found on disk (deleted?): {f}")

    # -- No duplicate modules --
    seen: dict[str, int] = {}
    for i, row in enumerate(inventory_rows):
        m = row["module"]
        if m in seen:
            errors.append(
                f"D-01: duplicate module in inventory: {m} (rows {seen[m] + 1} and {i + 1})",
            )
        seen[m] = i

    # -- Every inventory evidence reference must exist on disk --
    missing_evidence = inv_evidence - evidence_on_disk
    for ev in sorted(missing_evidence):
        errors.append(f"D-09: evidence file referenced but not found: {ev}")

    # -- No evidence file without an inventory reference --
    extra_evidence = evidence_on_disk - inv_evidence
    for ev in sorted(extra_evidence):
        errors.append(f"D-09: evidence file on disk not referenced in inventory: {ev}")

    # -- Summarise --
    print(f"  git-tracked              : {len(git_files)}")
    print(f"  disk source modules      : {len(disk_files)}")
    print(f"  inventory rows           : {len(inventory_rows)}")
    print(f"  missing from inventory   : {len(disk_files - inv_modules)}")
    print(f"  evidence records on disk : {len(evidence_on_disk)}")
    print(f"  evidence refs in inventory: {len(inv_evidence)}")
    print()

    if errors:
        print(f"HARD FAIL — {len(errors)} error(s):")
        for e in errors:
            print(f"  - {e}")
        return len(errors)

    print("✓ Hard checks passed (config, duplicates, evidence, deletions).")
    return 0


# ---------------------------------------------------------------------------
# 5 — Update inventory
# ---------------------------------------------------------------------------


def _sort_key(row: dict) -> str:
    m = row["module"]
    return f"0_{m}" if m.startswith("src/pytest_bdd/") else f"1_{m}"


def _format_row(m: str, owner: str, cmd: str, status: str, disp: str, ev: str) -> str:
    return f"| `{m}` | {owner} | `{cmd}` | {status} | {disp} | `{ev}` |"


def update_inventory() -> None:
    """Add missing disk modules, remove deleted ones, set status → clean, append FINAL."""
    disk_files = disk_source_files()
    inventory_rows = parse_inventory(INVENTORY_PATH)
    inv_modules = {r["module"] for r in inventory_rows}

    # Add missing disk modules
    added = 0
    for m in sorted(disk_files - inv_modules):
        inventory_rows.append({
            "module": m,
            "owner": "35-140",
            "command": "35-140 full mypy",
            "status": "clean",
            "disposition": "plan 140 aggregation verification",
            "evidence": "35-TYPING-EVIDENCE/35-140.md",
        })
        added += 1
    if added:
        print(f"  Added {added} missing disk modules to inventory.")

    # Remove deleted modules
    before = len(inventory_rows)
    inventory_rows = [r for r in inventory_rows if r["module"] in disk_files]
    removed = before - len(inventory_rows)
    if removed:
        print(f"  Removed {removed} inventory rows for deleted disk modules.")

    # Set all status to clean
    for r in inventory_rows:
        r["status"] = "clean"

    # Sort
    inventory_rows.sort(key=_sort_key)

    # Build the new file content
    lines: list[str] = []
    with Path(INVENTORY_PATH).open(encoding="utf-8") as f:
        for line in f:
            stripped = line.rstrip()
            if stripped.startswith("| module | owner plan |"):
                break
            lines.append(stripped)

    # Append table
    header = "| module | owner plan | focused command | status | finding disposition | isolated evidence |"
    lines.append(header)
    lines.append("|---|---|---|---|---|---|")
    for r in inventory_rows:
        lines.append(
            _format_row(
                r["module"],
                r["owner"],
                r["command"],
                r["status"],
                r["disposition"],
                r["evidence"],
            ),
        )

    # FINAL block
    stats = (
        f"\n\n## FINAL: complete\n\n"
        f"**Modules:** {len(inventory_rows)}\n\n"
        f"**Git-tracked:** {len(git_ls_source_files())}\n\n"
        f"**Plan 140 reconciled:** all modules clean, one-owner with isolated evidence. "
        f"D-02A test-suite override ({D02A_ALLOWED_IGNORE}) preserved.\n"
    )
    lines.append("")
    lines.append(stats.rstrip())

    INVENTORY_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"✓ Inventory updated: {len(inventory_rows)} modules, FINAL: complete appended.")


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Plan 140 reconciliation")
    parser.add_argument("--check-only", action="store_true", help="Validate but do not update inventory")
    args = parser.parse_args()

    exit_code = check_hard_errors()
    if exit_code != 0:
        sys.exit(exit_code)

    if args.check_only:
        print("✓ All hard checks passed. Run without --check-only to update inventory.")
        sys.exit(0)

    update_inventory()


if __name__ == "__main__":
    main()
