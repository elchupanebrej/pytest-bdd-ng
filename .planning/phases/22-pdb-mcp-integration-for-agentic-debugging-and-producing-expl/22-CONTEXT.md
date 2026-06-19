# Phase 22: pdb mcp integration for agentic debugging and producing explicit test artifacts - Context

**Gathered:** 2026-06-04
**Status:** Ready for planning

<domain>
## Phase Boundary

Implement agent-facing `mcp-pdb` debugging for pytest and pytest-bdd-ng. The plain pytest layer starts MCP/debug support at session start, holds failed tests on demand, exposes live failed-process state to agents, and writes agent-produced investigation artifacts. The pytest-bdd-ng layer enriches those failures with BDD runtime metadata and bridges artifacts into the existing BDD artifact hook.

This phase uses `mcp-pdb` as the debugger/MCP dependency. It must not reimplement PDB or duplicate `mcp-pdb` command behavior.

</domain>

<decisions>
## Implementation Decisions

### Dependency And Layering

- **D-01:** `mcp-pdb` is a dependency, not a reference implementation. Phase 22 must use it for PDB/MCP behavior instead of building a custom debugger protocol.
- **D-02:** Keep the plain pytest debug-MCP layer inside pytest-bdd-ng for now, but design boundaries so it can be split into a separate pytest plugin later.
- **D-03:** Build two layers: a pytest-only layer first, then a pytest-bdd-ng adapter that adds BDD metadata and uses the BDD artifact hook.

### CLI And Configuration

- **D-04:** `--mcp-pdb-on-fail` enables the feature. There is no separate `--mcp-pdb` enable option.
- **D-05:** All CLI options must have equivalent pytest config keys.
- **D-06:** Port behavior is fixed when a port is configured; if no port is configured, bind an available port automatically.
- **D-07:** Discovery must be both terminal-visible and file-visible. Write `.pytest_cache/mcp-pdb/session.json` and print concise endpoint information.

### Failure Hold Semantics

- **D-08:** Hold failures from pytest `setup`, `call`, and `teardown` phases.
- **D-09:** BDD metadata is best-effort. If scenario context exists, expose feature/scenario/tags/examples/step context where available. If no BDD context exists, plain pytest nodeid plus exception data is valid.
- **D-10:** Leave pytest capture behavior unchanged. Do not snapshot captured stdout/stderr into queue metadata in v1.
- **D-11:** Release can happen through an explicit release helper or raw PDB `continue`; explicit release is preferred.
- **D-12:** Release is allowed without an artifact. Missing artifact should be recorded, not blocked.

### MCP Control Surface

- **D-13:** Use a sidecar MCP server for pytest-bdd-ng helper tools. `mcp-pdb` remains the PDB server.
- **D-14:** The v1 sidecar helper surface includes lifecycle, artifacts, and BDD metadata: `get_active_failure`, `heartbeat`, `release`, `write_investigation_artifact`, and `get_bdd_context`.
- **D-15:** Discovery files must include both `mcp-pdb` endpoint and sidecar endpoint information.

### Artifact Contract

- **D-16:** Agent-produced artifacts must include both Markdown and JSON.
- **D-17:** JSON artifact shape is full BDD: `nodeid`, `pytest_phase`, `status`, `summary`, `inspected_commands`, `evidence`, `suspected_cause`, `next_action`, BDD metadata snapshot, and artifact/link identifiers.
- **D-18:** Artifact filenames use both sequence and nodeid slug: `failure-0001-{safe-nodeid}.json` and `failure-0001-{safe-nodeid}.md`.
- **D-19:** Invalid artifact payloads are rejected with a validation error. Do not coerce and do not save invalid drafts.

### xdist And Parallel Runs

- **D-20:** v1 supports xdist through worker-local endpoints, not a global single queue.
- **D-21:** Discovery includes both a root index and per-worker files. Each entry must include host/IP and ports for both the `mcp-pdb` endpoint and sidecar endpoint.
- **D-22:** Workers hold independently. Multiple workers may each hold one failure at the same time, and external orchestration may use sub-agents per worker endpoint.

### the agent's Discretion

- Decide exact internal class/module boundaries inside the debug-MCP plugin package while preserving a narrow `mcp-pdb` adapter.
- Decide exact config key names for timeout, lease, host, port, and artifact root, provided they mirror CLI options and remain pytest-style.
- Decide exact JSON schema details for status enum values and artifact identifiers, provided D-17 fields are present and validation is strict.
- Decide exact test harness strategy for fake MCP clients and xdist workers.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase Definition And AI Contract

- `.planning/ROADMAP.md` — Phase 22 entry and dependency on Phase 20.
- `.planning/REQUIREMENTS.md` — Phase 22 Debug MCP requirements `P21-MCP-*` and `P21-BDD-*`.
- `.planning/notes/phase-21-debug-mcp-architecture.md` — Exploration decisions that established layering, queue, timeout, lease, discovery, and artifacts.
- `.planning/phases/22-pdb-mcp-integration-for-agentic-debugging-and-producing-expl/22-AI-SPEC.md` — AI/debugging design contract, framework decision, eval strategy, guardrails, and reference dataset.

### Prior Phase Decisions

- `.planning/phases/21-codegen-step-binding-and-tolerant-steps/21-CONTEXT.md` — Recent CLI/runtime/reporting decisions and codegen plugin integration points.
- `.planning/phases/18-split-xdist-remote-tests-into-separate-parallel-gha-executor/18-CONTEXT.md` — xdist/CI execution boundary and worker-related test context.

### Codebase Maps

- `.planning/codebase/ARCHITECTURE.md` — pytest plugin architecture, `Config.stash`/`StashBound`, scenario execution lifecycle, BDD runtime state.
- `.planning/codebase/INTEGRATIONS.md` — local artifact storage, xdist/CI/Docker integration, external services, and existing observability.
- `.planning/codebase/STACK.md` — pytest, plugin entry points, Python/pytest support matrix, optional extras, and test tooling.

### External Dependency

- `https://github.com/samefarrar/mcp-pdb` — Required dependency for PDB/MCP behavior. Planner must verify import/runtime APIs before implementation.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets

- `src/pytest_bdd/model/stash_access.py`: Use `StashBound`/`Config.stash` pattern for debug-MCP session state.
- `src/pytest_bdd/plugin/pickle_runner/plugin.py`: Scenario execution and step failure hooks are likely BDD metadata capture points.
- `src/pytest_bdd/model/scenario_run.py` and split model modules: Runtime state includes `Run`, `ScenarioRun`, `FeatureRuntimeBinding`, active objects, and current step data.
- `src/pytest_bdd/plugin/code_generator/entrypoint.py` and related plugin packages: Recent CLI/plugin pattern for feature flags and pytest plugin structure.
- Existing BDD artifact/reporting hooks: Use the existing artifact hook rather than inventing a separate BDD artifact channel.

### Established Patterns

- pytest behavior belongs in plugin entrypoints/classes and hook implementations.
- Runtime state must use `Config.stash` through `StashBound`; avoid global mutable state.
- Plugin packages should follow class + entrypoint + hook.py conventions where practical.
- New structured data types should use `attrs`; Pydantic is acceptable for artifact/session schema validation where AI-SPEC calls for it.
- Tests should include focused unit/integration coverage and BDD/ATDD acceptance where user-facing behavior is introduced.

### Integration Points

- `pyproject.toml`: Add optional extra for `mcp-pdb` and pytest plugin entry point if new plugin package requires one.
- `src/pytest_bdd/plugin/debug_mcp/`: New plugin package proposed by AI-SPEC.
- `pytest_addoption`: Register `--mcp-pdb-on-fail` and related CLI/config keys.
- `pytest_sessionstart` / `pytest_sessionfinish`: Start endpoints, write discovery, and clean up worker/session state.
- pytest failure reporting hooks: Hold setup/call/teardown failures and populate queue entries.
- xdist worker hooks or worker identity helpers: Publish worker-local endpoint files and root discovery index.
- BDD runtime hooks/state: Enrich queue entries and artifacts with feature/scenario/step/tags/examples metadata.

</code_context>

<specifics>
## Specific Ideas

- Sidecar MCP server is intentionally separate from `mcp-pdb` so dependency behavior stays isolated and pytest-bdd-ng owns only lifecycle, metadata, and artifacts.
- Queue metadata should be small; live state inspection happens through PDB.
- Root discovery index plus per-worker files should support agent/sub-agent orchestration under xdist.
- Missing artifact on release is a recorded outcome, not a failure.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 21-pdb-mcp-integration-for-agentic-debugging-and-producing-explicit-test-artifacts*
*Context gathered: 2026-06-04*
