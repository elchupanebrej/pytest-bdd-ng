# Phase 22: pdb mcp integration for agentic debugging and producing explicit test artifacts - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-06-04
**Phase:** 21-pdb-mcp-integration-for-agentic-debugging-and-producing-explicit-test-artifacts
**Areas discussed:** Failure Hold Semantics, Agent Control Surface, Artifact Contract, xdist/Parallel Boundary

---

## Failure Hold Semantics

| Option | Description | Selected |
|--------|-------------|----------|
| Call only | Step/test body failures only. Cleaner; setup/teardown failures stay normal pytest failures. | |
| Setup + call | Includes fixture/setup failures. More useful; BDD step context may be absent. | |
| Setup + call + teardown | Captures all pytest phases; teardown holds can be noisy and late. | ✓ |

**User's choice:** Setup + call + teardown.
**Notes:** User wants all pytest failure phases held for MCP debugging.

| Option | Description | Selected |
|--------|-------------|----------|
| Scenario-level only | Feature/scenario/tags/examples, with `step=null`. | |
| Synthetic phase step | Step text like `<setup>` or `<teardown>`. | |
| Best-effort | Scenario-level metadata if known; plain pytest nodeid + exception if not. | ✓ |

**User's choice:** Best-effort metadata.
**Notes:** Setup/teardown failures may not have active BDD step context.

| Option | Description | Selected |
|--------|-------------|----------|
| Leave capture alone | Agent inspects process/PDB only; pytest output remains normal. | ✓ |
| Expose capture snapshot | Queue metadata includes current stdout/stderr if pytest provides it. | |
| Disable capture in debug hold | Closer to interactive debugging, noisier output. | |

**User's choice:** Leave capture alone.
**Notes:** No captured stdout/stderr snapshot in v1 queue metadata.

---

## Agent Control Surface

| Option | Description | Selected |
|--------|-------------|----------|
| Lifecycle only | `get_active_failure`, `heartbeat`, `release`. | |
| Lifecycle + artifacts | Lifecycle helpers plus `write_investigation_artifact`. | |
| Lifecycle + artifacts + BDD metadata | Lifecycle/artifact helpers plus `get_bdd_context` and queue metadata helper. | ✓ |

**User's choice:** Lifecycle + artifacts + BDD metadata.
**Notes:** v1 helper surface should include lifecycle, artifact writing, and BDD metadata access.

| Option | Description | Selected |
|--------|-------------|----------|
| Same server | One MCP endpoint; plugin extends/wraps `mcp-pdb`. | |
| Sidecar server | `mcp-pdb` remains PDB server; pytest-bdd-ng sidecar exposes metadata/artifacts. | ✓ |
| Adapter decides | Prefer same endpoint if supported; otherwise sidecar. | |

**User's choice:** Sidecar server.
**Notes:** Discovery must include both endpoint sets.

| Option | Description | Selected |
|--------|-------------|----------|
| Artifact required | Release rejects until Markdown+JSON artifact exists. | |
| Artifact optional | Release always allowed; missing artifact is recorded. | ✓ |
| Reason required | Release without artifact allowed only with reason string. | |

**User's choice:** Artifact optional.
**Notes:** Missing artifact should be recorded, not block release.

---

## Artifact Contract

| Option | Description | Selected |
|--------|-------------|----------|
| Lean | nodeid, phase, status, summary, next_action. | |
| Evidence-focused | Lean plus inspected commands, evidence, suspected cause. | |
| Full BDD | Evidence-focused plus BDD metadata snapshot and artifact links. | ✓ |

**User's choice:** Full BDD.
**Notes:** JSON artifact should be complete enough for BDD reporting and automation.

| Option | Description | Selected |
|--------|-------------|----------|
| Nodeid slug | `{safe-nodeid}.json/md`; readable but long. | |
| Sequence id | `failure-0001.json/md`; compact, needs index. | |
| Both | `failure-0001-{safe-nodeid}.json/md`; readable and stable order. | ✓ |

**User's choice:** Both.
**Notes:** Use sequence number plus nodeid slug.

| Option | Description | Selected |
|--------|-------------|----------|
| Reject only | Return validation error; agent can retry. | ✓ |
| Reject + invalid draft | Save invalid payload under `invalid/` for audit. | |
| Coerce best-effort | Fill missing fields where possible. | |

**User's choice:** Reject only.
**Notes:** Invalid artifact payloads should not be saved or coerced.

---

## xdist/Parallel Boundary

| Option | Description | Selected |
|--------|-------------|----------|
| Unsupported error | Fail early if xdist active. | |
| Controller-only | Only controller/session exposes queue; workers unsupported. | |
| Worker-local | Each worker may expose own MCP/debug endpoint. | ✓ |
| Serial fallback | Disable xdist when debug option enabled. | |

**User's choice:** Worker-local endpoints.
**Notes:** v1 supports xdist by giving each worker its own endpoints.

| Option | Description | Selected |
|--------|-------------|----------|
| One session file per worker | `.pytest_cache/mcp-pdb/workers/{workerid}.json`. | |
| Controller index | `.pytest_cache/mcp-pdb/session.json` lists workers/endpoints. | |
| Both | Per-worker files plus controller/root index, including IP/host and ports. | ✓ |

**User's choice:** Both.
**Notes:** Root and per-worker discovery must include IP/host and ports.

| Option | Description | Selected |
|--------|-------------|----------|
| Independent holds | Each worker holds one failure; agent may inspect many endpoints. | ✓ |
| Global single active | Controller coordinates one held failure across workers. | |
| Configurable max holds | Default one global hold, option raises limit. | |

**User's choice:** Independent holds.
**Notes:** Agent may use sub-agents per worker endpoint.

---

## the agent's Discretion

- Exact internal module/class boundaries.
- Exact option/config key spelling for supporting settings.
- Exact artifact status enum values and schema details beyond locked fields.
- Exact fake-client and xdist test harness approach.

## Deferred Ideas

None.
