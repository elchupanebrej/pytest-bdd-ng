---
phase: 35-improve-library-typing-using-best-practices-from-awesome-pyt
plan: 121
subsystem: typing
tags: [mypy, strict-typing, unit-tests, scenario, pylint]
requires: []
provides:
  - isolated strict-mypy evidence for scenario, locator, step, import-coverage, and pylint unit tests
affects: [phase-35-typing-inventory]
tech-stack:
  added: []
  patterns: []
key-files:
  created:
    - .planning/phases/35-improve-library-typing-using-best-practices-from-awesome-pyt/35-TYPING-EVIDENCE/35-121.md
  modified: []
key-decisions:
  - "Treat the type-ignore text in the pylint checker fixture as test data rather than an active suppression."
  - "Leave the checkout's broad pre-existing refactor outside this plan commit."
patterns-established:
  - "Focused typing plans record exact mypy commands and one disposition per source path."
requirements-completed: []
coverage:
  - id: D1
    description: "The five scenario, locator, step, import-coverage, and pylint unit-test modules pass focused strict mypy."
    verification:
      - kind: other
        ref: "uv run --all-extras mypy --config-file pyproject.toml src/pytest_bdd_toolchain/case/unit/test_phase14_import_coverage.py src/pytest_bdd_toolchain/case/unit/test_pylint_checkers.py src/pytest_bdd_toolchain/case/unit/test_scenario.py src/pytest_bdd_toolchain/case/unit/test_scenario_locator.py src/pytest_bdd_toolchain/case/unit/test_step_internals.py"
        status: pass
    human_judgment: false
  - id: D2
    description: "Plan-owned evidence records affected paths and typing dispositions without active suppressions."
    verification:
      - kind: other
        ref: ".planning/phases/35-improve-library-typing-using-best-practices-from-awesome-pyt/35-TYPING-EVIDENCE/35-121.md"
        status: pass
    human_judgment: false
duration: 15 min
completed: 2026-07-19
status: complete
---
# Phase 35 Plan 121: Strict-mypy evidence for scenario and checker tests

**The five targeted scenario, locator, step, import-coverage, and pylint unit-test modules pass focused strict mypy and Ruff without source changes or active target-slice suppressions.**

## Accomplishments

- The exact five-module strict mypy check passed with exit status 0.
- Confirmed the only suppression-pattern match is intentional checker-test fixture text.
- Focused Ruff passed and committed isolated evidence as `a9a2cdb`.

## Deviations from Plan

- The checkout contains a much larger pre-existing source and test refactor with repository-wide mypy and pylint failures. To avoid absorbing unrelated work, only the plan evidence was committed; source fixes remain in that existing working-tree refactor.
- The repository-relative verifier could not resolve `pyproject.toml` through the active `rtk uv` wrapper, so verification used the same command with an absolute config path; the focused check passed.
- The repository's installed pre-commit 2.17 could not parse the pinned `pre-commit-hooks v5` manifest, so the normal evidence commit used the temporary pre-commit 4.3.0 runtime established earlier without changing project dependencies.
- **Total deviations:** 3 environment/scope deviations; focused verification passed.

## Next Phase Readiness

- Plan 35-121 is complete; Plan 35-122 is next in Phase 35.

## Self-Check: PASSED

- Evidence file exists at `.planning/phases/35-improve-library-typing-using-best-practices-from-awesome-pyt/35-TYPING-EVIDENCE/35-121.md`.
- Evidence commit `a9a2cdb` is present in Git history.
