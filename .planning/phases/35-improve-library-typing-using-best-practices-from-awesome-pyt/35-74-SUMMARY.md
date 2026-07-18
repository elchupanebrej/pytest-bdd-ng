---
phase: 35-improve-library-typing-using-best-practices-from-awesome-pyt
plan: 74
subsystem: typing
tags: [mypy, strict-typing, contract-tests, plugins]
requires: []
provides:
  - isolated strict-mypy evidence for five plugin and capability contract tests
affects: [phase-35-typing-inventory]
tech-stack:
  added: []
  patterns:
    - "Use the supported importlib.metadata entry_points(group=...) API instead of suppressing a cross-version union."
key-files:
  created:
    - .planning/phases/35-improve-library-typing-using-best-practices-from-awesome-pyt/35-TYPING-EVIDENCE/35-74.md
  modified:
    - src/pytest_bdd_toolchain/case/contract/test_phase28_rename.py
key-decisions:
  - "Remove the stale entry-points union suppression using the project's supported Python 3.10+ API."
  - "Record evidence independently and leave the checkout's broad pre-existing refactor outside this plan commit."
patterns-established:
  - "Focused typing plans record exact mypy commands and one disposition per source path."
requirements-completed: []
coverage:
  - id: D1
    description: "The five plugin and capability contract tests pass focused strict mypy."
    verification:
      - kind: other
        ref: "uv run --all-extras mypy --config-file pyproject.toml src/pytest_bdd_toolchain/case/contract/test_large_file_contract.py src/pytest_bdd_toolchain/case/contract/test_messages_capability_coverage_contract.py src/pytest_bdd_toolchain/case/contract/test_phase28_rename.py src/pytest_bdd_toolchain/case/contract/test_plugin_boundary_contract.py src/pytest_bdd_toolchain/case/contract/test_plugin_patterns_contract.py"
        status: pass
    human_judgment: false
  - id: D2
    description: "Plan-owned evidence records affected paths and typing dispositions."
    verification:
      - kind: other
        ref: ".planning/phases/35-improve-library-typing-using-best-practices-from-awesome-pyt/35-TYPING-EVIDENCE/35-74.md"
        status: pass
    human_judgment: false
duration: 15 min
completed: 2026-07-18
status: complete
---
# Phase 35 Plan 74: Strict-mypy evidence for plugin contracts

**The five plugin and capability contract tests pass focused strict mypy without target-slice suppressions.**

## Accomplishments

- The exact five-module strict mypy check passed with exit status 0.
- Replaced the stale entry-point union suppression with the supported typed API.
- Confirmed the target slice contains no typing suppressions and committed isolated evidence as `5b9d0ea`.

## Deviations from Plan

- The checkout contains a much larger pre-existing source and test refactor with repository-wide mypy and pylint failures. To avoid absorbing unrelated work, only the plan evidence was committed; source fixes remain in that existing working-tree refactor.
- The repository-relative verifier could not resolve `pyproject.toml` through the active `rtk uv` wrapper, so verification used the same command with an absolute config path; the focused check passed.
- The repository's installed pre-commit 2.17 could not parse the pinned `pre-commit-hooks v5` manifest, so the normal evidence commit used the temporary pre-commit 4.3.0 runtime established earlier without changing project dependencies.
- **Total deviations:** 3 environment/scope deviations; focused verification passed.

## Next Phase Readiness

- Plan 35-74 is complete; Plan 35-75 is next in Phase 35.
