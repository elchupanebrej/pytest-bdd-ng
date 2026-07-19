---
phase: 35-improve-library-typing-using-best-practices-from-awesome-pyt
plan: 39
subsystem: typing
tags: [mypy, strict-typing, pickle-runner, pytest]
requires: []
provides:
  - isolated strict-mypy evidence for five pickle-runner plugin and transition modules
affects: [phase-35-typing-inventory]
tech-stack:
  added: []
  patterns:
    - "Use direct pytest types and focused local protocols or casts at dynamic runtime boundaries."
key-files:
  created:
    - .planning/phases/35-improve-library-typing-using-best-practices-from-awesome-pyt/35-TYPING-EVIDENCE/35-39.md
  modified:
    - src/pytest_bdd/plugin/pickle_runner/plugin/executor.py
    - src/pytest_bdd/plugin/pickle_runner/plugin/runner_plugin.py
    - src/pytest_bdd/plugin/pickle_runner/run_transitions.py
key-decisions:
  - "Record evidence independently and leave the checkout's broad pre-existing refactor outside this plan commit."
  - "Use non-overlapping per-file mypy invocations because the active refactor temporarily contains a module/package name collision."
  - "Replace existing typing suppressions with direct framework types, local protocols, and boundary casts."
patterns-established:
  - "Focused typing plans record exact mypy commands, structural verifier limitations, and one disposition per source path."
requirements-completed: []
coverage:
  - id: D1
    description: "The five pickle-runner plugin and transition modules pass focused strict mypy."
    verification:
      - kind: other
        ref: ".planning/phases/35-improve-library-typing-using-best-practices-from-awesome-pyt/35-TYPING-EVIDENCE/35-39.md"
        status: pass
    human_judgment: false
  - id: D2
    description: "Plan-owned evidence records affected paths and typing dispositions."
    verification:
      - kind: other
        ref: ".planning/phases/35-improve-library-typing-using-best-practices-from-awesome-pyt/35-TYPING-EVIDENCE/35-39.md"
        status: pass
    human_judgment: false
duration: 35 min
completed: 2026-07-18
status: complete
---
# Phase 35 Plan 39: Strict-mypy evidence for pickle runner plugin

**The five pickle-runner plugin and transition modules pass focused strict mypy through non-overlapping checks, with direct pytest types and explicit dynamic boundaries.**

## Accomplishments

- Resolved compatibility-layer typing failures by importing pytest framework types directly.
- Added a local protocol for pytest item fixture state and typed the dynamic stash/transition payload boundaries.
- Removed all `type: ignore` and `ignore_errors` suppressions from the five target modules.
- Verified all five files with exit-status-zero non-overlapping mypy commands.
- Committed isolated evidence as `fbd63c8`.

## Deviations from Plan

- The checkout contains a much larger pre-existing source and test refactor with repository-wide mypy and pylint failures. To avoid absorbing unrelated work, only the plan evidence was committed; source fixes remain in that existing working-tree refactor.
- The plan-specified combined mypy invocation cannot map both `pickle_runner/plugin.py` and `pickle_runner/plugin/__init__.py` simultaneously because they currently share the same dotted module name. The source paths were checked through non-overlapping invocations without exclusions or configuration changes.
- The repository's installed pre-commit 2.17 could not parse the pinned `pre-commit-hooks v5` manifest, so the normal evidence commit used the temporary pre-commit 4.3.0 runtime established earlier without changing project dependencies.
- **Total deviations:** 3 environment/scope deviations; focused per-file verification passed.

## Next Phase Readiness

- Plan 35-39 is complete; Plan 35-40 is next in Phase 35.
