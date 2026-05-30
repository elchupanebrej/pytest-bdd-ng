---
phase: 15-cross-platform-test-suite-entrypoint-makefile-mingw-sh
reviewed: 2026-05-24T04:48:34Z
depth: standard
files_reviewed: 2
files_reviewed_list:
  - Makefile
  - DEVELOPMENT.rst
findings:
  critical: 4
  warning: 3
  info: 1
  total: 8
status: issues_found
---

# Phase 15: Code Review Report

**Reviewed:** 2026-05-24T04:48:34Z
**Depth:** standard
**Files Reviewed:** 2
**Status:** issues_found

## Summary

Reviewed `Makefile` and `DEVELOPMENT.rst` against Phase 15 cross-platform tox orchestration requirements. Current implementation has blocking portability and correctness defects in Windows native routing, fail-fast validation ordering, Windows Docker execution, and shell argument interpolation. Docs also drift from Makefile behavior.

## Narrative Findings (AI reviewer)

## Critical Issues

### CR-01: BLOCKER: Windows native platform target bypasses PowerShell

**File:** `Makefile:113`
**Issue:** `test-platform-native` always runs `$(TOX)` directly in the active Make shell. On Windows/Git Bash, `TOX_NATIVE_ENVS` resolves to Windows tox envs, so `make test-all` runs Windows native tox under Git Bash before `test-platform-windows` later runs the same Windows envs through PowerShell. This violates Phase 15 requirement that native Windows tox launched from Git Bash must run through PowerShell, and it duplicates Windows platform work in full runs.
**Fix:**
```make
test-platform-native:
	@if printf '%s\n' "$(UNAME_S)" | grep -Eq '^(MINGW|MSYS|CYGWIN)'; then \
		$(MAKE_COMMAND) --no-print-directory test-platform-windows TEST_ALL_ARGS='$(TEST_ALL_ARGS)' TEST_WINDOWS_ARGS='$(TEST_NATIVE_ARGS)'; \
	else \
		$(MAKE_COMMAND) --no-print-directory env-check-tox; \
		$(TOX) run -e $(TOX_NATIVE_ENVS) -- $(TEST_ALL_ARGS) $(TEST_NATIVE_ARGS); \
	fi
```
Then avoid running duplicate Windows scope from `test-all` on MinGW, or make `test-platform-windows` the native Windows target and remove duplicate native Windows execution.

### CR-02: BLOCKER: Fail-fast validation does not validate macOS backend before work starts

**File:** `Makefile:258`
**Issue:** `validate-test-all-backends` checks PowerShell/WSL2 on MinGW, Windows Docker on Linux, and Linux/Windows Docker on macOS. It never validates that `test-platform-macos` can run on non-macOS hosts. With `FAIL_FAST=1`, `test-all` starts native/Linux/Windows work first, then fails at `test-platform-macos` on Windows or Linux. This breaks "validation before work" and fail-fast semantics.
**Fix:**
```make
validate-test-all-backends: env-check-tox
	@if [ "$(FAIL_FAST)" = "1" ]; then \
		if [ "$(UNAME_S)" != "Darwin" ]; then \
			echo "ERROR: macOS tox backend requires macOS host."; exit 1; \
		fi; \
		... existing backend checks ... \
	fi
```
Better: define selected platform scopes per host/mode, validate only selected scopes, and make `test-all` execute that same selected list.

### CR-03: BLOCKER: Windows Docker tox backend cannot run because container lacks `uvx`

**File:** `Makefile:145`
**Issue:** Windows Docker branch runs `$(TOX)`, defaulting to `uvx --with tox-uv tox`, inside `python:3.14-windowsservercore-ltsc2022`. Unlike the Linux Docker branch, it never installs `uv`, so `uvx` is unavailable in the container. `env-check-docker-windows` only checks Docker daemon OS, not tool availability inside the container, so validation can pass while execution fails immediately.
**Fix:**
```make
docker run --rm -v "$$PWD":C:/work -w C:/work python:3.14-windowsservercore-ltsc2022 \
	powershell -NoProfile -Command "python -m pip install uv; uvx --with tox-uv tox run -e $(TOX_WINDOWS_ENVS) -- $(TEST_ALL_ARGS) $(TEST_WINDOWS_ARGS)"
```
Also add a validation probe that executes `python -m pip --version` and `uvx --version` or installs `uv` in the same Windows container path used by the test target.

### CR-04: BLOCKER: Option passthrough allows shell/PowerShell injection and breaks valid pytest expressions

**File:** `Makefile:86`
**Issue:** User-facing argument variables (`TEST_ALL_ARGS`, `TEST_*_ARGS`, `REPORT_ARGS`) are interpolated directly into recursive Make shell commands and PowerShell command strings. A value containing a single quote breaks the recursive assignment (`TEST_WINDOWS_ARGS='-k a'b'`), while shell metacharacters can execute unintended commands. The PowerShell branch also embeds arguments in a double-quoted `-Command` string, so `;`, `&`, backticks, and quotes are interpreted by PowerShell instead of passed as tox args.
**Fix:**
```make
export TEST_ALL_ARGS TEST_NATIVE_ARGS TEST_LINUX_ARGS TEST_WINDOWS_ARGS TEST_MACOS_ARGS

test-all: validate-test-all-backends
	@$(MAKE_COMMAND) --no-print-directory test-platform-native

test-platform-native: env-check-tox
	$(TOX) run -e $(TOX_NATIVE_ENVS) -- "$$TEST_ALL_ARGS" "$$TEST_NATIVE_ARGS"
```
For PowerShell, pass values through environment variables and use `--%` or `Start-Process`/argument arrays rather than string-building `-Command`.

## Warnings

### WR-01: WARNING: Linux/macOS Windows backend policy is documented but not actually implementable

**File:** `Makefile:255`
**Issue:** `env-check-docker-windows` requires `docker version --format '{{.Server.Os}}'` to report `windows`. Normal Linux and macOS Docker daemons report `linux`; Docker Desktop for macOS does not run Windows containers. The docs say Linux/macOS use "Windows Docker or equivalent VM-like backend", but there is no equivalent backend path. `test-platform-windows` therefore cannot satisfy documented Linux/macOS routing on ordinary hosts.
**Fix:** Either implement explicit VM/remote backend variables, for example `WINDOWS_TOX_BACKEND_COMMAND`, or document and enforce that Windows platform tox is only supported from Windows hosts.

### WR-02: WARNING: Documentation tells users `make test` runs full tox report flow

**File:** `DEVELOPMENT.rst:528`
**Issue:** The "Running Tests" section says "To run the full test suite and render one HTML report per pytest-based tox environment" and shows `make test`. In the Makefile, `make test` runs direct pytest on the local feasible selector, while `make test-all` is the tox-backed full pipeline. This sends users to the wrong entrypoint.
**Fix:** Change that block to `make test-all`, and describe `make test` as local feasible pytest-only smoke/default suite.

### WR-03: WARNING: Cross-platform prerequisites omit required backends

**File:** `DEVELOPMENT.rst:36`
**Issue:** Windows row lists Git for Windows and Docker Desktop only, but `make test-all` also requires PowerShell and WSL2 for Linux tox from Windows. Linux/macOS rows mark Docker optional, but the documented full cross-platform target needs Docker or a Windows backend for non-native coverage. Setup docs are insufficient for reproducing the Makefile paths.
**Fix:** Add PowerShell and WSL2 to Windows prerequisites, clarify Docker/Windows-container requirements, and distinguish `make test` prerequisites from `make test-all` prerequisites.

## Info

### IN-01: Unused routing variables remain after `test-all` rewrite

**File:** `Makefile:23`
**Issue:** `NATIVE_TARGETS` and `DOCKER_TARGETS` are assigned for each OS but are no longer referenced by any recipe. They now create false confidence that platform routing table drives execution.
**Fix:** Remove these variables or wire `test-all` to use them consistently.

---

_Reviewed: 2026-05-24T04:48:34Z_
_Reviewer: the agent (gsd-code-reviewer)_
_Depth: standard_
