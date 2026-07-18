---
phase: 35-improve-library-typing-using-best-practices-from-awesome-pyt
plan: 48
subsystem: typing
tags: [mypy, strict-typing, steps, pytest]
requires: []
provides:
  - isolated strict-mypy evidence for five step and validation modules
affects: [phase-35-typing-inventory]
tech-stack:
  added: []
  patterns:
    - "Use typed local adapters for dynamic pytest fixture decorators and converter calls."
key-files:
  created:
    - .planning/phases/35-improve-library-typing-using-best-practices-from-awesome-pyt/35-TYPING-EVIDENCE/35-48.md
  modified:
    - src/pytest_bdd/steps/definition.py
    - src/pytest_bdd/steps/manager.py
key-decisions:
  - "Record evidence independently and leave the checkout's broad pre-existing refactor outside this plan commit."
  - "Use direct pytest types, a typed fixture decorator adapter, and an explicit converter helper instead of suppressions."
patterns-established:
  - "Focused typing plans record exact mypy commands and one disposition per source path."
requirements-completed: []
coverage:
  - id: D1
    description: "The five step and validation modules pass focused strict mypy."
    verification:
      - kind: other
        ref: "uv run --all-extras mypy --config-file pyproject.toml src/pytest_bdd/script/validate_feature_headings.py src/pytest_bdd/steps/__init__.py src/pytest_bdd/steps/decorators.py src/pytest_bdd/steps/definition.py src/pytest_bdd/steps/manager.py"
        status: pass
    human_judgment: false
  - id: D2
    description: "Plan-owned evidence records affected paths and typing dispositions."
    verification:
      - kind: other
        ref: ".planning/phases/35-improve-library-typing-using-best-practices-from-awesome-pyt/35-TYPING-EVIDENCE/35-48.md"
        status: pass
    human_judgment: false
duration: 25 min
completed: 2026-07-18
status: complete
---
# Phase 35 Plan 48: Strict-mypy evidence for steps

**The five step and validation modules pass focused strict mypy with direct pytest types and explicit dynamic boundaries.**

## Accomplishments

- The exact five-module strict mypy check passed with exit status 0.
- Replaced compatibility pytest imports with direct `Config` and `FixtureRequest` types.
- Replaced the dynamic fixture decorator suppression with a typed local decorator adapter.
- Replaced the converter-call suppression with an explicit typed converter helper.
- Committed isolated evidence as `977cb06`.

## Deviations from Plan

- The checkout contains a much larger pre-existing source and test refactor with repository-wide mypy and pylint failures. To avoid absorbing unrelated work, only the plan evidence was committed; source fixes remain in that existing working-tree refactor.
- The repository-relative verifier could not resolve `pyproject.toml` through the active `rtk uv` wrapper, so verification used the same command with an absolute config path; the focused check passed.
- The repository's installed pre-commit 2.17 could not parse the pinned `pre-commit-hooks v5` manifest, so the normal evidence commit used the temporary pre-commit 4.3.0 runtime established earlier without changing project dependencies.
- **Total deviations:** 3 environment/scope deviations; focused verification passed.

## Next Phase Readiness

- Plan 35-48 is complete; Plan 35-49 is next in Phase 35.
