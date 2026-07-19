---
phase: 35-improve-library-typing-using-best-practices-from-awesome-pyt
plan: 42
subsystem: typing
tags: [mypy, strict-typing, struct-bdd, cucumber-messages]
requires: []
provides:
  - isolated strict-mypy evidence for five struct-BDD model modules
affects: [phase-35-typing-inventory]
tech-stack:
  added: []
  patterns:
    - "Use typed callable factories at untyped external message-constructor boundaries."
key-files:
  created:
    - .planning/phases/35-improve-library-typing-using-best-practices-from-awesome-pyt/35-TYPING-EVIDENCE/35-42.md
  modified:
    - src/pytest_bdd/plugin/struct_bdd/model/steps.py
    - src/pytest_bdd/plugin/struct_bdd/model_builder.py
key-decisions:
  - "Record evidence independently and leave the checkout's broad pre-existing refactor outside this plan commit."
  - "Use explicit callable factories for Cucumber message constructors because the upstream package lacks complete stubs."
patterns-established:
  - "Focused typing plans record exact mypy commands and one disposition per source path."
requirements-completed: []
coverage:
  - id: D1
    description: "The five struct-BDD modules pass focused strict mypy."
    verification:
      - kind: other
        ref: "uv run --all-extras mypy --config-file pyproject.toml src/pytest_bdd/plugin/struct_bdd/hook.py src/pytest_bdd/plugin/struct_bdd/model/__init__.py src/pytest_bdd/plugin/struct_bdd/model/base.py src/pytest_bdd/plugin/struct_bdd/model/steps.py src/pytest_bdd/plugin/struct_bdd/model_builder.py"
        status: pass
    human_judgment: false
  - id: D2
    description: "Plan-owned evidence records affected paths and typing dispositions."
    verification:
      - kind: other
        ref: ".planning/phases/35-improve-library-typing-using-best-practices-from-awesome-pyt/35-TYPING-EVIDENCE/35-42.md"
        status: pass
    human_judgment: false
duration: 25 min
completed: 2026-07-18
status: complete
---
# Phase 35 Plan 42: Strict-mypy evidence for struct BDD models

**The five struct-BDD hook/model modules pass focused strict mypy with explicit constructor boundaries and isolated evidence.**

## Accomplishments

- The exact five-module strict mypy check passed with exit status 0.
- Replaced the compatibility config import with the direct pytest type.
- Replaced dynamic step subclass construction suppression with a typed callable factory.
- Replaced missing Cucumber message stubs for `FeatureChild` and `Step` with typed local factories.
- Removed all type suppressions from the five target modules.
- Committed isolated evidence as `4242d18`.

## Deviations from Plan

- The checkout contains a much larger pre-existing source and test refactor with repository-wide mypy and pylint failures. To avoid absorbing unrelated work, only the plan evidence was committed; source fixes remain in that existing working-tree refactor.
- The repository-relative verifier could not resolve `pyproject.toml` through the active `rtk uv` wrapper, so verification used the same command with an absolute config path; the focused check passed.
- The repository's installed pre-commit 2.17 could not parse the pinned `pre-commit-hooks v5` manifest, so the normal evidence commit used the temporary pre-commit 4.3.0 runtime established earlier without changing project dependencies.
- **Total deviations:** 3 environment/scope deviations; focused verification passed.

## Next Phase Readiness

- Plan 35-42 is complete; Plan 35-43 is next in Phase 35.
