---
phase: 15-cross-platform-test-suite-entrypoint-makefile-mingw-sh
fixed_at: 2026-05-21T00:00:00Z
review_path: .planning/phases/15-cross-platform-test-suite-entrypoint-makefile-mingw-sh/15-REVIEW.md
iteration: 1
findings_in_scope: 7
fixed: 7
skipped: 0
status: all_fixed
---

# Phase 15: Code Review Fix Report

**Fixed at:** 2026-05-21
**Source review:** .planning/phases/15-cross-platform-test-suite-entrypoint-makefile-mingw-sh/15-REVIEW.md
**Iteration:** 1

**Summary:**
- Findings in scope (critical + warning): 7
- Fixed: 7
- Skipped: 0

## Fixed Issues

### CR-01: Hardcoded short DOS paths for SHELL and Docker PATH

**Files modified:** `Makefile`
**Commit:** `cfc0b05b`
**Applied fix:** Removed the entire MSYS2/MINGW/CYGWIN block (lines 14-17) that hardcoded `C:/PROGRA~1/Git/bin/sh.exe` and `C:/PROGRA~1/Docker/Docker/resources/bin`. MSYS2/Git Bash already provides the correct SHELL. Docker path discovery is unnecessary — Docker should be on PATH, and `env-check-docker` validates availability with a friendly error message.

### CR-02: test-external regressed from non-fatal to mandatory in test-all

**Files modified:** `Makefile`
**Commit:** `1140b481`
**Applied fix:** Moved `test-external` from NATIVE_TARGETS to DOCKER_TARGETS for all three platforms (Linux, Darwin, MINGW/MSYS/CYGWIN). Docker targets are invoked with `@-` prefix in `test-all`, making Docker-unavailable failures non-fatal. Restores the original intent from the pre-Phase-15 Makefile.

### WR-01: env-check-windows uses bare python instead of uv run python

**Files modified:** `Makefile`
**Commit:** `860c8d3b` (combined with WR-05)
**Applied fix:** Changed `python -c` to `uv run python -c` in the env-check-windows else branch. Consistent with all other targets using `$(PYTEST)` / `uv run python`.

### WR-02: local-pr-gate depends on rg without availability check

**Files modified:** `Makefile`
**Commit:** `8101eae5`
**Applied fix:** Added `command -v rg` guard as the first recipe line in `local-pr-gate`. If `rg` is missing, a clear error message with install link is shown and the gate exits. Prevents false negatives and misleading errors from failed rg invocations.

### WR-03: DEVELOPMENT.rst references non-existent make test-docker target

**Files modified:** `DEVELOPMENT.rst`
**Commit:** `99819135` (combined with WR-04)
**Applied fix:** Replaced `make test-docker` with `make test-docker-linux` and `make test-docker-windows` under a new "Docker-backed tests (split by platform)" subsection. Matches the actual post-Phase-15 target names.

### WR-04: DEVELOPMENT.rst reports wrong output extension .html for render-tox-reports

**Files modified:** `DEVELOPMENT.rst`
**Commit:** `99819135` (combined with WR-03)
**Applied fix:** Changed output extension from `.html` to `.json` and description from "HTML reports" to "JSON reports" in the Running Tests section. The Makefile renders Cucumber JSON via `--cucumber-json`, not HTML.

### WR-05: env-check-windows lacks env-check prerequisite

**Files modified:** `Makefile`
**Commit:** `860c8d3b` (combined with WR-01)
**Applied fix:** Added `env-check` as a prerequisite to `env-check-windows`. Ensures uv/Python availability is validated before attempting to run `uv run python`, providing a friendly error message instead of a cryptic shell error.

## Deferred (Info-level, out of scope)

These Info findings were not in the `critical_warning` fix scope:

- **IN-01** (NATIVE_TARGETS code duplication): Consolidation deferred — a refactoring risk that should go through a separate change.
- **IN-02** (TOX_HTML_REPORT_DIR misleading name): Variable rename requires updating 6 references across the file — deferred to avoid scope creep.
- **IN-03** (check-shell no-op placeholder): Needs design decision on whether to remove or document — deferred.

---

_Fixed: 2026-05-21T00:00:00Z_
_Fixer: the agent (gsd-code-fixer)_
_Iteration: 1_
