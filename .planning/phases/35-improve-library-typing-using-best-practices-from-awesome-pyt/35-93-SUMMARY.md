---
phase: 35-improve-library-typing-using-best-practices-from-awesome-pyt
plan: 93
subsystem: typing
tags: [mypy, strict-typing, ruff, external-tests]
requires: []
provides:
  - isolated strict-mypy evidence for the external Docker and xdist test slice
affects: [phase-35-typing-inventory]
tech-stack:
  added: []
  patterns:
    - local protocols for pytest APIs missing from project stubs
key-files:
  created:
    - .planning/phases/35-improve-library-typing-using-best-practices-from-awesome-pyt/35-TYPING-EVIDENCE/35-93.md
  modified:
    - src/pytest_bdd_toolchain/case/external/test_subprocess_output_attachments.py
    - src/pytest_bdd_toolchain/case/external/test_xdist_html_reporting.py
    - src/pytest_bdd_toolchain/case/external/test_xdist_message_aggregation.py
    - src/pytest_bdd_toolchain/case/external/test_xdist_remote_message_aggregation.py
key-decisions:
  - "Use narrow local protocols and casts at pytest's incomplete stub boundary instead of type ignores."
  - "Leave the checkout's broad pre-existing refactor outside this plan commit."
patterns-established:
  - "Focused typing plans record exact mypy commands and one disposition per source path."
requirements-completed: []
coverage:
  - id: D1
    description: "The five external Docker and xdist test modules pass focused strict mypy without type suppressions."
    verification:
      - kind: other
        ref: "uv run --all-extras mypy --config-file pyproject.toml src/pytest_bdd_toolchain/case/external/test_docker_wsl2.py src/pytest_bdd_toolchain/case/external/test_subprocess_output_attachments.py src/pytest_bdd_toolchain/case/external/test_xdist_html_reporting.py src/pytest_bdd_toolchain/case/external/test_xdist_message_aggregation.py src/pytest_bdd_toolchain/case/external/test_xdist_remote_message_aggregation.py"
        status: pass
    human_judgment: false
  - id: D2
    description: "The same source slice passes focused Ruff and has plan-owned evidence."
    verification:
      - kind: other
        ref: "uv run ruff check [five Plan 35-93 source paths]"
        status: pass
      - kind: other
        ref: ".planning/phases/35-improve-library-typing-using-best-practices-from-awesome-pyt/35-TYPING-EVIDENCE/35-93.md"
        status: pass
    human_judgment: false
duration: 35 min
completed: 2026-07-19
status: complete
---
# Phase 35 Plan 93: Strict typing for external Docker and xdist tests

**The five targeted external test modules are strict-mypy and Ruff clean after local pytest-stub boundary typing.**

## Accomplishments

- Added concrete pytest marker, raises, import-skip, and pytester protocol boundaries where local stubs were incomplete.
- Corrected the pytester option container annotation and removed two stale upstream-attribute type suppressions.
- Focused mypy passed with exit status 0, and focused Ruff passed with exit status 0.
- Committed isolated evidence as `6fec7dc`.

## Deviations from Plan

- The checkout contains a much larger pre-existing source and test refactor with repository-wide mypy and pylint failures. To avoid absorbing unrelated work, only the plan evidence was committed; the source fixes remain in that existing working-tree refactor.
- The repository-relative verifier could not resolve `pyproject.toml` through the active `rtk uv` wrapper, so verification used the same command with an absolute config path; the focused checks passed.
- The repository's installed pre-commit 2.17 could not parse the pinned `pre-commit-hooks v5` manifest, so the normal evidence commit used the temporary pre-commit 4.3.0 runtime established earlier without changing project dependencies.
- **Total deviations:** 3 environment/scope deviations; focused typing and lint verification passed.

## Next Phase Readiness

- Plan 35-93 is complete; Plan 35-94 is next in Phase 35.

## Self-Check: PASSED

- Evidence file exists at `.planning/phases/35-improve-library-typing-using-best-practices-from-awesome-pyt/35-TYPING-EVIDENCE/35-93.md`.
- Evidence commit `6fec7dc` is present in Git history.
