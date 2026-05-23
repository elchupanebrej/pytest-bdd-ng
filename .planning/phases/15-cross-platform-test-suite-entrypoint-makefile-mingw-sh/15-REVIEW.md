---
phase: 15-cross-platform-test-suite-entrypoint-makefile-mingw-sh
reviewed: 2026-05-21T00:00:00Z
depth: standard
files_reviewed: 2
files_reviewed_list:
  - Makefile
  - DEVELOPMENT.rst
findings:
  critical: 2
  warning: 5
  info: 3
  total: 10
status: issues_found
---

# Phase 15: Code Review Report

**Reviewed:** 2026-05-21T00:00:00Z
**Depth:** standard
**Files Reviewed:** 2
**Status:** issues_found

## Summary

Reviewed the two deliverables for Phase 15 (Cross-platform Makefile entrypoint): the project root `Makefile` and `DEVELOPMENT.rst` documentation. The phase added OS detection, unsupported-shell guard, Windows SHELL/PATH fix, Docker target split, platform routing, and cross-platform shell syntax fixes.

Two **BLOCKER** issues found: hardcoded short DOS paths that will fail on non-standard Windows installations, and a regression where `test-external` changed from non-fatal to mandatory in `test-all`, breaking macOS users without Docker. Five **WARNING** issues in environment check consistency, missing tool dependency validation, and documentation inaccuracies. Three **INFO** items on code duplication and naming.

## Critical Issues

### CR-01: Hardcoded short DOS paths for SHELL and Docker PATH

**File:** `Makefile:15-16`
**Issue:** The MSYS2/MINGW/CYGWIN block sets two hardcoded paths using short DOS 8.3 names:

```makefile
SHELL := C:/PROGRA~1/Git/bin/sh.exe
export PATH := C:/PROGRA~1/Docker/Docker/resources/bin:$(PATH)
```

These paths will fail in any of these scenarios:
- **Non-English Windows** — "Program Files" is localized (e.g., "Programme" in German), making `PROGRA~1` point to a different or non-existent directory.
- **Custom install locations** — Git or Docker installed on a different drive (e.g., `D:\Git`, `E:\Docker`).
- **Short-name collisions** — If another directory already claims `PROGRA~1`, the real "Program Files" gets `PROGRA~2`.
- **64-bit vs 32-bit** — Git might reside in `Program Files (x86)` with short name `PROGRA~2`.

A wrong `SHELL` path will cause ALL recipe commands to fail with "sh.exe: not found". A wrong Docker PATH means `docker` is not discoverable even when installed.

**Fix:** Detect the actual Git and Docker locations dynamically. Use environment-aware resolution instead of hardcoded paths:

```makefile
ifneq ($(filter MINGW% MSYS% CYGWIN%,$(UNAME_S)),)
  # Use the shell that invoked make itself — already correct for MSYS2/Git Bash
  # SHELL is already set correctly by MSYS2 make; only override if unset
  ifeq ($(origin SHELL),default)
    SHELL := sh.exe
  endif
  # Discover Docker via common install paths + registry, or rely on PATH
  DOCKER_BIN_DIR := $(or $(wildcard /c/Program Files/Docker/Docker/resources/bin),\
                         $(wildcard /c/Program Files (x86)/Docker/Docker/resources/bin))
  ifneq ($(DOCKER_BIN_DIR),)
    export PATH := $(DOCKER_BIN_DIR):$(PATH)
  endif
endif
```

Or, simpler and more robust — don't override SHELL at all (MSYS2 make already uses the correct shell), and for Docker, add a user-friendly error in `env-check-docker` rather than guessing install paths:

```makefile
ifneq ($(filter MINGW% MSYS% CYGWIN%,$(UNAME_S)),)
  # MSYS2/Git Bash already provides sh.exe as the default SHELL.
  # Do not hardcode paths. Rely on env-check-docker to validate Docker availability.
endif
```

---

### CR-02: `test-external` regressed from non-fatal to mandatory in `test-all`

**File:** `Makefile:19-28, 55-61`
**Issue:** In the old `test-all` target, `test-external` was invoked via `-$(MAKE) --no-print-directory test-external` — the leading `-` made Docker-unavailable failures non-fatal. The new platform routing places `test-external` inside `NATIVE_TARGETS` for ALL platforms:

```makefile
# Linux NATIVE_TARGETS
NATIVE_TARGETS := ... test-external   # mandatory (no - prefix)
# Darwin NATIVE_TARGETS
NATIVE_TARGETS := ... test-external   # mandatory (no - prefix)
# else (MINGW*/MSYS*/CYGWIN*)
NATIVE_TARGETS := ... test-external   # mandatory (no - prefix)
```

The `test-all` recipe invokes native targets WITHOUT the `-` prefix:
```makefile
@$(MAKE) --no-print-directory $(NATIVE_TARGETS)
```

Since `test-external` depends on `env-check-docker` (which fails when Docker is absent), `make test-all` now **fails** on any machine without Docker — including macOS, where the DEVELOPMENT.rst docs explicitly state Docker is optional.

**Fix:** Move `test-external` from `NATIVE_TARGETS` into `DOCKER_TARGETS` (which already uses `@-` prefix), or keep it in `NATIVE_TARGETS` but wrap it with `-` separately. The intent from the old Makefile was clear: Docker-backed tests are non-fatal.

```makefile
# Approach A: Move test-external to DOCKER_TARGETS (matches old behavior)
ifeq ($(UNAME_S),Linux)
  NATIVE_TARGETS := test-unit test-integration test-contract test-e2e test-compat test-perf test-slow test-posix
  DOCKER_TARGETS := test-docker-windows test-external
else ifeq ($(UNAME_S),Darwin)
  NATIVE_TARGETS := test-unit test-integration test-contract test-e2e test-compat test-perf test-slow test-posix
  DOCKER_TARGETS := test-docker-linux test-docker-windows test-external
else
  NATIVE_TARGETS := test-unit test-integration test-contract test-e2e test-compat test-perf test-slow test-posix test-windows
  DOCKER_TARGETS := test-docker-linux test-external
endif
```

Or, keep it in NATIVE_TARGETS but use `-` for just that target in the recipe:
```makefile
test-all: env-check
	@echo "=== Native targets ($(UNAME_S)) ==="
	@$(MAKE) --no-print-directory $(filter-out test-external,$(NATIVE_TARGETS))
	@-$(MAKE) --no-print-directory test-external
	@echo "=== Docker targets ==="
	@-$(MAKE) --no-print-directory $(DOCKER_TARGETS)
	@-$(MAKE) --no-print-directory render-tox-reports-run
```

---

## Warnings

### WR-01: `env-check-windows` uses bare `python` instead of `uv run python`

**File:** `Makefile:114`
**Issue:** The else branch of `env-check-windows` runs:
```makefile
python -c "import platform, sys; sys.exit(0 if platform.system() == 'Windows' else 1)"
```

The entire Makefile otherwise uses `$(PYTEST)` (which expands to `uv run python -m pytest`) and `uv run python`. Using bare `python` is inconsistent and may resolve to a different interpreter (Python 2, system Python, or missing entirely on Windows PATH). Furthermore, `env-check-windows` does not depend on `env-check`, so `uv`/Python availability is not verified before this check runs. If `python` is not on PATH, the error message will be a cryptic "python: command not found" rather than the intended "Windows target requires Windows host or WSL bridge."

**Fix:** Use `uv run python` for consistency, and add `env-check` as a prerequisite:
```makefile
env-check-windows: env-check
	@if [ "$$(uname -s 2>/dev/null)" = "Linux" ]; then \
		command -v wsl.exe >/dev/null || { echo "ERROR: Windows bridge missing. Run make env-install-windows."; exit 1; }; \
	else \
		uv run python -c "import platform, sys; sys.exit(0 if platform.system() == 'Windows' else 1)" || { echo "ERROR: Windows target requires Windows host or WSL bridge."; exit 1; }; \
	fi
```

---

### WR-02: `local-pr-gate` depends on `rg` (ripgrep) without availability check

**File:** `Makefile:179-182, 184-187`
**Issue:** The `local-pr-gate` target uses `rg` (ripgrep) in two `if` conditions:

```makefile
@if rg -n '"3\.9"|"pypy3\.9"' .github/workflows/*.yml; then \
    echo "ERROR: unsupported 3.9 matrix entries found in workflows"; \
    exit 1; \
fi
```

```makefile
@if ! rg -n '"jq;platform_system!=\x27Windows\x27"' pyproject.toml >/dev/null; then \
    echo "ERROR: jq dependency marker for Windows exclusion is missing in pyproject.toml"; \
    exit 1; \
fi
```

If `rg` is not installed on the developer's machine, `rg` returns exit code 127 (or similar non-zero). In the first check, `if rg ...` evaluates to FALSE, so the `then` branch (error) is SKIPPED — a **false negative**. Unsanctioned 3.9 entries in workflow files would pass silently. In the second check, `if ! rg ...` evaluates to TRUE, so the error IS shown — but the error message is misleading ("jq dependency marker is missing") when the real problem is that `rg` is not available.

**Fix:** Guard both checks with a `command -v rg` prerequisite, or use `grep -r` (more universally available):

```makefile
@command -v rg >/dev/null 2>&1 || { echo "ERROR: ripgrep (rg) is required for local-pr-gate. Install: https://github.com/BurntSushi/ripgrep"; exit 1; }
```

Or replace with `grep -r`:
```makefile
@if grep -rn '"3\.9"\|"pypy3\.9"' .github/workflows/*.yml; then \
    echo "ERROR: unsupported 3.9 matrix entries found in workflows"; \
    exit 1; \
fi
```

---

### WR-03: DEVELOPMENT.rst references non-existent `make test-docker` target

**File:** `DEVELOPMENT.rst:354`
**Issue:** The "Makefile Test API" section lists:
```
make test-docker
```
This target was split into `test-docker-linux` and `test-docker-windows` in this phase. The old `test-docker` target no longer exists. Running `make test-docker` will produce a Make error: `No rule to make target 'test-docker'`.

**Fix:** Update the documentation to list the actual available targets:
```rst
   # Docker-backed tests (split by platform)
   make test-docker-linux
   make test-docker-windows
```

---

### WR-04: DEVELOPMENT.rst reports wrong output extension for `render-tox-reports`

**File:** `DEVELOPMENT.rst:506`
**Issue:** The documentation states:
```
the Makefile renders HTML reports to ``.tmp/tox-reports/<envname>.html``
```
However, the Makefile (line 205) renders JSON using `--cucumber-json`:
```makefile
uv run render_cucumber_formatters --messages-ndjson "$$ndjson" --cucumber-json "$(TOX_HTML_REPORT_DIR)/$$envname.json"
```
The output extension is `.json`, not `.html`. (The variable name `TOX_HTML_REPORT_DIR` is also misleading — see IN-02.)

**Fix:** Correct the documentation to reflect the actual output format:
```rst
the Makefile renders JSON reports to ``.tmp/tox-reports/<envname>.json``
```

---

### WR-05: `env-check-windows` lacks `env-check` prerequisite

**File:** `Makefile:110-115`
**Issue:** `env-check-windows` runs Python (`python -c "..."`) but does not declare `env-check` as a prerequisite. If a developer runs `make test-windows` directly without first running `make env-install` or `make env-check`, the `env-check-windows` check will fail with a raw "python: command not found" shell error rather than the friendly "ERROR: uv missing. Run make env-install." message provided by `env-check`.

All other `env-check-*` targets should validate basic environment first, but `env-check-docker` and `env-check-browser` also lack `env-check` as a prerequisite — though they don't use Python directly so the impact is lower.

**Fix:** Add `env-check` as a prerequisite to `env-check-windows`:
```makefile
env-check-windows: env-check
```

---

## Info

### IN-01: Code duplication in NATIVE_TARGETS for Linux and Darwin

**File:** `Makefile:20-24`
**Issue:** The Linux and Darwin (macOS) branches define identical NATIVE_TARGETS lists:
```makefile
ifeq ($(UNAME_S),Linux)
  NATIVE_TARGETS := test-unit test-integration test-contract test-e2e test-compat test-perf test-slow test-posix test-external
  DOCKER_TARGETS := test-docker-windows
else ifeq ($(UNAME_S),Darwin)
  NATIVE_TARGETS := test-unit test-integration test-contract test-e2e test-compat test-perf test-slow test-posix test-external
  DOCKER_TARGETS := test-docker-linux test-docker-windows
```

The duplication is benign but makes maintenance harder — adding or removing a test target requires changing two identical lines.

**Fix:** Consolidate to a single POSIX block, with only DOCKER_TARGETS differing:
```makefile
ifeq ($(UNAME_S),Windows)
  $(error ...)
endif

# POSIX systems (Linux, Darwin, etc.)
NATIVE_TARGETS := test-unit test-integration test-contract test-e2e test-compat test-perf test-slow test-posix test-external

ifeq ($(UNAME_S),Darwin)
  DOCKER_TARGETS := test-docker-linux test-docker-windows
else
  DOCKER_TARGETS := test-docker-linux
endif
```

---

### IN-02: Variable `TOX_HTML_REPORT_DIR` is misleading — outputs JSON, not HTML

**File:** `Makefile:38`
**Issue:** The variable is named `TOX_HTML_REPORT_DIR` but the rendered output uses `--cucumber-json` (line 205), producing `.json` files. The directory contains JSON reports, not HTML. This naming can confuse developers looking for HTML artifacts.

**Fix:** Rename to `TOX_REPORT_DIR` or `TOX_JSON_REPORT_DIR`:
```makefile
TOX_REPORT_DIR ?= .tmp/tox-reports
```

Update all references (lines 38, 196, 197, 204, 205, 211) to use the new name.

---

### IN-03: `check-shell` target is a no-op placeholder

**File:** `Makefile:98-99`
**Issue:** The `check-shell` target does nothing (`@true`) and serves as a dependency of `env-check`. However, the actual unsupported-shell guard runs at Makefile parse-time (lines 10-12, `$(error ...)`) and is NOT executed by this target. The no-op `check-shell` likely confuses readers who expect it to perform the shell validation. It appears to be a leftover from development or a hook point for sub-makes.

**Fix:** Either remove `check-shell` entirely (the parse-time guard on lines 10-12 already handles this), or add a comment explaining its purpose if it serves a specific need:

```makefile
# check-shell is a no-op; the actual guard runs at parse-time (see UNAME_S check above).
# Included as a prerequisite anchor for sub-make contexts.
check-shell:
	@true
```

---

_Reviewed: 2026-05-21T00:00:00Z_
_Reviewer: the agent (gsd-code-reviewer)_
_Depth: standard_
