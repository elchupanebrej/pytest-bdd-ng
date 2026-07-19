---
phase: 35-improve-library-typing-using-best-practices-from-awesome-pyt
plan: 101
subsystem: typing
tags: [mypy, strict-typing, integration-tests, hooks, formatters]
requires: []
provides:
  - isolated strict-mypy evidence for the hook and gherkin integration test slice
affects: [phase-35-typing-inventory]
tech-stack:
  added: []
  patterns: []
key-files:
  created:
    - .planning/phases/35-improve-library-typing-using-best-practices-from-awesome-pyt/35-TYPING-EVIDENCE/35-101.md
  modified:
    - src/pytest_bdd_toolchain/case/integration/gherkin_integration/test_pickles_load.py
    - src/pytest_bdd_toolchain/case/integration/hook/test_gherkin_reporter_context_lifecycle.py
key-decisions:
  - "Remove stale upstream-attribute and dynamic-assignment suppressions where repository-owned typing boundaries already make them unnecessary."
  - "Leave the checkout's broad pre-existing refactor outside this plan commit."
patterns-established:
  - "Focused typing plans record exact mypy commands and one disposition per source path."
requirements-completed: []
coverage:
  - id: D1
    description: "The five hook and gherkin integration test modules pass focused strict mypy."
    verification:
      - kind: other
        ref: "uv run --all-extras mypy --config-file pyproject.toml src/pytest_bdd_toolchain/case/integration/gherkin_integration/test_pickles_load.py src/pytest_bdd_toolchain/case/integration/hook/__init__.py src/pytest_bdd_toolchain/case/integration/hook/test_gherkin_message_reporter_pytest90_regression.py src/pytest_bdd_toolchain/case/integration/hook/test_gherkin_reporter_context_lifecycle.py src/pytest_bdd_toolchain/case/integration/hook/test_heading_validation_diagnostics.py"
        status: pass
    human_judgment: false
  - id: D2
    description: "Plan-owned evidence records affected paths, fixes, and typing dispositions without suppressions."
    verification:
      - kind: other
        ref: ".planning/phases/35-improve-library-typing-using-best-practices-from-awesome-pyt/35-TYPING-EVIDENCE/35-101.md"
        status: pass
    human_judgment: false
duration: 20 min
completed: 2026-07-19
status: complete
---
# Phase 35 Plan 101: Strict-mypy evidence for hook integration tests

**The five targeted hook and gherkin integration test modules pass focused strict mypy and Ruff without remaining suppressions.**

## Accomplishments

- Removed two stale upstream-attribute suppressions in the pickle and reporter integration tests.
- Removed the dynamic method-assignment suppression and renamed the unused helper parameter.
- The exact five-module strict mypy check and focused Ruff check passed with exit status 0.
- Committed isolated evidence as `e149399`.

## Deviations from Plan

- The checkout contains a much larger pre-existing source and test refactor with repository-wide mypy and pylint failures. To avoid absorbing unrelated work, only the plan evidence was committed; the two source fixes remain in that existing working-tree refactor.
- The repository-relative verifier could not resolve `pyproject.toml` through the active `rtk uv` wrapper, so verification used the same command with an absolute config path; the focused check passed.
- The repository's installed pre-commit 2.17 could not parse the pinned `pre-commit-hooks v5` manifest, so the normal evidence commit used the temporary pre-commit 4.3.0 runtime established earlier without changing project dependencies.
- **Total deviations:** 3 environment/scope deviations; focused verification passed.

## Next Phase Readiness

- Plan 35-101 is complete; Plan 35-102 is next in Phase 35.

## Self-Check: PASSED

- Evidence file exists at `.planning/phases/35-improve-library-typing-using-best-practices-from-awesome-pyt/35-TYPING-EVIDENCE/35-101.md`.
- Evidence commit `e149399` is present in Git history.
