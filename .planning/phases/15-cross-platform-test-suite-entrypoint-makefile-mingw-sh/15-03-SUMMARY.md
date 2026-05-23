---
phase: 15-cross-platform-test-suite-entrypoint-makefile-mingw-sh
plan: 03
subsystem: testing
tags: [makefile, tox, cross-platform, git-bash, wsl2, powershell]

requires:
  - phase: 15-cross-platform-test-suite-entrypoint-makefile-mingw-sh
    provides: "Phase 15 plans 01 and 02 established Makefile platform routing and cross-platform setup docs"
provides:
  - "tox-backed make test-all orchestration through named platform targets"
  - "backend validation for native tox, PowerShell, WSL2, and Docker probes"
  - "per-platform argument forwarding and FAIL_FAST/ARTIFACT_MODE/REPORT_MODE controls"
affects: [testing, developer-workflow, cross-platform]

tech-stack:
  added: []
  patterns:
    - "Make remains the human test entrypoint while tox executes platform matrix work"
    - "Dry-run friendly target calls expose per-platform arg forwarding without executing subtargets"

key-files:
  created:
    - ".planning/phases/15-cross-platform-test-suite-entrypoint-makefile-mingw-sh/15-03-SUMMARY.md"
  modified:
    - "Makefile"
    - "DEVELOPMENT.rst"
    - ".planning/ROADMAP.md"
    - ".planning/STATE.md"

key-decisions:
  - "Kept Make as the public test API and routed full/platform test execution through tox-backed subtargets."
  - "Used collect mode as the default so missing non-native Docker/WSL backends are loud but non-fatal unless FAIL_FAST=1."
  - "Made test-all dry-run output show target-specific argument forwarding without invoking recursive subtargets."

patterns-established:
  - "Cross-platform Make targets validate required native tox first, then route non-native work through explicit backend commands."
  - "TEST_*_ARGS variables are passed only to their matching platform target; TEST_ALL_ARGS remains shared."

requirements-completed: ["P15-SPEC-TOX-PIPELINE"]

duration: 34min
completed: 2026-05-24
---

# Phase 15 Plan 03: Tox-Backed Cross-Platform Test Pipeline Summary

**Make test-all now validates tox backends and delegates full cross-platform execution to named tox-backed platform targets.**

## Performance

- **Duration:** 34 min
- **Started:** 2026-05-23T23:34:00+03:00
- **Completed:** 2026-05-24T00:08:19+03:00
- **Tasks:** 3
- **Files modified:** 2 implementation/doc files

## Accomplishments

- Added tox execution variables, platform env mappings, and isolated `TEST_NATIVE_ARGS`, `TEST_LINUX_ARGS`, `TEST_WINDOWS_ARGS`, and `TEST_MACOS_ARGS`.
- Converted `make test-all` to depend on `validate-test-all-backends` and delegate to `test-platform-native`, `test-platform-linux`, `test-platform-windows`, and `test-platform-macos`.
- Added backend validation and routing for PowerShell-native Windows tox, WSL2 Linux tox from Git Bash, host tox, and Docker-backed non-native probes.
- Documented the tox-backed pipeline, backend routing, collect/default mode, `FAIL_FAST=1`, `REPORT_MODE`, and target-specific argument forwarding.

## Task Commits

1. **Task 1: Convert full and platform test entrypoints to tox-backed debuggable targets** - `08535672` (feat)
2. **Task 2: Add backend preflight validation plus fail-fast and artifact/report modes** - `08535672` (feat)
3. **Task 3: Document and verify the tox-backed pipeline gap closure** - `08535672` (feat)

**Plan metadata:** committed separately with this summary.

## Files Created/Modified

- `Makefile` - Adds tox-backed platform targets, backend validation, routing, fail-fast/report modes, and isolated argument forwarding.
- `DEVELOPMENT.rst` - Documents the tox-backed `make test-all` pipeline, backend routing, validation semantics, and argument variables.
- `.planning/phases/15-cross-platform-test-suite-entrypoint-makefile-mingw-sh/15-03-SUMMARY.md` - Records gap closure execution.

## Decisions Made

- Kept `make test-all` as the human entrypoint while tox owns platform execution.
- Defaulted to artifact collection semantics: non-native backend absence is loud and skipped in collect mode, while `FAIL_FAST=1` hard-fails early.
- Avoided recursive `$(MAKE)` in dry-run-visible orchestration so `make -n test-all` remains inspection-only and still shows target-specific args.

## Verification

- `rtk powershell ...` static checks passed for tox variables, platform targets, validation targets, backend launch patterns, and documentation tokens.
- `rtk make -n test-all TEST_NATIVE_ARGS='-k native_only' TEST_LINUX_ARGS='-k linux_only' TEST_WINDOWS_ARGS='-k windows_only' TEST_MACOS_ARGS='-k macos_only' FAIL_FAST=1 REPORT_MODE=skip` passed dry-run inspection.
- `rtk sh -lc ...` arg isolation check passed: each platform arg appears only on its matching target line.
- `rtk uv run pre-commit run --files Makefile DEVELOPMENT.rst` passed.

## Deviations from Plan

None - plan executed as written. The only implementation adjustment was making `test-all` dry-run friendly after discovering GNU Make executes recipe lines containing recursive `$(MAKE)` even under `make -n`; this preserved the planned dry-run verification contract.

**Total deviations:** 0 auto-fixed.
**Impact on plan:** No scope change.

## Issues Encountered

- Nested PowerShell quoting broke two verification command attempts; the same checks were rerun with escaped script blocks or Git Bash-native shell commands and passed.
- Initial dry-run design used recursive `$(MAKE)` inside a shell loop, which caused dry-run subtarget execution. Reworked `test-all` to expose explicit target calls without executing subtargets in dry-run mode.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

Phase 15 gap closure is ready for final verification. The remaining check should confirm `VERIFICATION.md` status can move from gap-found to passed for the tox-backed cross-platform pipeline scope.

---
*Phase: 15-cross-platform-test-suite-entrypoint-makefile-mingw-sh*
*Completed: 2026-05-24*
