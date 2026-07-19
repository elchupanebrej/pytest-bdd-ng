---
phase: 35-improve-library-typing-using-best-practices-from-awesome-pyt
plan: 106
subsystem: typing
tags: [mypy, strict-typing, integration-tests, messages, ast]
requires: []
provides:
  - isolated strict-mypy evidence for the message and AST integration test slice
affects: [phase-35-typing-inventory]
tech-stack:
  added: []
  patterns: []
key-files:
  created:
    - .planning/phases/35-improve-library-typing-using-best-practices-from-awesome-pyt/35-TYPING-EVIDENCE/35-106.md
  modified:
    - src/pytest_bdd_toolchain/case/integration/messages/test_message_attachments.py
    - src/pytest_bdd_toolchain/case/integration/messages/test_message_emission_points.py
key-decisions:
  - "Remove stale upstream-message import suppressions where repository-owned message stubs provide the typed boundary."
  - "Replace the AST helper's complexity suppression with small typed helpers and preserve its inferred payload sets."
  - "Leave the checkout's broad pre-existing refactor outside this plan commit."
patterns-established:
  - "Focused typing plans record exact mypy commands and one disposition per source path."
requirements-completed: []
coverage:
  - id: D1
    description: "The five message integration test modules pass focused strict mypy."
    verification:
      - kind: other
        ref: "uv run --all-extras mypy --config-file pyproject.toml src/pytest_bdd_toolchain/case/integration/messages/test_ide_step_bindings.py src/pytest_bdd_toolchain/case/integration/messages/test_message_attachments.py src/pytest_bdd_toolchain/case/integration/messages/test_message_emission_points.py src/pytest_bdd_toolchain/case/integration/messages/test_message_extension.py src/pytest_bdd_toolchain/case/integration/messages/test_message_outcome_mapping.py"
        status: pass
    human_judgment: false
  - id: D2
    description: "Plan-owned evidence records affected paths, fixes, and typing dispositions without suppressions."
    verification:
      - kind: other
        ref: ".planning/phases/35-improve-library-typing-using-best-practices-from-awesome-pyt/35-TYPING-EVIDENCE/35-106.md"
        status: pass
    human_judgment: false
duration: 25 min
completed: 2026-07-19
status: complete
---
# Phase 35 Plan 106: Strict-mypy evidence for message AST tests

**The five targeted message integration test modules pass focused strict mypy and Ruff without remaining suppressions.**

## Accomplishments

- Removed four stale upstream-message import suppressions from the attachment integration tests.
- Replaced the message-emission AST helper's complexity suppression with typed helper functions.
- The exact five-module strict mypy check and focused Ruff check passed with exit status 0.
- Committed isolated evidence as `95b7d8e`.

## Deviations from Plan

- The checkout contains a much larger pre-existing source and test refactor with repository-wide mypy and pylint failures. To avoid absorbing unrelated work, only the plan evidence was committed; the source fixes remain in that existing working-tree refactor.
- The repository-relative verifier could not resolve `pyproject.toml` through the active `rtk uv` wrapper, so verification used the same command with an absolute config path; the focused check passed.
- The repository's installed pre-commit 2.17 could not parse the pinned `pre-commit-hooks v5` manifest, so the normal evidence commit used the temporary pre-commit 4.3.0 runtime established earlier without changing project dependencies.
- **Total deviations:** 3 environment/scope deviations; focused verification passed.

## Next Phase Readiness

- Plan 35-106 is complete; Plan 35-107 is next in Phase 35.

## Self-Check: PASSED

- Evidence file exists at `.planning/phases/35-improve-library-typing-using-best-practices-from-awesome-pyt/35-TYPING-EVIDENCE/35-106.md`.
- Evidence commit `95b7d8e` is present in Git history.
