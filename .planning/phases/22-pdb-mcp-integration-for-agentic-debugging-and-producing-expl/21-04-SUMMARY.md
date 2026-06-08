---
phase: 21-pdb-mcp-integration-for-agentic-debugging-and-producing-expl
plan: 4
subsystem: testing
tags: [pytest-bdd, debug-mcp, bdd-metadata, hookspec, artifacts]
requires:
  - phase: 21-pdb-mcp-integration-for-agentic-debugging-and-producing-expl
    provides: 21-02 failure queue and 21-03 sidecar artifact writer
provides:
  - Best-effort BDD metadata extraction for held failures
  - Sidecar `get_bdd_context` metadata parity with active failure snapshots
  - Debug MCP artifact-created hookspec and hook emission
  - Artifact hook payloads with nodeid, phase, BDD metadata, paths, status, and summary
affects: [debug-mcp, pytest-bdd-runtime, artifacts, phase-20]
tech-stack:
  added: []
  patterns: [best-effort runtime extraction, narrow hookspec, validated artifact hook emission]
key-files:
  created:
    - src/pytest_bdd/plugin/debug_mcp/bdd_adapter.py
    - src/pytest_bdd/plugin/debug_mcp/hookspec.py
    - tests/cases/integration/debug_mcp/test_bdd_metadata_and_artifact_bridge.py
  modified:
    - src/pytest_bdd/plugin/debug_mcp/artifacts.py
    - src/pytest_bdd/plugin/debug_mcp/entrypoint.py
    - src/pytest_bdd/plugin/debug_mcp/hook.py
    - src/pytest_bdd/plugin/debug_mcp/sidecar.py
key-decisions:
  - "No generic artifact hook existed, so Plan 21-04 adds narrow `pytest_bdd_debug_mcp_artifact_created` hookspec."
  - "BDD metadata extraction returns null outside pytest-bdd-ng runtime instead of making plain pytest failures error-prone."
patterns-established:
  - "Held failures are enriched at report-hook time before scenario cleanup can clear active runtime state."
  - "Artifact hook fires only after strict schema validation and paired file writes succeed."
requirements-completed: [P21-BDD-01, P21-BDD-02]
duration: 60min
completed: 2026-06-05
---

# Phase 21 Plan 04 Summary

**BDD metadata snapshots and artifact hook bridge for debug MCP investigations**

## Performance

- **Duration:** 60 min
- **Started:** 2026-06-05T09:10:00Z
- **Completed:** 2026-06-05T10:10:00Z
- **Tasks:** 2
- **Files modified:** 7

## Accomplishments

- Added `BddContextExtractor` for feature path/name, scenario, step keyword/text, tags, and example breadcrumb metadata.
- Enriched queued failures through the debug MCP report hook before active scenario state is cleared.
- Added `pytest_bdd_debug_mcp_artifact_created` hookspec and registered it from the debug MCP entrypoint.
- Emitted artifact hook payloads after successful validation and paired JSON/Markdown writes.

## Task Commits

1. **Task 1: Extract best-effort BDD metadata for held failures** - `18c44b6d` (feat)
2. **Task 2: Bridge validated artifacts into BDD artifact hook** - `18c44b6d` (feat)

## Files Created/Modified

- `src/pytest_bdd/plugin/debug_mcp/bdd_adapter.py` - Best-effort BDD runtime metadata extraction and failure enrichment.
- `src/pytest_bdd/plugin/debug_mcp/hookspec.py` - Debug MCP artifact-created hook specification.
- `src/pytest_bdd/plugin/debug_mcp/hook.py` - Enriches queued failures with BDD metadata.
- `src/pytest_bdd/plugin/debug_mcp/entrypoint.py` - Registers debug MCP hookspecs.
- `src/pytest_bdd/plugin/debug_mcp/artifacts.py` - Emits artifact-created hook after successful writes.
- `src/pytest_bdd/plugin/debug_mcp/sidecar.py` - Accepts pluginmanager and bridges artifact writes to hooks.
- `tests/cases/integration/debug_mcp/test_bdd_metadata_and_artifact_bridge.py` - Metadata and hook bridge tests.

## Decisions Made

- Used a narrow debug-MCP-specific hook because repository search found no existing generic BDD artifact hook.
- Tested BDD extraction with controlled runtime doubles to keep this plan focused on metadata shape and bridge behavior.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## Verification

- `uv run python -m pytest tests/cases/integration/debug_mcp/test_bdd_metadata_and_artifact_bridge.py -q` - 5 passed.
- `uv run python -m pytest tests/cases/integration/debug_mcp -q` - 24 passed.
- `uv run ruff check src/pytest_bdd/plugin/debug_mcp tests/cases/integration/debug_mcp` - passed.
- `uv run --extra testtypes mypy src/pytest_bdd/plugin/debug_mcp` - passed.
- Pre-commit during `git commit` - passed.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

Plan 21-05 can add xdist worker discovery and executable BDD/docs coverage over the debug MCP workflow.

---
*Phase: 21-pdb-mcp-integration-for-agentic-debugging-and-producing-expl*
*Completed: 2026-06-05*
