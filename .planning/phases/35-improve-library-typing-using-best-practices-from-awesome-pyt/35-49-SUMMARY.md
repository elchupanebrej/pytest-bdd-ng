---
phase: 35-improve-library-typing-using-best-practices-from-awesome-pyt
plan: 49
subsystem: typing
tags: [mypy, strict-typing, steps, types]
requires: []
provides:
  - isolated strict-mypy evidence for five step and type modules
affects: [phase-35-typing-inventory]
tech-stack:
  added: []
  patterns:
    - "Use dynamic member lookup for extended runtime enums whose upstream stubs omit members."
key-files:
  created:
    - .planning/phases/35-improve-library-typing-using-best-practices-from-awesome-pyt/35-TYPING-EVIDENCE/35-49.md
  modified:
    - src/pytest_bdd/steps/matcher.py
key-decisions:
  - "Record evidence independently and leave the checkout's broad pre-existing refactor outside this plan commit."
  - "Use direct pytest types and dynamic enum-member lookup instead of type suppressions."
patterns-established:
  - "Focused typing plans record exact mypy commands and one disposition per source path."
requirements-completed: []
coverage:
  - id: D1
    description: "The five step and type modules pass focused strict mypy."
    verification:
      - kind: other
        ref: "uv run --all-extras mypy --config-file pyproject.toml src/pytest_bdd/steps/matcher.py src/pytest_bdd/steps/registry.py src/pytest_bdd/template/__init__.py src/pytest_bdd/types/__init__.py src/pytest_bdd/types/exception.py"
        status: pass
    human_judgment: false
  - id: D2
    description: "Plan-owned evidence records affected paths and typing dispositions."
    verification:
      - kind: other
        ref: ".planning/phases/35-improve-library-typing-using-best-practices-from-awesome-pyt/35-TYPING-EVIDENCE/35-49.md"
        status: pass
    human_judgment: false
duration: 25 min
completed: 2026-07-18
status: complete
---
# Phase 35 Plan 49: Strict-mypy evidence for step matching

**The five step and type modules pass focused strict mypy with direct pytest types, dynamic enum boundaries, and isolated evidence.**

## Accomplishments

- The exact five-module strict mypy check passed with exit status 0.
- Replaced compatibility pytest imports with direct `Config` and `FixtureRequest` types.
- Replaced upstream/extended enum-member suppressions with explicit dynamic member lookup.
- Committed isolated evidence as `f9d8705`.

## Deviations from Plan

- The checkout contains a much larger pre-existing source and test refactor with repository-wide mypy and pylint failures. To avoid absorbing unrelated work, only the plan evidence was committed; source fixes remain in that existing working-tree refactor.
- The repository-relative verifier could not resolve `pyproject.toml` through the active `rtk uv` wrapper, so verification used the same command with an absolute config path; the focused check passed.
- The repository's installed pre-commit 2.17 could not parse the pinned `pre-commit-hooks v5` manifest, so the normal evidence commit used the temporary pre-commit 4.3.0 runtime established earlier without changing project dependencies.
- **Total deviations:** 3 environment/scope deviations; focused verification passed.

## Next Phase Readiness

- Plan 35-49 is complete; Plan 35-50 is next in Phase 35.
