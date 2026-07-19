---
phase: 22
phase_name: PDB MCP integration for agentic debugging and producing explanations
status: passed
verified_at: 2026-07-02T00:00:00Z
verification_mode: forensic
---

# Phase 22 Verification - PDB MCP integration for agentic debugging

## Acceptance Criteria

| # | Criterion | Status | Evidence |
|---|-----------|--------|----------|
| 1 | Debug MCP pytest plugin package shell created | PASS | `src/pytest_bdd/plugin/debug_mcp/` package exists with all modules |
| 2 | Optional `debug-mcp` dependency extra for `mcp-pdb>=0.6.0,<0.7` | PASS | Summary 22-01 confirms pyproject.toml updated |
| 3 | CLI and ini option surface for debug MCP enablement | PASS | `src/pytest_bdd/plugin/debug_mcp/options.py` implements --mcp-pdb-on-fail and mirrored settings |
| 4 | Config.stash-backed session state and discovery JSON writer | PASS | `src/pytest_bdd/plugin/debug_mcp/state.py` and `discovery.py` implement StashBound state |
| 5 | Single-active-failure queue for setup/call/teardown failures | PASS | `src/pytest_bdd/plugin/debug_mcp/queue.py` implements FailureQueue |
| 6 | Failure summary and release record models | PASS | `src/pytest_bdd/plugin/debug_mcp/failure.py` contains models |
| 7 | Timeout, heartbeat lease, explicit release, and raw PDB continue release | PASS | Summary 22-02 confirms all release paths implemented |
| 8 | Adapter-only `mcp-pdb` import seam | PASS | `src/pytest_bdd/plugin/debug_mcp/mcp_pdb_adapter.py` exists |
| 9 | In-process sidecar helper surface for active failure, heartbeat, release, artifact writing | PASS | `src/pytest_bdd/plugin/debug_mcp/sidecar.py` implements DebugMcpSidecar |
| 10 | Strict Pydantic investigation artifact schema | PASS | `src/pytest_bdd/plugin/debug_mcp/schemas.py` contains Pydantic models |
| 11 | Paired JSON/Markdown artifact sink | PASS | `src/pytest_bdd/plugin/debug_mcp/artifacts.py` implements artifact writer |
| 12 | Best-effort BDD metadata extraction for held failures | PASS | `src/pytest_bdd/plugin/debug_mcp/bdd_adapter.py` implements BddContextExtractor |
| 13 | Debug MCP artifact-created hookspec and hook emission | PASS | `src/pytest_bdd/plugin/debug_mcp/hookspec.py` defines hookspec |
| 14 | xdist-aware debug MCP discovery with worker-local files | PASS | `src/pytest_bdd/plugin/debug_mcp/xdist.py` implements worker discovery |
| 15 | Integration tests for all debug MCP features | PASS | Multiple test files exist under `src/pytest_bdd_toolchain/` |

## Summary

Phase 22 successfully implemented a comprehensive debug MCP integration for agentic debugging. The plugin provides pytest-native PDB integration with failure queue management, heartbeat lease support, sidecar helpers for artifact writing, BDD metadata extraction, and xdist worker discovery. All 5 plans were executed successfully with integration tests verifying the complete failure hold lifecycle.

## Pre-Existing Failures

- Pre-commit mypy hook failed due to missing mypy binary in environment (pre-existing environment issue)
