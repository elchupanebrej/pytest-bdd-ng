---
phase: 35-improve-library-typing-using-best-practices-from-awesome-pyt
plan: "07"
subsystem: model
tags: [mypy, typing, cucumber-messages]
requires:
  - phase: 35
    provides: strict no-bypass mypy baseline
provides:
  - isolated strict-mypy evidence for the model source slice
affects: [35-140-PLAN.md]
tech-stack:
  added: []
  patterns: [local protocol for untyped upstream model]
key-files:
  created:
    - .planning/phases/35-improve-library-typing-using-best-practices-from-awesome-pyt/35-TYPING-EVIDENCE/35-07.md
  modified:
    - src/pytest_bdd/model/feature_binding.py
key-decisions:
  - "Use a local protocol only for the Step attributes consumed by FeatureRuntimeBinding."
requirements-completed: []
coverage: []
completed: 2026-07-14
status: complete
---

# Phase 35 Plan 07: Model Typing Slice Summary

**The five targeted model modules are strict-mypy clean, with an isolated typed boundary for the untyped upstream `Step` class.**

## Performance

- **Tasks:** 1 completed
- **Files modified:** 3

## Accomplishments

- Added a local `GherkinStep` protocol at the cucumber-message boundary, preserving runtime `Step` detection while exposing only the required attributes.
- Verified the remaining four modules required no code changes.
- Recorded the exact focused command and its result in plan-owned evidence; the shared inventory was not changed.

## Task Commits

1. **Task 1: Remediate the exact strict-typing source slice** — pending

## Verification

- Passed: `uv run --all-extras mypy --config-file pyproject.toml src/pytest_bdd/model/execution_message_reader.py src/pytest_bdd/model/feature_binding.py src/pytest_bdd/model/heading_validation.py src/pytest_bdd/model/message_baseline_diff.py src/pytest_bdd/model/message_capability.py`
- Passed: no `type: ignore`, mypy-file directive, or `ignore_errors` bypass occurs in the five source modules.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## Next Phase Readiness

The final Phase 35 aggregation plan can consume `35-TYPING-EVIDENCE/35-07.md` without a concurrent shared-inventory write.

## Self-Check: PASSED
