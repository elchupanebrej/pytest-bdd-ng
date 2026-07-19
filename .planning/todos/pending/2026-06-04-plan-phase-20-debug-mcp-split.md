---
title: Plan Phase 20 debug MCP split
date: 2026-06-04
priority: high
---

## Task

Break Phase 20 into implementation plans for agentic `mcp-pdb` debugging and pytest-bdd-ng artifact integration.

## Required Planning Slices

- Plain pytest plugin surface: CLI/config options, pytest session startup, failure interception, and report/property behavior.
- `mcp-pdb` adapter: dependency boundary, remote debug session startup, command/release handling, and import/runtime contracts.
- Failure queue and leases: single active failed test, no-client timeout, heartbeat lease, cleanup, and continuation.
- Session discovery: terminal connect line and `.pytest_cache/mcp-pdb/session.json`.
- Plain pytest artifacts: configurable artifact root, Markdown and JSON investigation files, optional reporter links.
- pytest-bdd-ng adapter: BDD metadata enrichment, framework hooks/primitives, and BDD artifact hook integration.
- Tests: plain pytest behavior first, then pytest-bdd-ng enrichment and artifact bridge.

## Acceptance Notes

Keep plain pytest layer in this repository for now, but maintain a boundary that allows later extraction to a separate pytest plugin.
