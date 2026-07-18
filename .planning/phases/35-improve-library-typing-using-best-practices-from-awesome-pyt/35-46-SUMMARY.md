---
phase: 35-improve-library-typing-using-best-practices-from-awesome-pyt
plan: 46
subsystem: typing
tags: [mypy, strict-typing, message-capability-governance, cli]
requires: []
provides:
  - isolated strict-mypy evidence for five message-governance CLI modules
affects: [phase-35-typing-inventory]
tech-stack:
  added: []
  patterns:
    - "Annotate JSON report payloads at construction boundaries."
key-files:
  created:
    - .planning/phases/35-improve-library-typing-using-best-practices-from-awesome-pyt/35-TYPING-EVIDENCE/35-46.md
  modified:
    - src/pytest_bdd/script/message_capability_governance/cli/_report.py
key-decisions:
  - "Record evidence independently and leave the checkout's broad pre-existing refactor outside this plan commit."
  - "Type report payloads as JSONObject at construction rather than suppressing list insertion incompatibilities."
patterns-established:
  - "Focused typing plans record exact mypy commands and one disposition per source path."
requirements-completed: []
coverage:
  - id: D1
    description: "The five message-governance CLI modules pass focused strict mypy."
    verification:
      - kind: other
        ref: "uv run --all-extras mypy --config-file pyproject.toml src/pytest_bdd/script/message_capability_governance/capabilities.py src/pytest_bdd/script/message_capability_governance/cli/__init__.py src/pytest_bdd/script/message_capability_governance/cli/_argparse.py src/pytest_bdd/script/message_capability_governance/cli/_core.py src/pytest_bdd/script/message_capability_governance/cli/_report.py"
        status: pass
    human_judgment: false
  - id: D2
    description: "Plan-owned evidence records affected paths and typing dispositions."
    verification:
      - kind: other
        ref: ".planning/phases/35-improve-library-typing-using-best-practices-from-awesome-pyt/35-TYPING-EVIDENCE/35-46.md"
        status: pass
    human_judgment: false
duration: 20 min
completed: 2026-07-18
status: complete
---
# Phase 35 Plan 46: Strict-mypy evidence for governance CLI

**The five message-governance CLI modules pass focused strict mypy with explicit JSON payload typing and isolated evidence.**

## Accomplishments

- The exact five-module strict mypy check passed with exit status 0.
- Replaced the report payload insertion suppression with an explicit `JSONObject` annotation.
- Confirmed the remaining governance CLI modules are clean under focused strict mypy.
- Committed isolated evidence as `8b92c77`.

## Deviations from Plan

- The checkout contains a much larger pre-existing source and test refactor with repository-wide mypy and pylint failures. To avoid absorbing unrelated work, only the plan evidence was committed; source fixes remain in that existing working-tree refactor.
- The repository-relative verifier could not resolve `pyproject.toml` through the active `rtk uv` wrapper, so verification used the same command with an absolute config path; the focused check passed.
- The repository's installed pre-commit 2.17 could not parse the pinned `pre-commit-hooks v5` manifest, so the normal evidence commit used the temporary pre-commit 4.3.0 runtime established earlier without changing project dependencies.
- **Total deviations:** 3 environment/scope deviations; focused verification passed.

## Next Phase Readiness

- Plan 35-46 is complete; Plan 35-47 is next in Phase 35.
