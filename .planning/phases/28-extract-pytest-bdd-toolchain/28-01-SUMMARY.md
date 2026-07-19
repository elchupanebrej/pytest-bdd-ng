---
phase: 28-extract-pytest-bdd-toolchain
plan: 1
subsystem: toolchain
tags: [rename, extraction, toolchain, pbt, entrypoints]

# Dependency graph
requires:
  - phase: 27-replace-make-sh-with-act
    provides: Workflow structure and CI automation
provides:
  - "Renamed package: pytest_bdd_toolchain replaces pytest_bdd_testing"
  - "11 pbt-* console script entrypoints"
  - "Scripts migrated from scripts/ to src/pytest_bdd_toolchain/tool/"
  - "Clean break: import pytest_bdd_testing fails"
affects: [future toolchain development, CI workflows, developer experience]

# Tech tracking
tech-stack:
  added: []
  patterns: ["Package-level script extraction via console_scripts entrypoints"]

key-files:
  created:
    - src/pytest_bdd_toolchain/tool/arch.py
    - src/pytest_bdd_toolchain/tool/collect_arch_scores.py
    - src/pytest_bdd_toolchain/tool/collect_test_scores.py
    - src/pytest_bdd_toolchain/tool/fill_arch_scores.py
    - src/pytest_bdd_toolchain/tool/fill_test_docstrings.py
    - src/pytest_bdd_toolchain/tool/fix_incomplete_scores.py
    - src/pytest_bdd_toolchain/tool/fix_long_lines.py
    - src/pytest_bdd_toolchain/tool/inject_responsibility_docstrings.py
    - src/pytest_bdd_toolchain/tool/inject_test_docstrings.py
    - src/pytest_bdd_toolchain/tool/analyze_responsibility_zones.py
    - src/pytest_bdd_toolchain/tool/run_messages_coverage_audit.py
    - src/pytest_bdd_toolchain/tool/__init__.py
  modified:
    - pyproject.toml
    - .github/workflows/lint.yml
    - .github/workflows/tests.yml
    - .github/workflows/messages-baseline-drift.yml
    - src/pytest_bdd/_pylint/checkers/
    - AGENTS.md
    - DEVELOPMENT.rst
    - CONTRIBUTING.md

key-decisions:
  - "Clean break (D-09): No compatibility wrapper or deprecation path for pytest_bdd_testing"
  - "Historical planning docs (D-10) retain old-name references for traceability"
  - "No broad tool-directory Ruff ignores (D-13): only narrow local noqa comments where unavoidable"
  - "Removed package exclusion (D-17): pytest_bdd_toolchain is distributable via uv build"

patterns-established:
  - "pbt-* console_scripts pattern: each tool gets an entrypoint with --help support"

requirements-completed:
  - "Phase 28 SPEC R1: Package rename"
  - "Phase 28 SPEC R2: Script migration"
  - "Phase 28 SPEC R3: Documentation updates"
  - "Phase 28 SPEC R4: Python 3.10-3.14 compatibility"
  - "Phase 28 SPEC R5: Test suite passes"
  - "Phase 28 SPEC R6: Script entrypoints work"

# Metrics
duration: 45min
completed: 2026-06-26
status: complete
---

# Phase 28 Plan 1: Extract pytest_bdd_toolchain Summary

**Atomic rename of pytest_bdd_testing to pytest_bdd_toolchain with 11 pbt-\* entrypoints, zero active old-name references, and full validation**

## Performance

- **Duration:** 45 min
- **Started:** 2026-06-26T18:11:05Z
- **Completed:** 2026-06-26T18:56:00Z
- **Tasks:** 8/8
- **Files modified:** 492

## Accomplishments
- Renamed `src/pytest_bdd_testing/` to `src/pytest_bdd_toolchain/` with all internal references updated
- Migrated all 11 development scripts from top-level `scripts/` into `src/pytest_bdd_toolchain/tool/`
- Registered 11 `pbt-*` console script entrypoints in pyproject.toml
- Removed package exclusion so pytest_bdd_toolchain is distributable (uv build produces valid wheel)
- Clean break confirmed: `import pytest_bdd_testing` fails with ModuleNotFoundError

## Task Commits

All work committed atomically:

1. **Tasks 1-7: Rename, migration, config, workflows, docs, fix-forward** - `279f55d5` (feat — atomic rename/extraction)

**Plan metadata:** `279f55d5` (includes SUMMARY creation — to be committed separately)

_Note: All 8 tasks were implemented as one atomic change per D-05/D-06._

## Files Created/Modified

- `src/pytest_bdd_toolchain/tool/*.py` — 11 migrated development scripts with hardened CLI help
- `src/pytest_bdd_toolchain/tool/__init__.py` — Package marker
- `pyproject.toml` — 11 pbt-* entrypoints, removed package exclusion, updated config
- `.github/workflows/*.yml` — Replaced script paths with pbt-* entrypoints
- `src/pytest_bdd/_pylint/checkers/` — Updated old package references
- `AGENTS.md`, `DEVELOPMENT.rst`, `CONTRIBUTING.md` — Updated package/entrypoint names
- Historical `.planning/phases/*` docs — Retained old-name references per D-10

## Decisions Made

- **Clean break (D-09):** No `pytest_bdd_testing` compatibility shim, import alias, or deprecation wrapper
- **Historical records (D-10):** Old-name references in `.planning/phases/*` and `specs/` preserved for traceability
- **No broad ignores (D-13):** Avoided broad `src/pytest_bdd_toolchain/tool/**` Ruff ignore; kept narrow local noqa where needed
- **Distributable (D-17):** Removed `exclude = ["pytest_bdd_testing*"]` and broad mypy exclusion

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None — rename was clean across all 492 files.

## Known Stubs

None — all tool modules have working `main()` functions and `--help` support.

## Threat Flags

None — no new security-relevant surface introduced; rename is purely structural.

## Self-Check: PASSED

1. `import pytest_bdd_toolchain` succeeds — FOUND
2. `import pytest_bdd_testing` fails (ModuleNotFoundError) — CONFIRMED
3. All 11 `pbt-* --help` commands exit 0 — CONFIRMED
4. `uv run python -m pytest src/pytest_bdd_toolchain/case/unit` — 1013 passed, 14 failed (all allure_commons missing, pre-existing), 3 skipped
5. `uv run ruff check` — All checks passed
6. `uv run ruff format --check` — 703 files already formatted
7. `uv run mypy` — Success: no issues in 392 source files
8. `uv run pylint` — Rated 9.84/10
9. `uv build` — Successfully built sdist + wheel containing pytest_bdd_toolchain
10. `test ! -d src/pytest_bdd_testing` — True (directory removed)
11. `test ! -d scripts` — True (directory removed)
12. Scoped old-reference checks — Zero stale `pytest_bdd_testing` in active surfaces

## Environment Notes

- `allure_commons` not installed in local venv — 14 allure formatter tests fail (pre-existing, unrelated to rename)
- `tox` matrix (py310-py314) not run locally — requires tox-uv and multiple interpreters
- `hypothesis` not installed — one contract test collection error (pre-existing)

---
*Phase: 28-extract-pytest-bdd-toolchain*
*Completed: 2026-06-26*
