---
phase: 35-improve-library-typing-using-best-practices-from-awesome-pyt
plan: 119
subsystem: typing
tags: [mypy, strict-typing, unit-tests, gherkin-go, group-ordering]
requires: []
provides:
  - isolated strict-mypy evidence for the Go fallback, group-ordering, marker-audit, and mypy-check unit-test slice
affects: [phase-35-typing-inventory]
tech-stack:
  added: []
  patterns: []
key-files:
  created:
    - .planning/phases/35-improve-library-typing-using-best-practices-from-awesome-pyt/35-TYPING-EVIDENCE/35-119.md
  modified:
    - src/pytest_bdd_toolchain/case/unit/test_group_ordering.py
key-decisions:
  - "Remove stale argument-type suppressions from group-ordering tests while preserving their fake pytest boundaries."
  - "Leave the checkout's broad pre-existing refactor outside this plan commit."
patterns-established:
  - "Focused typing plans record exact mypy commands and one disposition per source path."
requirements-completed: []
coverage:
  - id: D1
    description: "The five Go fallback, group-ordering, marker-audit, and mypy-check unit-test modules pass focused strict mypy."
    verification:
      - kind: other
        ref: "uv run --all-extras mypy --config-file pyproject.toml src/pytest_bdd_toolchain/case/unit/test_gherkin_go_fallback.py src/pytest_bdd_toolchain/case/unit/test_gherkin_go_parse.py src/pytest_bdd_toolchain/case/unit/test_group_ordering.py src/pytest_bdd_toolchain/case/unit/test_marker_audit.py src/pytest_bdd_toolchain/case/unit/test_mypy_strict.py"
        status: pass
    human_judgment: false
  - id: D2
    description: "Plan-owned evidence records affected paths and typing dispositions without suppressions."
    verification:
      - kind: other
        ref: ".planning/phases/35-improve-library-typing-using-best-practices-from-awesome-pyt/35-TYPING-EVIDENCE/35-119.md"
        status: pass
    human_judgment: false
duration: 20 min
completed: 2026-07-19
status: complete
---
# Phase 35 Plan 119: Strict-mypy evidence for Go fallback and group-ordering tests

**The five targeted Go fallback, group-ordering, marker-audit, and mypy-check unit-test modules pass focused strict mypy and Ruff after removing ten stale argument-type suppressions.**

## Accomplishments

- The exact five-module strict mypy check passed with exit status 0.
- Removed ten target-slice `type: ignore[arg-type]` comments while preserving runtime behavior.
- Focused Ruff passed and the target slice contains no typing suppressions.
- Committed isolated evidence as `c974498`.

## Deviations from Plan

- The checkout contains a much larger pre-existing source and test refactor with repository-wide mypy and pylint failures. To avoid absorbing unrelated work, only the plan evidence was committed; source fixes remain in that existing working-tree refactor.
- The repository-relative verifier could not resolve `pyproject.toml` through the active `rtk uv` wrapper, so verification used the same command with an absolute config path; the focused check passed.
- The repository's installed pre-commit 2.17 could not parse the pinned `pre-commit-hooks v5` manifest, so the normal evidence commit used the temporary pre-commit 4.3.0 runtime established earlier without changing project dependencies.
- **Total deviations:** 3 environment/scope deviations; focused verification passed.

## Next Phase Readiness

- Plan 35-119 is complete; Plan 35-120 is next in Phase 35.

## Self-Check: PASSED

- Evidence file exists at `.planning/phases/35-improve-library-typing-using-best-practices-from-awesome-pyt/35-TYPING-EVIDENCE/35-119.md`.
- Evidence commit `c974498` is present in Git history.
