---
phase: 35-improve-library-typing-using-best-practices-from-awesome-pyt
plan: 107
subsystem: typing
tags: [mypy, strict-typing, integration-tests, messages, struct-bdd]
requires: []
provides:
  - isolated strict-mypy evidence for the message and StructBDD integration test slice
affects: [phase-35-typing-inventory]
tech-stack:
  added: []
  patterns: []
key-files:
  created:
    - .planning/phases/35-improve-library-typing-using-best-practices-from-awesome-pyt/35-TYPING-EVIDENCE/35-107.md
  modified:
    - src/pytest_bdd_toolchain/case/integration/messages/test_tolerant_step_reporting.py
    - src/pytest_bdd_toolchain/case/integration/struct_bdd/test_deserialization.py
    - src/pytest_bdd_toolchain/case/integration/struct_bdd/test_gherkin_document_model_compat.py
key-decisions:
  - "Remove stale message and converter import suppressions where repository-owned typing provides the boundary."
  - "Leave the checkout's broad pre-existing refactor outside this plan commit."
patterns-established:
  - "Focused typing plans record exact mypy commands and one disposition per source path."
requirements-completed: []
coverage:
  - id: D1
    description: "The five message and StructBDD integration test modules pass focused strict mypy."
    verification:
      - kind: other
        ref: "uv run --all-extras mypy --config-file pyproject.toml src/pytest_bdd_toolchain/case/integration/messages/test_startup_imports.py src/pytest_bdd_toolchain/case/integration/messages/test_tolerant_step_reporting.py src/pytest_bdd_toolchain/case/integration/struct_bdd/__init__.py src/pytest_bdd_toolchain/case/integration/struct_bdd/test_deserialization.py src/pytest_bdd_toolchain/case/integration/struct_bdd/test_gherkin_document_model_compat.py"
        status: pass
    human_judgment: false
  - id: D2
    description: "Plan-owned evidence records affected paths, fixes, and typing dispositions without suppressions."
    verification:
      - kind: other
        ref: ".planning/phases/35-improve-library-typing-using-best-practices-from-awesome-pyt/35-TYPING-EVIDENCE/35-107.md"
        status: pass
    human_judgment: false
duration: 20 min
completed: 2026-07-19
status: complete
---
# Phase 35 Plan 107: Strict-mypy evidence for StructBDD tests

**The five targeted message and StructBDD integration test modules pass focused strict mypy and Ruff without remaining suppressions.**

## Accomplishments

- Removed three stale message/converter import suppressions from the target slice.
- The exact five-module strict mypy check and focused Ruff check passed with exit status 0.
- Committed isolated evidence as `2544c05`.

## Deviations from Plan

- The checkout contains a much larger pre-existing source and test refactor with repository-wide mypy and pylint failures. To avoid absorbing unrelated work, only the plan evidence was committed; the source fixes remain in that existing working-tree refactor.
- The repository-relative verifier could not resolve `pyproject.toml` through the active `rtk uv` wrapper, so verification used the same command with an absolute config path; the focused check passed.
- The repository's installed pre-commit 2.17 could not parse the pinned `pre-commit-hooks v5` manifest, so the normal evidence commit used the temporary pre-commit 4.3.0 runtime established earlier without changing project dependencies.
- **Total deviations:** 3 environment/scope deviations; focused verification passed.

## Next Phase Readiness

- Plan 35-107 is complete; Plan 35-108 is next in Phase 35.

## Self-Check: PASSED

- Evidence file exists at `.planning/phases/35-improve-library-typing-using-best-practices-from-awesome-pyt/35-TYPING-EVIDENCE/35-107.md`.
- Evidence commit `2544c05` is present in Git history.
