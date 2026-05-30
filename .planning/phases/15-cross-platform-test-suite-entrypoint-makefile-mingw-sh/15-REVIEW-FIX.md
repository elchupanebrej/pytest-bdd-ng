---
phase: 15-cross-platform-test-suite-entrypoint-makefile-mingw-sh
fixed_at: 2026-05-24T05:12:00Z
review_path: .planning/phases/15-cross-platform-test-suite-entrypoint-makefile-mingw-sh/15-REVIEW.md
iteration: 2
findings_in_scope: 8
fixed: 8
skipped: 0
status: all_fixed
---

# Phase 15: Code Review Fix Report

**Fixed at:** 2026-05-24
**Source review:** `.planning/phases/15-cross-platform-test-suite-entrypoint-makefile-mingw-sh/15-REVIEW.md`
**Iteration:** 2

## Summary

- Findings in scope: 8
- Fixed: 8
- Skipped: 0

## Fixed Issues

### CR-01: Windows native platform target bypasses PowerShell

**Files modified:** `Makefile`
**Applied fix:** `test-platform-native` now delegates to `test-platform-windows` on MinGW/MSYS/CYGWIN hosts. `test-all` also skips separate `test-platform-windows` execution on Windows hosts to avoid duplicate native Windows tox work.

### CR-02: Fail-fast validation misses macOS backend before work starts

**Files modified:** `Makefile`
**Applied fix:** `validate-test-all-backends FAIL_FAST=1` now fails before any subwork on non-macOS hosts when the full cross-platform set includes macOS tox. This preserves validation-before-work semantics.

### CR-03: Windows Docker backend lacks `uvx`

**Files modified:** `Makefile`
**Applied fix:** Windows Docker execution now installs `uv` inside `python:3.14-windowsservercore-ltsc2022` before invoking `uvx --with tox-uv tox`. `env-check-docker-windows` also probes the Windows container Python backend before work.

### CR-04: Option passthrough injection and quoting risk

**Files modified:** `Makefile`
**Applied fix:** `TEST_ALL_ARGS`, `TEST_NATIVE_ARGS`, `TEST_LINUX_ARGS`, `TEST_WINDOWS_ARGS`, `TEST_MACOS_ARGS`, and `REPORT_ARGS` are exported instead of re-quoted into recursive Make assignments. PowerShell and Docker branches read args from environment variables instead of interpolating raw Make variables into command strings.

### WR-01: Linux/macOS Windows backend policy not implementable

**Files modified:** `Makefile`, `DEVELOPMENT.rst`
**Applied fix:** Added `WINDOWS_TOX_BACKEND_COMMAND` as an explicit override for non-standard Windows tox backends. Documentation now states Linux/macOS Windows tox requires Windows Docker containers or a configured backend command.

### WR-02: Running Tests docs point full tox flow at `make test`

**Files modified:** `DEVELOPMENT.rst`
**Applied fix:** The Running Tests section now describes `make test` as the local feasible default suite and uses `make test-all` for the full tox-backed cross-platform/report flow.

### WR-03: Cross-platform prerequisites omit required backends

**Files modified:** `DEVELOPMENT.rst`
**Applied fix:** Windows prerequisites now include PowerShell, WSL2 with `uvx`, and Windows-container requirements. Linux/macOS prerequisites now mention Docker and `WINDOWS_TOX_BACKEND_COMMAND` or equivalent Windows backend.

### IN-01: Unused routing variables remain

**Files modified:** `Makefile`
**Applied fix:** Removed unused `NATIVE_TARGETS` and `DOCKER_TARGETS` assignments. `test-all` now uses explicit platform target orchestration.

## Verification

- `rtk make -n test-platform-windows TEST_WINDOWS_ARGS='-k windows_only'`
- `rtk make -n test-all TEST_NATIVE_ARGS='-k native_only' TEST_LINUX_ARGS='-k linux_only' TEST_WINDOWS_ARGS='-k windows_only' TEST_MACOS_ARGS='-k macos_only' FAIL_FAST=0 REPORT_MODE=skip`
- `rtk make -n test-all TEST_NATIVE_ARGS='-k native_only' TEST_LINUX_ARGS='-k linux_only' TEST_WINDOWS_ARGS='-k windows_only' TEST_MACOS_ARGS='-k macos_only' FAIL_FAST=1 REPORT_MODE=skip`
- `rtk powershell ...` static checks for review-fix evidence in `Makefile` and `DEVELOPMENT.rst`
- `rtk uv run pre-commit run --files Makefile DEVELOPMENT.rst`

All listed checks passed.

---

_Fixed: 2026-05-24T05:12:00Z_
_Fixer: Codex_
_Iteration: 2_
