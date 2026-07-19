---
title: Phase 20 debug MCP architecture
date: 2026-06-04
context: Exploration session — Phase 20 pdb MCP integration for agentic debugging
---

## Decisions

Phase 20 adds two layers:

- Plain pytest debug-MCP layer, implemented inside pytest-bdd-ng for now and designed for later extraction.
- pytest-bdd-ng adapter layer, enriching plain pytest failures with BDD metadata and artifact hooks.

`mcp-pdb` is a required runtime dependency for the enabled feature, not an inspiration to reimplement. The project should depend on it through an optional extra and wrap its PDB/MCP functionality with a narrow adapter.

The MCP service starts at pytest session start. Failed tests enter a single-item queue and expose live failed-process state to an agent through `mcp-pdb`. The failed pytest process stays alive while waiting for an MCP client.

Lifecycle ownership:

- pytest owns the no-client timeout.
- a babysitting agent owns spawned debug-agent lifecycle when used.
- connected debug sessions use heartbeat leases; missed heartbeat closes MCP handling and lets pytest continue.
- if no MCP client connects before timeout, MCP shuts down for that failure and the test run continues.

Queue entries expose nodeid, exception type/message, and BDD metadata. BDD metadata should include feature path/name, scenario name, step keyword/text, tags, example row, and generated pytest nodeid when available.

Agent completion accepts either an explicit release command or raw PDB `continue`; explicit release is preferred.

## CLI and Config

Main enable option:

- `--mcp-pdb-on-fail`
- `mcp_pdb_on_fail = true`

Supporting options:

- `--mcp-pdb-timeout=30`
- `mcp_pdb_timeout = 30`
- `--mcp-pdb-lease=60`
- `mcp_pdb_lease = 60`
- `--mcp-pdb-artifacts=PATH`
- `mcp_pdb_artifacts = .pytest_cache/mcp-pdb/artifacts`
- `--mcp-pdb-host=127.0.0.1`
- `mcp_pdb_host = 127.0.0.1`
- `--mcp-pdb-port=PORT`
- `mcp_pdb_port = PORT`

Port policy: configured port uses fixed port. Missing port binds a free auto port.

Discovery uses both terminal output and `.pytest_cache/mcp-pdb/session.json`. The session file includes host, port, session id, status, and active failure summary.

## Artifacts

Plain pytest has no generic first-class artifact attachment API. The pytest layer should therefore use a plugin-owned output directory and may attach paths through report properties when supported by configured reporters.

The pytest-bdd-ng layer should map agent-produced Markdown and JSON investigation artifacts into the existing BDD run artifact hook.
