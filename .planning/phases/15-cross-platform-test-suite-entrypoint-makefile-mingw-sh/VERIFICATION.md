---
phase: 15-cross-platform-test-suite-entrypoint-makefile-mingw-sh
verified: 2026-05-23T21:34:56Z
status: human_needed
score: 15/15 must-haves verified
overrides_applied: 0
re_verification:
  previous_status: gaps_found
  previous_score: 10/15
  gaps_closed:
    - "Windows SHELL/PATH fix restored with Git Bash short DOS path and Docker resources/bin PATH export"
    - "validate-test-all-backends probes selected PowerShell/WSL2/Docker backends before test-all subwork and hard-fails selected probes under FAIL_FAST=1"
    - "Linux/macOS Windows tox route validates env-check-docker-windows and uses python:3.14-windowsservercore-ltsc2022 before Windows tox Docker run"
    - "SPEC-named test targets now run tox instead of direct pytest"
  gaps_remaining: []
  regressions: []
human_verification:
  - test: "Run make test-all from Git Bash on Windows with WSL2 and Docker Desktop available"
    expected: "PowerShell native Windows tox, WSL2 Linux tox, Docker/external work, and report rendering follow documented collect/fail-fast behavior"
    why_human: "Requires real Windows host, Git Bash, PowerShell, WSL2, Docker Desktop state, and tox backend execution"
  - test: "Run make test-all on Linux and macOS hosts with Docker configured for requested non-native backends"
    expected: "Linux/macOS route Windows tox through validated Windows Docker or equivalent VM-like backend and route Linux/macOS native tox as documented"
    why_human: "Cross-host Docker backend behavior cannot be proven from this Windows workspace by static inspection alone"
---

# Phase 15: Cross-Platform Test Suite Entrypoint Verification Report

**Phase Goal:** Add a Makefile-based test entrypoint that works across platforms including MinGW shell.
**Verified:** 2026-05-23T21:34:56Z
**Status:** human_needed
**Re-verification:** Yes - after blocker fixes.

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|---|---|---|
| 1 | OS detection uses `uname -s` | VERIFIED | `UNAME_S := $(shell uname -s 2>/dev/null || echo Windows)` in `Makefile`. |
| 2 | PowerShell/cmd invocation blocked with actionable error | VERIFIED | `rtk make -n test-unit` from PowerShell exits before tests with `ERROR: make requires Git Bash on Windows. Run from Git Bash terminal.` |
| 3 | Windows SHELL short DOS path and Docker PATH export exist | VERIFIED | `Makefile:19` has `SHELL := C:/PROGRA~1/Git/bin/sh.exe`; `Makefile:20` exports `C:/PROGRA~1/Docker/Docker/resources/bin:$(PATH)`. |
| 4 | `test-docker` split targets exist | VERIFIED | `test-docker`, `test-docker-linux`, and `test-docker-windows` exist; split targets select Docker Linux/Windows marker scopes. |
| 5 | `test-all` has platform-specific routing | VERIFIED | `test-all: validate-test-all-backends` delegates to `test-platform-native`, `test-platform-linux`, `test-platform-windows`, and `test-platform-macos`. |
| 6 | `test-windows` and `test-posix` shell syntax fixed | VERIFIED | Both targets capture `EXIT=$$?` and ignore pytest exit 5 only. |
| 7 | DEVELOPMENT.rst Cross-Platform Setup table exists | VERIFIED | Section has OS/tools/verify/install columns plus tox-backed `make test-all` docs. |
| 8 | Existing Makefile targets continue to resolve | VERIFIED | Dry-runs parse for `test-all`, platform targets, split Docker targets, Windows/Posix targets; legacy target names remain. |
| 9 | `make test-all` documented as full tox-backed entrypoint | VERIFIED | DEVELOPMENT.rst documents tox-backed full cross-platform pipeline, backend routing, args, modes, and report behavior. |
| 10 | `test-all` delegates execution to tox-backed named sub-targets | VERIFIED | `test-all` invokes named platform targets; platform targets call `$(TOX) run -e ...`. |
| 11 | Windows native tox uses PowerShell; Windows Linux tox uses WSL2 | VERIFIED | `test-platform-windows` uses `powershell.exe ... $(TOX)` on MinGW; `test-platform-linux` uses `wsl.exe sh -lc "... $(TOX) ..."`. |
| 12 | Each platform target receives its own arg variable | VERIFIED | Dry-run with `TEST_NATIVE_ARGS=nat TEST_LINUX_ARGS=lin TEST_WINDOWS_ARGS=win TEST_MACOS_ARGS=mac` shows each arg only on its matching platform target invocation. |
| 13 | Default collect mode and `FAIL_FAST=1` behavior exist | VERIFIED | `FAIL_FAST`, `ARTIFACT_MODE`, and `REPORT_MODE` are wired; dry-runs show default collect branches and `FAIL_FAST=1` exit branches. |
| 14 | Required backend validation happens before tox subwork | VERIFIED | `validate-test-all-backends` runs before `test-all` recipe. Default mode probes selected PowerShell/WSL2/Docker backends with loud optional skip messages; `FAIL_FAST=1` hard-fails selected backend probes before subwork. |
| 15 | SPEC-named test targets are tox wrappers | VERIFIED | `test-unit`, `test-integration`, `test-contract`, `test-e2e`, `test-compat`, `test-perf`, `test-slow`, `test-docker-linux`, `test-docker-windows`, `test-windows`, and `test-posix` all invoke `$(TOX) run -e ...`; direct pytest remains only default `test` and external utility/support targets. |

**Score:** 15/15 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
|---|---|---|---|
| `Makefile` | Cross-platform entrypoint, MinGW shell fix, tox-backed routing, validation, args, modes | VERIFIED | `gsd-sdk verify.artifacts` passed; manual wiring confirms prior blocker fixes. |
| `DEVELOPMENT.rst` | Cross-platform setup plus tox pipeline docs | VERIFIED | `gsd-sdk verify.artifacts` passed; docs describe prerequisites, backend routing, validation, collect/fail-fast/report modes. |

### Key Link Verification

| From | To | Via | Status | Details |
|---|---|---|---|---|
| `Makefile:test-all` | `validate-test-all-backends` | target dependency | WIRED | `test-all: validate-test-all-backends`. |
| `Makefile:test-platform-windows` | PowerShell native tox launch | `powershell.exe` | WIRED | MinGW branch runs `powershell.exe ... $(TOX) run -e $(TOX_WINDOWS_ENVS)`. |
| `Makefile:test-platform-linux` | WSL2 Linux backend | `wsl.exe` | WIRED | MinGW branch runs `wsl.exe sh -lc "... $(TOX) run -e $(TOX_LINUX_ENVS) ..."`. |
| `Makefile:test-platform-windows` | Windows Docker backend on Linux/macOS | `env-check-docker-windows` then Windows image | WIRED | Non-MinGW branch calls `env-check-docker-windows`, then `docker run ... python:3.14-windowsservercore-ltsc2022 ... $(TOX)`. |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|---|---|---|---|---|
| `Makefile` | `UNAME_S` | `uname -s` fallback | Yes | FLOWING |
| `Makefile` | `TEST_*_ARGS` | Make variables into recursive target args and tox posargs | Yes | FLOWING |
| `Makefile` | backend availability | `command -v`, `uvx tox --version`, `wsl.exe`, `powershell.exe`, `docker info`, `docker version --format` | Yes | FLOWING |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|---|---|---|---|
| PowerShell shell guard | `rtk make -n test-unit` | Exit 1 with Git Bash error before pytest/tox work | PASS |
| `FAIL_FAST=1` validation before subwork | Git Bash `make -n test-all FAIL_FAST=1 REPORT_MODE=skip` | Shows `validate-test-all-backends` first; selected backend checks use hard-fail branch before platform target calls | PASS |
| Default validation probes | Git Bash `make -n validate-test-all-backends FAIL_FAST=0` | Shows PowerShell/WSL2 probes on MinGW plus Docker availability probe; Linux/macOS overrides show Docker backend probes | PASS |
| Linux/macOS Windows tox backend | Git Bash `make -n test-platform-windows UNAME_S=Linux/Darwin FAIL_FAST=1` | Shows `env-check-docker-windows` before `python:3.14-windowsservercore-ltsc2022` tox run | PASS |
| SPEC-named targets use tox | Static Makefile scan | All named targets from prior gap call `$(TOX) run`; no direct `$(PYTEST)` in those target bodies | PASS |

### Probe Execution

| Probe | Command | Result | Status |
|---|---|---|---|
| None declared | N/A | No `scripts/*/tests/probe-*.sh` or phase-declared probes found | SKIPPED |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|---|---|---|---|---|
| `P15-SPEC-TOX-PIPELINE` | `15-03-PLAN.md` / `15-SPEC.md` | Tox-backed Makefile pipeline, validation, routing, args, modes | SATISFIED | Makefile routes through tox platform targets, validates backends before subwork, documents collect/fail-fast behavior. |
| Roadmap SC 1-8 | ROADMAP Phase 15 | OS detection, shell guard/fix, Docker split, routing, shell syntax, docs, target no-regression | SATISFIED | All roadmap truths verified by Makefile/DEVELOPMENT.rst evidence and dry-runs. |

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|---|---:|---|---|---|
| None | N/A | N/A | N/A | `rtk rg` found no `TBD`, `FIXME`, `XXX`, `TODO`, `HACK`, placeholders, or empty implementations in `Makefile` / `DEVELOPMENT.rst`. |

### Human Verification Required

### 1. Windows Real Backend Run

**Test:** Run `make test-all` from Git Bash on Windows with WSL2 and Docker Desktop available.
**Expected:** PowerShell native Windows tox, WSL2 Linux tox, Docker/external work, and report rendering follow documented collect/fail-fast behavior.
**Why human:** Requires real Windows host, Git Bash, PowerShell, WSL2, Docker Desktop state, and tox backend execution.

### 2. Linux/macOS Real Backend Run

**Test:** Run `make test-all` on Linux and macOS hosts with Docker configured for requested non-native backends.
**Expected:** Linux/macOS route Windows tox through validated Windows Docker or equivalent VM-like backend and route Linux/macOS native tox as documented.
**Why human:** Cross-host Docker backend behavior cannot be proven from this Windows workspace by static inspection alone.

### Gaps Summary

No blocker gaps remain. All four prior verifier gaps are closed in the codebase. Automated/static verification reaches 15/15 must-haves. Final status is `human_needed` because real cross-platform backend execution requires target hosts and Docker/WSL/PowerShell environments.

---

_Verified: 2026-05-23T21:34:56Z_
_Verifier: the agent (gsd-verifier)_
