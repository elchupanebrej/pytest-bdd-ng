---
phase: 35-improve-library-typing-using-best-practices-from-awesome-pyt
plan: 110
subsystem: typing
tags: [mypy, strict-typing, unit-tests, parsers]
requires: []
provides:
  - isolated strict-mypy evidence for the parser argument unit-test slice
affects: [phase-35-typing-inventory]
tech-stack:
  added: []
  patterns: []
key-files:
  created:
    - .planning/phases/35-improve-library-typing-using-best-practices-from-awesome-pyt/35-TYPING-EVIDENCE/35-110.md
  modified: []
key-decisions:
  - "Record the clean five-module verification as isolated evidence without source changes."
  - "Leave the checkout's broad pre-existing refactor outside this plan commit."
patterns-established:
  - "Focused typing plans record exact mypy commands and one disposition per source path."
requirements-completed: []
coverage:
  - id: D1
    description: "The five parser argument unit-test modules pass focused strict mypy."
    verification:
      - kind: other
        ref: "uv run --all-extras mypy --config-file pyproject.toml src/pytest_bdd_toolchain/case/unit/args/cfparse/test_args.py src/pytest_bdd_toolchain/case/unit/args/cucumber_expression/__init__.py src/pytest_bdd_toolchain/case/unit/args/cucumber_expression/test_args.py src/pytest_bdd_toolchain/case/unit/args/heuristic/__init__.py src/pytest_bdd_toolchain/case/unit/args/heuristic/test_args.py"
        status: pass
    human_judgment: false
  - id: D2
    description: "Plan-owned evidence records affected paths and typing dispositions without suppressions."
    verification:
      - kind: other
        ref: ".planning/phases/35-improve-library-typing-using-best-practices-from-awesome-pyt/35-TYPING-EVIDENCE/35-110.md"
        status: pass
    human_judgment: false
duration: 15 min
completed: 2026-07-19
status: complete
---
# Phase 35 Plan 110: Strict-mypy evidence for parser argument tests

**The five targeted parser argument unit-test modules pass focused strict mypy and Ruff without source changes or target-slice suppressions.**

## Accomplishments

- The exact five-module strict mypy check passed with exit status 0.
- Confirmed the target slice contains no typing suppressions and committed isolated evidence as `97ccf1a`.

## Deviations from Plan

- The checkout contains a much larger pre-existing source and test refactor with repository-wide mypy and pylint failures. To avoid absorbing unrelated work, only the plan evidence was committed; source fixes remain in that existing working-tree refactor.
- The repository-relative verifier could not resolve `pyproject.toml` through the active `rtk uv` wrapper, so verification used the same command with an absolute config path; the focused check passed.
- The repository's installed pre-commit 2.17 could not parse the pinned `pre-commit-hooks v5` manifest, so the normal evidence commit used the temporary pre-commit 4.3.0 runtime established earlier without changing project dependencies.
- **Total deviations:** 3 environment/scope deviations; focused verification passed.

## Next Phase Readiness

- Plan 35-110 is complete; Plan 35-111 is next in Phase 35.

## Self-Check: PASSED

- Evidence file exists at `.planning/phases/35-improve-library-typing-using-best-practices-from-awesome-pyt/35-TYPING-EVIDENCE/35-110.md`.
- Evidence commit `97ccf1a` is present in Git history.
