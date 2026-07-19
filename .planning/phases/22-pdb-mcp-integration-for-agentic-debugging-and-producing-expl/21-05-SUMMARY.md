# Plan 21-05 Summary: xdist Worker Discovery and BDD Docs

## Delivered

- Added xdist-aware debug MCP discovery:
  - worker-local files under `.pytest_cache/mcp-pdb/workers/{workerid}.json`
  - root `.pytest_cache/mcp-pdb/session.json` worker index
  - root status aggregation that reports `holding_failure` when any worker is paused
  - worker-specific mcp-pdb and sidecar endpoint publication
- Routed failure-hold discovery writes through a queue writer callback so worker holds update both the worker file and root index.
- Preserved non-xdist behavior by keeping root `session.json` as the process-local discovery path outside workers.
- Added integration tests for non-xdist root discovery, multi-worker index creation, and independent worker failure holds.
- Added executable BDD docs for agentic debugging:
  - discovery enablement
  - setup/call/teardown holds
  - valid artifact writes
  - invalid artifact rejection
  - BDD metadata persistence
  - xdist root worker references
- Added generated RST docs and feature index entry.

## Verification

- `uv run python -m pytest tests/cases/integration/debug_mcp tests/cases/e2e/e2e/test_feature_065_debug_mcp.py -q`
- `uv run ruff check src/pytest_bdd/plugin/debug_mcp tests/cases/integration/debug_mcp tests/cases/e2e/steps_debug_mcp.py tests/cases/e2e/e2e/test_feature_065_debug_mcp.py`
- `uv run --extra testtypes mypy src/pytest_bdd/plugin/debug_mcp`
- `uv run pre-commit run --files src/pytest_bdd/plugin/debug_mcp/entrypoint.py src/pytest_bdd/plugin/debug_mcp/queue.py src/pytest_bdd/plugin/debug_mcp/xdist.py tests/cases/integration/debug_mcp/test_xdist_worker_discovery.py tests/cases/e2e/steps_debug_mcp.py tests/cases/e2e/e2e/test_feature_065_debug_mcp.py 'features/17 Debug MCP/01 Agentic debugging.feature.md' 'docs/features/17 Debug MCP/01 Agentic debugging.feature.rst' docs/features/features.rst`
