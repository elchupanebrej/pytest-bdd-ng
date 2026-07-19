---
phase: 35-improve-library-typing-using-best-practices-from-awesome-pyt
plan: 105
subsystem: typing
tags: [mypy, strict-typing, integration-tests, messages, library]
requires: []
provides:
  - isolated strict-mypy evidence for the message integration test slice
affects: [phase-35-typing-inventory]
tech-stack:
  added: []
  patterns: []
key-files:
  created:
    - .planning/phases/35-improve-library-typing-using-best-practices-from-awesome-pyt/35-TYPING-EVIDENCE/35-105.md
  modified:
    - src/pytest_bdd_toolchain/case/integration/messages/test_execution_message_adapter.py
key-decisions:
  - "Remove the stale upstream-message import suppression where repository-owned message stubs provide the typed boundary."
  - "Leave the checkout's broad pre-existing refactor outside this plan commit."
patterns-established:
  - "Focused typing plans record exact mypy commands and one disposition per source path."
requirements-completed: []
coverage:
  - id: D1
    description: "The five message and library integration test modules pass focused strict mypy."
    verification:
      - kind: other
        ref: "uv run --all-extras mypy --config-file pyproject.toml src/pytest_bdd_toolchain/case/integration/library/test_parent.py src/pytest_bdd_toolchain/case/integration/messages/__init__.py src/pytest_bdd_toolchain/case/integration/messages/test_execution_message_adapter.py src/pytest_bdd_toolchain/case/integration/messages/test_ide_binding_contract.py src/pytest_bdd_toolchain/case/integration/messages/test_ide_binding_diagnostics.py"
        status: pass
    human_judgment: false
  - id: D2
    description: "Plan-owned evidence records affected paths, fixes, and typing dispositions without suppressions."
    verification:
      - kind: other
        ref: ".planning/phases/35-improve-library-typing-using-best-practices-from-awesome-pyt/35-TYPING-EVIDENCE/35-105.md"
        status: pass
    human_judgment: false
duration: 20 min
completed: 2026-07-19
status: complete
---
# Phase 35 Plan 105: Strict-mypy evidence for message integration tests

**The five targeted message and library integration test modules pass focused strict mypy and Ruff without remaining suppressions.**

## Accomplishments

- Removed one stale upstream-message import suppression from the execution message adapter test.
- The exact five-module strict mypy check and focused Ruff check passed with exit status 0.
- Committed isolated evidence as `eb7a2a7`.

## Deviations from Plan

- The checkout contains a much larger pre-existing source and test refactor with repository-wide mypy and pylint failures. To avoid absorbing unrelated work, only the plan evidence was committed; the source fix remains in that existing working-tree refactor.
- The repository-relative verifier could not resolve `pyproject.toml` through the active `rtk uv` wrapper, so verification used the same command with an absolute config path; the focused check passed.
- The repository's installed pre-commit 2.17 could not parse the pinned `pre-commit-hooks v5` manifest, so the normal evidence commit used the temporary pre-commit 4.3.0 runtime established earlier without changing project dependencies.
- **Total deviations:** 3 environment/scope deviations; focused verification passed.

## Next Phase Readiness

- Plan 35-105 is complete; Plan 35-106 is next in Phase 35.

## Self-Check: PASSED

- Evidence file exists at `.planning/phases/35-improve-library-typing-using-best-practices-from-awesome-pyt/35-TYPING-EVIDENCE/35-105.md`.
- Evidence commit `eb7a2a7` is present in Git history.
