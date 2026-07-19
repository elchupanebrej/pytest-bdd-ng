---
phase: 35-improve-library-typing-using-best-practices-from-awesome-pyt
plan: 122
subsystem: typing
tags: [mypy, strict-typing, unit-tests, steps, unicode]
requires: []
provides:
  - isolated strict-mypy evidence for step policy, step execution, Unicode, and stub unit tests
affects: [phase-35-typing-inventory]
tech-stack:
  added: []
  patterns: []
key-files:
  created:
    - .planning/phases/35-improve-library-typing-using-best-practices-from-awesome-pyt/35-TYPING-EVIDENCE/35-122.md
  modified:
    - src/pytest_bdd_toolchain/case/unit/test_steps_unicode.py
key-decisions:
  - "Replace Unicode lint suppressions with equivalent escape-based fixture literals while preserving generated runtime text."
  - "Leave the checkout's broad pre-existing refactor outside this plan commit."
patterns-established:
  - "Focused typing plans record exact mypy commands and one disposition per source path."
requirements-completed: []
coverage:
  - id: D1
    description: "The five step policy, step execution, Unicode, and stub unit-test modules pass focused strict mypy."
    verification:
      - kind: other
        ref: "uv run --all-extras mypy --config-file pyproject.toml src/pytest_bdd_toolchain/case/unit/test_step_policy_decorators.py src/pytest_bdd_toolchain/case/unit/test_steps.py src/pytest_bdd_toolchain/case/unit/test_steps_given.py src/pytest_bdd_toolchain/case/unit/test_steps_unicode.py src/pytest_bdd_toolchain/case/unit/test_stubs.py"
        status: pass
    human_judgment: false
  - id: D2
    description: "Plan-owned evidence records affected paths and typing dispositions without suppressions."
    verification:
      - kind: other
        ref: ".planning/phases/35-improve-library-typing-using-best-practices-from-awesome-pyt/35-TYPING-EVIDENCE/35-122.md"
        status: pass
    human_judgment: false
  - id: D3
    description: "The modified Unicode test fixtures retain runtime behavior."
    verification:
      - kind: other
        ref: "uv run pytest -q src/pytest_bdd_toolchain/case/unit/test_steps_unicode.py"
        status: pass
    human_judgment: false
duration: 25 min
completed: 2026-07-19
status: complete
---
# Phase 35 Plan 122: Strict-mypy evidence for step and Unicode tests

**The five targeted step policy, step execution, Unicode, and stub unit-test modules pass focused strict mypy and Ruff after replacing three Unicode noqa comments with equivalent escaped fixtures.**

## Accomplishments

- The exact five-module strict mypy check passed with exit status 0.
- Replaced three active Unicode `noqa` comments with equivalent `\u` fixture escapes.
- The affected Unicode module passed its focused runtime check: 2 passed, 85 skipped.
- Focused Ruff passed and the target slice contains no suppression comments.
- Committed isolated evidence as `2fd9a68`.

## Deviations from Plan

- The checkout contains a much larger pre-existing source and test refactor with repository-wide mypy and pylint failures. To avoid absorbing unrelated work, only the plan evidence was committed; source fixes remain in that existing working-tree refactor.
- The repository-relative verifier could not resolve `pyproject.toml` through the active `rtk uv` wrapper, so verification used the same command with an absolute config path; the focused check passed.
- The repository's installed pre-commit 2.17 could not parse the pinned `pre-commit-hooks v5` manifest, so the normal evidence commit used the temporary pre-commit 4.3.0 runtime established earlier without changing project dependencies.
- **Total deviations:** 3 environment/scope deviations; focused verification passed.

## Next Phase Readiness

- Plan 35-122 is complete; Plan 35-123 is next in Phase 35.

## Self-Check: PASSED

- Evidence file exists at `.planning/phases/35-improve-library-typing-using-best-practices-from-awesome-pyt/35-TYPING-EVIDENCE/35-122.md`.
- Evidence commit `2fd9a68` is present in Git history.
