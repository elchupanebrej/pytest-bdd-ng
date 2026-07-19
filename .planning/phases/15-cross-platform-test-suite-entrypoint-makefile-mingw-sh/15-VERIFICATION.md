---
phase: 15
phase_name: Cross-platform test suite entrypoint (Makefile + MinGW sh)
status: superseded
verified_at: 2026-07-02T00:00:00Z
verification_mode: forensic
note: "Phase 27 (Replace Make&sh with Act) superseded Phase 15's Makefile-based entrypoint"
---

# Phase 15 Verification - Cross-platform test suite entrypoint

## Acceptance Criteria

| # | Criterion | Status | Evidence |
|---|-----------|--------|----------|
| 1 | OS detection at top of Makefile uses `uname -s` to detect Windows, macOS, Linux | SUPERSEDED | Root `Makefile` no longer exists — removed by Phase 27 (Replace Make&sh with Act). Phase 15's Makefile-based entrypoint was replaced by GitHub Actions workflow-based entrypoint. |
| 2 | Unsupported shell guard exits early with actionable error when invoked from cmd.exe/PowerShell | SUPERSEDED | Same as above. |
| 3 | Windows SHELL set to Git Bash `sh.exe` (short DOS path) and Docker bin added to PATH | SUPERSEDED | Same as above. |
| 4 | `test-docker` split into `test-docker-linux` and `test-docker-windows` with per-platform routing in `test-all` | SUPERSEDED | Same as above. |
| 5 | `test-all` routes native, Docker, and platform-specific targets per OS | SUPERSEDED | Same as above. |
| 6 | Shell syntax in `test-windows` and `test-posix` fixed for cross-platform compatibility | SUPERSEDED | Same as above. |
| 7 | DEVELOPMENT.rst has "Cross-Platform Setup" section with prerequisite table | PASS | `DEVELOPMENT.rst:22` has "Cross-Platform Setup" section with `.. list-table:: Cross-Platform Prerequisites` at line 30. Documents OS/tools/verify/install columns plus tox-backed pipeline. |
| 8 | All existing Makefile targets continue to work; no regressions in test suite | SUPERSEDED | Root `Makefile` no longer exists. CI workflows at `.github/workflows/` (docs.yml, env.yml, lint.yml, main.yml, messages-baseline-drift.yml, release.yaml, release.yml, tests.yml) provide test entrypoints. |

## Summary

Phase 15 was completed on 2026-05-23 with all Makefile cross-platform targets working. However, **Phase 27 subsequently replaced the Make-based entrypoint with GitHub Actions workflows and a Python command surface**, rendering the root `Makefile` obsolete. The Makefile was deleted as part of Phase 27's scope.

Of the 8 ROADMAP success criteria:
- **1 criterion (SC#7)** is verifiable: DEVELOPMENT.rst cross-platform section exists and is documented.
- **7 criteria (SC#1-6, SC#8)** are superseded by Phase 27's architectural replacement.

The cross-platform testing capability persists through the Phase 27 replacement (GitHub Actions workflows + Python command surface), but the specific Makefile-based implementation from Phase 15 no longer exists in the codebase.

## Pre-Existing Failures

- Phase 27 superseded Phase 15's Makefile approach. The Makefile was intentionally removed, not lost.
