---
phase: 21-pdb-mcp-integration-for-agentic-debugging-and-producing-expl
plan: 2
subsystem: testing
tags: [pytest, mcp-pdb, debug-mcp, failure-queue, heartbeat]
requires:
  - phase: 21-pdb-mcp-integration-for-agentic-debugging-and-producing-expl
    provides: 21-01 debug MCP plugin shell, options, session state, and discovery writer
provides:
  - Single-active-failure queue for setup/call/teardown pytest failures
  - Failure summary and release record models
  - Timeout, heartbeat lease, explicit release, and raw PDB continue release paths
  - Adapter-only `mcp-pdb` import seam
  - Integration tests for failure phases and hold lifecycle
affects: [debug-mcp, pytest-plugin, phase-20]
tech-stack:
  added: []
  patterns: [adapter seam, single-active queue, hookwrapper report capture]
key-files:
  created:
    - src/pytest_bdd/plugin/debug_mcp/failure.py
    - src/pytest_bdd/plugin/debug_mcp/mcp_pdb_adapter.py
    - src/pytest_bdd/plugin/debug_mcp/queue.py
    - tests/cases/integration/debug_mcp/test_failure_hold_lifecycle.py
  modified:
    - src/pytest_bdd/plugin/debug_mcp/discovery.py
    - src/pytest_bdd/plugin/debug_mcp/entrypoint.py
    - src/pytest_bdd/plugin/debug_mcp/hook.py
    - src/pytest_bdd/plugin/debug_mcp/state.py
key-decisions:
  - "The production adapter import is lazy via importlib so the optional `mcp-pdb` dependency remains isolated until enabled failure handling enters the adapter."
  - "Failure hook uses pytest report hookwrapper output and leaves capture mode unchanged."
patterns-established:
  - "Only `mcp_pdb_adapter.py` may import or load `mcp_pdb`."
  - "FailureQueue owns release state and discovery updates; pytest hooks only translate reports into queue entries."
requirements-completed: [P21-MCP-02, P21-MCP-05, P21-MCP-06]
duration: 55min
completed: 2026-06-05
---

# Phase 21 Plan 02 Summary

**Bounded pytest failure hold queue with adapter-isolated mcp-pdb entry**

## Performance

- **Duration:** 55 min
- **Started:** 2026-06-05T07:20:00Z
- **Completed:** 2026-06-05T08:15:00Z
- **Tasks:** 2
- **Files modified:** 8

## Accomplishments

- Added deterministic failure metadata for setup, call, and teardown failures.
- Added `FailureQueue` with no-client timeout, heartbeat lease expiry, explicit release, and raw PDB continue release support.
- Wired pytest report handling into debug MCP session state without changing pytest capture.
- Added `McpPdbAdapter` as sole `mcp_pdb` import boundary.

## Task Commits

1. **Task 1: Add queued failure model and report hook wiring** - `9a53df7e` (feat)
2. **Task 2: Implement timeout, heartbeat lease, release, and mcp-pdb adapter seam** - `9a53df7e` (feat)

## Files Created/Modified

- `src/pytest_bdd/plugin/debug_mcp/failure.py` - Failure summary, queued failure, and release record models.
- `src/pytest_bdd/plugin/debug_mcp/queue.py` - Single-active queue and release lifecycle logic.
- `src/pytest_bdd/plugin/debug_mcp/mcp_pdb_adapter.py` - Adapter seam for `mcp_pdb.rpdb.set_trace`.
- `src/pytest_bdd/plugin/debug_mcp/hook.py` - Report hookwrapper that queues failed setup/call/teardown reports.
- `src/pytest_bdd/plugin/debug_mcp/entrypoint.py` - Hook delegation and queue construction at session start.
- `src/pytest_bdd/plugin/debug_mcp/discovery.py` - Holding-failure discovery payload support.
- `src/pytest_bdd/plugin/debug_mcp/state.py` - Debug state now carries queue instance.
- `tests/cases/integration/debug_mcp/test_failure_hold_lifecycle.py` - Failure phase and lifecycle coverage.

## Decisions Made

- Kept queue tests fake-adapter based so integration tests never block on real PDB/MCP behavior.
- Used lazy `importlib.import_module("mcp_pdb.rpdb")` inside the adapter to preserve optional dependency boundaries.
- Stored BDD metadata as optional `None` for this plan, leaving enrichment to Plan 21-04.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## Verification

- `uv run python -m pytest tests/cases/integration/debug_mcp/test_failure_hold_lifecycle.py -q` - 6 passed.
- `uv run python -m pytest tests/cases/integration/debug_mcp/test_options_and_discovery.py tests/cases/integration/debug_mcp/test_failure_hold_lifecycle.py -q` - 13 passed.
- `uv run ruff check src/pytest_bdd/plugin/debug_mcp tests/cases/integration/debug_mcp/test_failure_hold_lifecycle.py` - passed.
- `uv run --extra testtypes mypy src/pytest_bdd/plugin/debug_mcp` - passed.
- Pre-commit during `git commit` - passed.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

Plan 21-03 can add sidecar MCP helpers and artifact writing on top of active failure metadata, release records, and discovery status.

---
*Phase: 21-pdb-mcp-integration-for-agentic-debugging-and-producing-expl*
*Completed: 2026-06-05*
