---
phase: 21-pdb-mcp-integration-for-agentic-debugging-and-producing-expl
plan: 3
subsystem: testing
tags: [pytest, debug-mcp, sidecar, artifacts, pydantic]
requires:
  - phase: 21-pdb-mcp-integration-for-agentic-debugging-and-producing-expl
    provides: 21-02 active failure queue and release lifecycle
provides:
  - In-process sidecar helper surface for active failure, heartbeat, release, artifact writing, and BDD context
  - Strict Pydantic investigation artifact schema
  - Paired JSON/Markdown artifact sink
  - Stable `failure-0001-{safe-nodeid}.json/md` filenames
affects: [debug-mcp, artifacts, phase-20]
tech-stack:
  added: []
  patterns: [Pydantic validation, paired artifact sink, in-process sidecar handler]
key-files:
  created:
    - src/pytest_bdd/plugin/debug_mcp/artifacts.py
    - src/pytest_bdd/plugin/debug_mcp/schemas.py
    - src/pytest_bdd/plugin/debug_mcp/sidecar.py
    - tests/cases/integration/debug_mcp/test_sidecar_and_artifacts.py
  modified:
    - src/pytest_bdd/plugin/debug_mcp/queue.py
key-decisions:
  - "Sidecar is implemented as a testable in-process handler layer first; socket/MCP server construction remains isolated for later expansion."
  - "Invalid artifact payloads return validation errors without creating directories or draft files."
patterns-established:
  - "Investigation artifacts must validate before any filesystem write."
  - "Artifact writes mark the active failure sequence so later release records report `artifact_status: written`."
requirements-completed: [P21-MCP-04, P21-MCP-07]
duration: 45min
completed: 2026-06-05
---

# Phase 21 Plan 03 Summary

**Sidecar helper surface with strict paired JSON/Markdown investigation artifacts**

## Performance

- **Duration:** 45 min
- **Started:** 2026-06-05T08:20:00Z
- **Completed:** 2026-06-05T09:05:00Z
- **Tasks:** 2
- **Files modified:** 5

## Accomplishments

- Added `DebugMcpSidecar` helper methods for `get_active_failure`, `heartbeat`, `release`, `write_investigation_artifact`, and `get_bdd_context`.
- Added strict Pydantic schemas for BDD metadata, active failures, and investigation artifacts.
- Added paired JSON/Markdown artifact writer with stable failure sequence filenames.
- Ensured invalid artifact payloads fail validation without writing files.

## Task Commits

1. **Task 1: Add sidecar helper surface** - `0dd4dfc2` (feat)
2. **Task 2: Add strict artifact schema and Markdown/JSON sink** - `0dd4dfc2` (feat)

## Files Created/Modified

- `src/pytest_bdd/plugin/debug_mcp/sidecar.py` - Sidecar helper API over queue and artifact sink.
- `src/pytest_bdd/plugin/debug_mcp/schemas.py` - Pydantic artifact and metadata schemas.
- `src/pytest_bdd/plugin/debug_mcp/artifacts.py` - JSON/Markdown artifact writer and slug helpers.
- `src/pytest_bdd/plugin/debug_mcp/queue.py` - Tracks artifact-written sequences for release records.
- `tests/cases/integration/debug_mcp/test_sidecar_and_artifacts.py` - Sidecar and artifact contract tests.

## Decisions Made

- Kept sidecar socket/server creation out of this plan; handlers are callable directly and ready for MCP transport binding.
- Kept BDD context `None` until Plan 21-04 adds pytest-bdd-ng metadata enrichment.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## Verification

- `uv run python -m pytest tests/cases/integration/debug_mcp/test_sidecar_and_artifacts.py -q` - 6 passed.
- `uv run python -m pytest tests/cases/integration/debug_mcp -q` - 19 passed.
- `uv run ruff check src/pytest_bdd/plugin/debug_mcp tests/cases/integration/debug_mcp` - passed.
- `uv run --extra testtypes mypy src/pytest_bdd/plugin/debug_mcp` - passed.
- Pre-commit during `git commit` - passed.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

Plan 21-04 can enrich active failure and artifacts with BDD metadata using the sidecar `get_bdd_context` and artifact schema fields.

---
*Phase: 21-pdb-mcp-integration-for-agentic-debugging-and-producing-expl*
*Completed: 2026-06-05*
