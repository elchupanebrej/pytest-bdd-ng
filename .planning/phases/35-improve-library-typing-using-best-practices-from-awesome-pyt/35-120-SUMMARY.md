---
phase: 35-improve-library-typing-using-best-practices-from-awesome-pyt
plan: 120
subsystem: typing
tags: [mypy, strict-typing, unit-tests, parser, governance]
requires: []
provides:
  - isolated strict-mypy evidence for parser, performance, and Phase 14 gap unit tests
affects: [phase-35-typing-inventory]
tech-stack:
  added: []
  patterns: []
key-files:
  created:
    - .planning/phases/35-improve-library-typing-using-best-practices-from-awesome-pyt/35-TYPING-EVIDENCE/35-120.md
  modified:
    - src/pytest_bdd_toolchain/case/unit/test_phase14_gap_modules.py
key-decisions:
  - "Replace the intentional invalid-cadence suppression with a quoted cast boundary and preserve the runtime-invalid test value."
  - "Build the POSIX RAM-temp path from path components so the intentional filesystem assertion needs no noqa."
  - "Leave the checkout's broad pre-existing refactor outside this plan commit."
patterns-established:
  - "Focused typing plans record exact mypy commands and one disposition per source path."
requirements-completed: []
coverage:
  - id: D1
    description: "The five parser, performance, and Phase 14 gap unit-test modules pass focused strict mypy."
    verification:
      - kind: other
        ref: "uv run --all-extras mypy --config-file pyproject.toml src/pytest_bdd_toolchain/case/unit/test_no_commented_code.py src/pytest_bdd_toolchain/case/unit/test_parser.py src/pytest_bdd_toolchain/case/unit/test_parsers_unit.py src/pytest_bdd_toolchain/case/unit/test_performance_batch.py src/pytest_bdd_toolchain/case/unit/test_phase14_gap_modules.py"
        status: pass
    human_judgment: false
  - id: D2
    description: "Plan-owned evidence records affected paths and typing dispositions without suppressions."
    verification:
      - kind: other
        ref: ".planning/phases/35-improve-library-typing-using-best-practices-from-awesome-pyt/35-TYPING-EVIDENCE/35-120.md"
        status: pass
    human_judgment: false
duration: 20 min
completed: 2026-07-19
status: complete
---
# Phase 35 Plan 120: Strict-mypy evidence for parser and governance tests

**The five targeted parser, performance, and Phase 14 gap unit-test modules pass focused strict mypy and Ruff after replacing two local suppressions with typed/path-safe code.**

## Accomplishments

- The exact five-module strict mypy check passed with exit status 0.
- Replaced the invalid-cadence `type: ignore[arg-type]` with a typed cast boundary.
- Replaced the RAM-temp-path `noqa` with equivalent path-component construction.
- Focused Ruff passed and the precise suppression scan is empty.
- Committed isolated evidence as `68e1346`.

## Deviations from Plan

- The checkout contains a much larger pre-existing source and test refactor with repository-wide mypy and pylint failures. To avoid absorbing unrelated work, only the plan evidence was committed; source fixes remain in that existing working-tree refactor.
- The repository-relative verifier could not resolve `pyproject.toml` through the active `rtk uv` wrapper, so verification used the same command with an absolute config path; the focused check passed.
- The repository's installed pre-commit 2.17 could not parse the pinned `pre-commit-hooks v5` manifest, so the normal evidence commit used the temporary pre-commit 4.3.0 runtime established earlier without changing project dependencies.
- **Total deviations:** 3 environment/scope deviations; focused verification passed.

## Next Phase Readiness

- Plan 35-120 is complete; Plan 35-121 is next in Phase 35.

## Self-Check: PASSED

- Evidence file exists at `.planning/phases/35-improve-library-typing-using-best-practices-from-awesome-pyt/35-TYPING-EVIDENCE/35-120.md`.
- Evidence commit `68e1346` is present in Git history.
