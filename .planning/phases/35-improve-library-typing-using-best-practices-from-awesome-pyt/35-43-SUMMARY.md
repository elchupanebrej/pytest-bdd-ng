---
phase: 35-improve-library-typing-using-best-practices-from-awesome-pyt
plan: 43
subsystem: typing
tags: [mypy, strict-typing, struct-bdd, test-group-ordering, pytest]
requires: []
provides:
  - isolated strict-mypy evidence for five struct-BDD and test-group-ordering modules
affects: [phase-35-typing-inventory]
tech-stack:
  added: []
  patterns:
    - "Use direct pytest types and typed adapters for dynamic loaders or framework payloads."
key-files:
  created:
    - .planning/phases/35-improve-library-typing-using-best-practices-from-awesome-pyt/35-TYPING-EVIDENCE/35-43.md
  modified:
    - src/pytest_bdd/plugin/struct_bdd/parser.py
    - src/pytest_bdd/plugin/struct_bdd/plugin.py
key-decisions:
  - "Record evidence independently and leave the checkout's broad pre-existing refactor outside this plan commit."
  - "Use dynamic import and callable adapters for optional YAML/JSON loaders instead of import or argument suppressions."
  - "Use a focused protocol for pytest module payloads whose public type omits the runtime module attribute."
patterns-established:
  - "Focused typing plans record exact mypy commands and one disposition per source path."
requirements-completed: []
coverage:
  - id: D1
    description: "The five struct-BDD and test-group-ordering modules pass focused strict mypy."
    verification:
      - kind: other
        ref: "uv run --all-extras mypy --config-file pyproject.toml src/pytest_bdd/plugin/struct_bdd/parser.py src/pytest_bdd/plugin/struct_bdd/plugin.py src/pytest_bdd/plugin/test_group_ordering/entrypoint.py src/pytest_bdd/plugin/test_group_ordering/hook.py src/pytest_bdd/plugin/test_group_ordering/plugin.py"
        status: pass
    human_judgment: false
  - id: D2
    description: "Plan-owned evidence records affected paths and typing dispositions."
    verification:
      - kind: other
        ref: ".planning/phases/35-improve-library-typing-using-best-practices-from-awesome-pyt/35-TYPING-EVIDENCE/35-43.md"
        status: pass
    human_judgment: false
duration: 35 min
completed: 2026-07-18
status: complete
---
# Phase 35 Plan 43: Strict-mypy evidence for struct BDD and group ordering

**The five struct-BDD and test-group-ordering modules pass focused strict mypy with explicit loader/module boundaries and isolated evidence.**

## Accomplishments

- The exact five-module strict mypy check passed with exit status 0.
- Replaced compatibility pytest types with direct public pytest types.
- Replaced dynamic pytest module attribute suppressions with a focused protocol and cast.
- Replaced YAML import and JSON kwargs suppressions with typed dynamic loader adapters.
- Removed all type suppressions from the five target modules.
- Committed isolated evidence as `4ecfbfb`.

## Deviations from Plan

- The checkout contains a much larger pre-existing source and test refactor with repository-wide mypy and pylint failures. To avoid absorbing unrelated work, only the plan evidence was committed; source fixes remain in that existing working-tree refactor.
- The repository-relative verifier could not resolve `pyproject.toml` through the active `rtk uv` wrapper, so verification used the same command with an absolute config path; the focused check passed.
- The repository's installed pre-commit 2.17 could not parse the pinned `pre-commit-hooks v5` manifest, so the normal evidence commit used the temporary pre-commit 4.3.0 runtime established earlier without changing project dependencies.
- **Total deviations:** 3 environment/scope deviations; focused verification passed.

## Next Phase Readiness

- Plan 35-43 is complete; Plan 35-44 is next in Phase 35.
