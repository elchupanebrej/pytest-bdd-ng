# Expose failed executable test state to agent

## Source

Captured from user request on 2026-06-04 via `gsd-capture --backlog`.

## Idea

Add a special step or hook that exposes internal state of an executable test, especially a failed test, to an agent.

## Motivation

When a test fails, agent should be able to inspect live failure state and continue investigation without losing state or immediately re-running the test.

## Possible Approach

- Add pytest/BDD hook integration around failed scenario/test execution.
- Preserve execution context, fixtures, locals, step state, and traceback details after failure.
- Expose that state through an MCP interface so agent can inspect it interactively.
- Investigate whether `samefarrar/mcp-pdb` can provide debugger-backed state access.

Reference: https://github.com/samefarrar/mcp-pdb

## Open Questions

- Should hook activate only on failures, or also on explicit debug steps?
- Should state exposure happen through PDB, pytest hooks, pytest-bdd step context, or a dedicated MCP server?
- What data can be exposed safely without leaking secrets from fixtures or environment?
- How should test process lifetime be managed while agent inspects state?

## Acceptance Sketch

- Failing executable test can pause or preserve debug session.
- Agent can query relevant scenario/test state without re-running test.
- User can opt in/out through config or marker.
- Normal test runs remain unchanged when feature is disabled.
