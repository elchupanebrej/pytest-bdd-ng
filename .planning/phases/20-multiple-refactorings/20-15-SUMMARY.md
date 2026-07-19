# Plan 20-15 Summary: INIT-01 Package Hygiene

**Status:** PARTIAL — Tasks 1 and 5 complete, Tasks 2-4 remain.

## What was done

### Task 1: Create init_rules.py (BLQ1401/BLQ1402)
- Created `src/pytest_bdd/_ruff/rules/init_rules.py` (~150 lines)
- BLQ1401: detects __init__.py files with re-exports lacking classification comment
- BLQ1402: detects __init__.py files with re-exports missing __all__
- Exempt: `# init: no-check` files
- Wired pre-commit hook in `.pre-commit-config.yaml`
- **Currently detects 22 violations** in un-annotated __init__.py files

### Task 5: Create layout_rules.py (BLQ1501/BLQ1502/BLQ1503)
- Created `src/pytest_bdd/_ruff/rules/layout_rules.py` (~130 lines)
- BLQ1501: detects duplicate .ruff/ directory
- BLQ1502: detects rule files outside _ruff/rules/
- BLQ1503: detects directories named .ruff
- Wired pre-commit hook
- **Currently detects 9 violations** (BLQ1501 for .ruff/, BLQ1502 false positives from scripts)

### Remaining
| Task | Description | Notes |
|------|-------------|-------|
| 2 | Audit 48 __init__.py files + add classification comments | 22 violations currently detected |
| 3 | Reorganize ruff rules in pyproject.toml + Makefile targets | select/per-file-ignores reorg |
| 4 | Merge .ruff/ wrapper into canonical _ruff/ | Delete wrappers, update configs |

## Commits
1. `feat(20-15): add init_rules.py (BLQ1401/2) and layout_rules.py (BLQ1501-3) + pre-commit hooks`
