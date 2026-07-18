---
phase: 35-improve-library-typing-using-best-practices-from-awesome-pyt
plan: 70
subsystem: typing
tags: [mypy, strict-typing, contract-tests, messages-coverage]
requires: []
provides:
  - isolated strict-mypy evidence for message-coverage runtime and governance tests
affects: [phase-35-typing-inventory]
tech-stack:
  added: []
  patterns:
    - "Preserve intentionally unhashable test helper classes with post-class runtime assignment when direct __hash__ typing conflicts with object."
key-files:
  created:
    - .planning/phases/35-improve-library-typing-using-best-practices-from-awesome-pyt/35-TYPING-EVIDENCE/35-70.md
  modified:
    - src/pytest_bdd_toolchain/case/contract/messages_coverage/test_mandatory_attachments.py
key-decisions:
  - "Remove the coordinate helper's __hash__ suppression while preserving its runtime contract through setattr."
  - "Record evidence independently and leave the checkout's broad pre-existing refactor outside this plan commit."
patterns-established:
  - "Focused typing plans record exact mypy commands and one disposition per source path."
requirements-completed: []
coverage:
  - id: D1
    description: "The five message-coverage runtime and governance modules pass focused strict mypy."
    verification:
      - kind: other
        ref: "uv run --all-extras mypy --config-file pyproject.toml src/pytest_bdd_toolchain/case/contract/messages_coverage/probes/test_parse_error_runtime.py src/pytest_bdd_toolchain/case/contract/messages_coverage/probes/test_undefined_parameter_runtime.py src/pytest_bdd_toolchain/case/contract/messages_coverage/test_full_capability_governance.py src/pytest_bdd_toolchain/case/contract/messages_coverage/test_mandatory_attachments.py src/pytest_bdd_toolchain/case/contract/messages_coverage/test_run_governance_regression.py"
        status: pass
    human_judgment: false
  - id: D2
    description: "Plan-owned evidence records affected paths and typing dispositions."
    verification:
      - kind: other
        ref: ".planning/phases/35-improve-library-typing-using-best-practices-from-awesome-pyt/35-TYPING-EVIDENCE/35-70.md"
        status: pass
    human_judgment: false
duration: 20 min
completed: 2026-07-18
status: complete
---
# Phase 35 Plan 70: Strict-mypy evidence for coverage tests

**The five message-coverage runtime and governance modules pass focused strict mypy without target-slice suppressions.**

## Accomplishments

- The exact five-module strict mypy check passed with exit status 0.
- Removed the coordinate helper's stale `__hash__` suppression while preserving unhashability.
- Confirmed the target slice contains no typing suppressions and committed isolated evidence as `5b2b1f4`.

## Deviations from Plan

- The checkout contains a much larger pre-existing source and test refactor with repository-wide mypy and pylint failures. To avoid absorbing unrelated work, only the plan evidence was committed; source fixes remain in that existing working-tree refactor.
- The repository-relative verifier could not resolve `pyproject.toml` through the active `rtk uv` wrapper, so verification used the same command with an absolute config path; the focused check passed.
- The repository's installed pre-commit 2.17 could not parse the pinned `pre-commit-hooks v5` manifest, so the normal evidence commit used the temporary pre-commit 4.3.0 runtime established earlier without changing project dependencies.
- **Total deviations:** 3 environment/scope deviations; focused verification passed.

## Next Phase Readiness

- Plan 35-70 is complete; Plan 35-71 is next in Phase 35.
