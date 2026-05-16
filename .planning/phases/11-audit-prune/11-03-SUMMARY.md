---
phase: 11-audit-prune
plan: "03"
subsystem: code-architecture
tags: [module-split, package-refactor, monkeypatch-compatibility]

# Dependency graph
requires:
  - phase: 11-audit-prune
    provides: dead code removal from 11-01
provides:
  - message_capability_governance.py split into 5 focused modules
  - Backward-compatible re-exports for all public functions
  - python -m entry point preserved
affects: [future governance feature development, test monkeypatching]

# Tech tracking
tech-stack:
  added: []
  patterns: [package re-exports, runtime sys.modules lookup for monkeypatch compatibility, per-file ruff ignores for intentional late imports]

key-files:
  created:
    - src/pytest_bdd/script/message_capability_governance/__init__.py
    - src/pytest_bdd/script/message_capability_governance/__main__.py
    - src/pytest_bdd/script/message_capability_governance/schema.py
    - src/pytest_bdd/script/message_capability_governance/capabilities.py
    - src/pytest_bdd/script/message_capability_governance/decisions.py
    - src/pytest_bdd/script/message_capability_governance/cli.py
  modified:
    - pyproject.toml
  deleted:
    - src/pytest_bdd/script/message_capability_governance.py

key-decisions:
  - "Used runtime sys.modules lookup in discover_governance_schema_path and main() to preserve test monkeypatch compatibility"
  - "Added per-file ruff ignores for PLC0415/SLF001/TC003 on new package (lazy imports intentional for monkeypatch compatibility)"
  - "Re-exported generate_inventory, _repo_root, _candidate_repo_roots from __init__.py for test monkeypatch targets"

patterns-established:
  - "Monkeypatch-compatible package split: functions that tests monkeypatch are looked up via sys.modules at runtime, not imported at module load time"
  - "Per-file ruff ignores for intentional architectural choices (late imports, private member access within package)"

requirements-completed: [SIM-03]

# Metrics
duration: 45min
completed: 2026-05-16
---

# Phase 11 Plan 03: Split message_capability_governance.py Summary

Split 853-line monolithic script module into 5 focused sub-modules (~100-250L each) with full backward compatibility for imports and test monkeypatching.

## Performance

- **Duration:** 45min
- **Started:** 2026-05-16T22:48:00Z
- **Completed:** 2026-05-16T23:30:00Z
- **Tasks:** 1
- **Files modified:** 7 (5 created, 1 modified, 1 deleted)

## Accomplishments

- Split `message_capability_governance.py` (853L) into package with 5 modules: `schema.py`, `capabilities.py`, `decisions.py`, `cli.py`, `__main__.py`
- Preserved all public API imports from package path
- Preserved test monkeypatch compatibility via runtime sys.modules lookups
- All 34 governance tests pass (1 skipped)
- ruff F401/F811/ERA001 passes clean

## Task Commits

Each task was committed atomically:

1. **Task 1: Split message_capability_governance.py into package** - `8383a33c` (refactor)

**Plan metadata:** included in above commit (single-task plan)

## Files Created/Modified

- `src/pytest_bdd/script/message_capability_governance/__init__.py` - Re-exports all public functions
- `src/pytest_bdd/script/message_capability_governance/__main__.py` - python -m entry point
- `src/pytest_bdd/script/message_capability_governance/schema.py` - Schema loading, validation, repo root discovery
- `src/pytest_bdd/script/message_capability_governance/capabilities.py` - Capability loading, scope validation
- `src/pytest_bdd/script/message_capability_governance/decisions.py` - Decision loading, validation, baseline diff
- `src/pytest_bdd/script/message_capability_governance/cli.py` - CLI entry point (parse_args, main, _emit_text)
- `pyproject.toml` - Added per-file ignores for new package
- `src/pytest_bdd/script/message_capability_governance.py` - DELETED (original 853L file)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Missing `__main__.py` for `python -m` execution**
- **Found during:** Task 1 verification
- **Issue:** Plan required `python -m pytest_bdd.script.message_capability_governance` to work, but package without `__main__.py` cannot be executed directly
- **Fix:** Created `__main__.py` with `raise SystemExit(main())`
- **Files modified:** `src/pytest_bdd/script/message_capability_governance/__main__.py`
- **Commit:** `8383a33c`

**2. [Rule 2 - Missing critical functionality] Test monkeypatch compatibility**
- **Found during:** Task 1 test execution
- **Issue:** Tests monkeypatch `generate_inventory`, `_repo_root`, `_candidate_repo_roots` on the module namespace. After split, these functions lived in sub-modules and monkeypatching the package `__init__.py` didn't affect sub-module usage
- **Fix:** Added re-exports to `__init__.py`; used runtime `sys.modules` lookup in `discover_governance_schema_path()` and `main()` to resolve monkeypatched names at call time
- **Files modified:** `__init__.py`, `schema.py`, `cli.py`
- **Commit:** `8383a33c`

**3. [Rule 3 - Blocking] Missing `validate_capability_decision` import in cli.py**
- **Found during:** Task 1 pre-commit
- **Issue:** Removed import during split but function still called in `validate-decision` command handler
- **Fix:** Added local import inside the command handler
- **Files modified:** `cli.py`
- **Commit:** `8383a33c`

**4. [Rule 3 - Blocking] Ruff lint failures (PLC0415, SLF001, TC003)**
- **Found during:** Task 1 pre-commit
- **Issue:** Late imports (intentional for monkeypatch compatibility), private member access (package-internal), and Path import usage flagged by ruff
- **Fix:** Added per-file ignores in `pyproject.toml` matching existing pattern from `collector_batch.py`
- **Files modified:** `pyproject.toml`
- **Commit:** `8383a33c`

## Self-Check: PASSED

- All 5 new files exist and import correctly
- Original file deleted (Test-Path returns False)
- Script entry point works (`--help` exits 0)
- 34 governance tests pass, 1 skipped
- ruff F401/F811/ERA001 passes clean
- Commit `8383a33c` exists in git log
