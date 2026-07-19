---
phase: 35-improve-library-typing-using-best-practices-from-awesome-pyt
plan: 117
subsystem: typing
tags: [mypy, strict-typing, unit-tests, parser, collector]
requires: []
provides:
  - isolated strict-mypy evidence for the parser and collector unit-test slice
affects: [phase-35-typing-inventory]
tech-stack:
  added: []
  patterns: []
key-files:
  created:
    - .planning/phases/35-improve-library-typing-using-best-practices-from-awesome-pyt/35-TYPING-EVIDENCE/35-117.md
  modified:
    - src/pytest_bdd_toolchain/case/unit/test_collector_batch.py
key-decisions:
  - "Remove stale assignment suppressions from the collector batch tests while preserving direct typed cache assignments."
  - "Leave the checkout's broad pre-existing refactor outside this plan commit."
patterns-established:
  - "Focused typing plans record exact mypy commands and one disposition per source path."
requirements-completed: []
coverage:
  - id: D1
    description: "The five parser and collector unit-test modules pass focused strict mypy."
    verification:
      - kind: other
        ref: "uv run --all-extras mypy --config-file pyproject.toml src/pytest_bdd_toolchain/case/unit/model/test_stash_access_maybe.py src/pytest_bdd_toolchain/case/unit/parser/test_parser_result_contract.py src/pytest_bdd_toolchain/case/unit/parser/test_parsers.py src/pytest_bdd_toolchain/case/unit/test_collector.py src/pytest_bdd_toolchain/case/unit/test_collector_batch.py"
        status: pass
    human_judgment: false
  - id: D2
    description: "Plan-owned evidence records affected paths and typing dispositions without suppressions."
    verification:
      - kind: other
        ref: ".planning/phases/35-improve-library-typing-using-best-practices-from-awesome-pyt/35-TYPING-EVIDENCE/35-117.md"
        status: pass
    human_judgment: false
duration: 20 min
completed: 2026-07-19
status: complete
---
# Phase 35 Plan 117: Strict-mypy evidence for parser and collector tests

**The five targeted parser and collector unit-test modules pass focused strict mypy and Ruff after removing three stale assignment suppressions.**

## Accomplishments

- The exact five-module strict mypy check passed with exit status 0.
- Removed the three target-slice `type: ignore[assignment]` comments while preserving runtime behavior.
- Focused Ruff passed and the target slice contains no typing suppressions.
- Committed isolated evidence as `6e95ce4`.

## Deviations from Plan

- The checkout contains a much larger pre-existing source and test refactor with repository-wide mypy and pylint failures. To avoid absorbing unrelated work, only the plan evidence was committed; source fixes remain in that existing working-tree refactor.
- The repository-relative verifier could not resolve `pyproject.toml` through the active `rtk uv` wrapper, so verification used the same command with an absolute config path; the focused check passed.
- The repository's installed pre-commit 2.17 could not parse the pinned `pre-commit-hooks v5` manifest, so the normal evidence commit used the temporary pre-commit 4.3.0 runtime established earlier without changing project dependencies.
- **Total deviations:** 3 environment/scope deviations; focused verification passed.

## Next Phase Readiness

- Plan 35-117 is complete; Plan 35-118 is next in Phase 35.

## Self-Check: PASSED

- Evidence file exists at `.planning/phases/35-improve-library-typing-using-best-practices-from-awesome-pyt/35-TYPING-EVIDENCE/35-117.md`.
- Evidence commit `6e95ce4` is present in Git history.
