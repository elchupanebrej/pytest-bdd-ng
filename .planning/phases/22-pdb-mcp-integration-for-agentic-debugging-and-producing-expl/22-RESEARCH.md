# Phase 22 Research: mcp-pdb integration for pytest-bdd-ng

**Date:** 2026-06-04
**Status:** Complete

## Scope

Research focused on how to implement Phase 22 without reimplementing debugger behavior:

- `mcp-pdb` dependency and public runtime surface
- pytest plugin lifecycle for holding setup/call/teardown failures
- pytest-bdd-ng metadata and artifact integration points
- xdist worker-local discovery and endpoint behavior

## Findings

### mcp-pdb dependency shape

`mcp-pdb` v0.6.0 is current and suitable as the dependency baseline for Phase 22. Its package metadata declares Python `>=3.10`, dependencies on `mcp[cli]>=1.6.0` and `remote-pdb>=2.1.0`, and console scripts:

- `mcp-pdb = mcp_pdb:main`
- `rpdb = mcp_pdb.rpdb:main`

The project README documents the key MCP tools: `start_debug`, `connect_remote_debug`, `send_pdb_command`, `set_breakpoint`, `clear_breakpoint`, `list_breakpoints`, `restart_debug`, `examine_variable`, `get_debug_status`, and `end_debug`.

Research source: `https://github.com/samefarrar/mcp-pdb`.

### Security constraint

`mcp-pdb` can execute Python through PDB. Phase 22 must default to local-only binding and document trusted-environment use. Public/non-local host binding should require explicit configuration and emit a warning.

### Public import/runtime API

The wheel exposes:

- `mcp_pdb.rpdb.set_trace(host="127.0.0.1", port=4444)`
- `mcp_pdb.rpdb.Debugger`, usable with `pytest --pdb --pdbcls=mcp_pdb.rpdb:Debugger`
- `mcp_pdb.rpdb.DualPdb`, used by the `rpdb` console script

`mcp_pdb.__init__` exports only `main`. The MCP tool functions live in `mcp_pdb.main` behind `@mcp.tool()` decorators, but this is not a stable extension API for pytest-bdd-ng to patch. Phase 22 should therefore treat `mcp-pdb` as:

- a remote-PDB endpoint dependency for live PDB state;
- a separate MCP server the agent can connect to;
- not a namespace to extend directly.

This supports the locked decision to implement pytest-bdd-ng helper tools as a sidecar MCP server.

### Remote PDB behavior

`rpdb` supports:

- `REMOTE_PDB_HOST`, default `127.0.0.1`
- `REMOTE_PDB_PORT`, default `4444`
- `REMOTE_PDB_ACCEPT_TIMEOUT`, default `600` seconds in v0.6.0
- in-source `from mcp_pdb.rpdb import set_trace; set_trace()`
- `PYTHONBREAKPOINT=mcp_pdb.rpdb.set_trace`
- Python 3.11+ `pytest --pdb --pdbcls=mcp_pdb.rpdb:Debugger`

For pytest-bdd-ng, direct `set_trace(host, port)` is the most practical per-failure entry point, but it blocks waiting for a remote client. Phase 22 must own timeout and hold semantics around that blocking point.

### pytest-bdd-ng integration points

Relevant local patterns:

- Plugin packages live under `src/pytest_bdd/plugin/`.
- CLI/config registration belongs in `pytest_addoption` and pytest ini options.
- Session state must use `Config.stash` through `StashBound`.
- Runtime BDD context is available through `Run`, `ScenarioRun`, and `FeatureRuntimeBinding`.
- Existing xdist worker identity helpers live in `src/pytest_bdd/util/live_reporting.py`.

No generic BDD artifact hook was found in source grep for `artifact`; planning should include a task to verify the hook name/user intent and either bridge to the existing hook if it exists outside grep coverage or add a narrow pytest-bdd-ng hook for debug investigation artifacts.

## Recommended plan shape

1. Scaffold pytest-only debug-MCP plugin, dependency extra, options, state, discovery.
2. Implement failure queue/hold lifecycle with adapter-isolated `mcp-pdb` calls.
3. Implement sidecar MCP helper server and strict artifact schema/sink.
4. Add pytest-bdd-ng BDD metadata enrichment and artifact hook bridge.
5. Add xdist worker-local discovery/holds and executable BDD/docs coverage.

## Risks

- `set_trace()` blocks; tests need fake adapter seams to avoid real hangs.
- Sidecar MCP server dependency/API must be chosen carefully to avoid coupling to `mcp-pdb.main` internals.
- xdist endpoint discovery can become flaky if root index writes are not file-lock protected.
- BDD metadata capture timing must happen before scenario teardown clears active runtime state.
