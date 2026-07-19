# Architecture Note: Agentic Fan-Out Test Execution and Repair Strategy

This document records the architectural design, technical research, and implemented mechanisms for running the `pytest-bdd-ng` test suite in a parallel "fan-out" mode, diagnosing failures via an autonomous agent loop, and optimizing test execution performance.

---

## 1. Context and Problem Statement

To enable rapid developer and agent cycles (saving 60–90% on token operations), we required:
1. A way to run the full test suite in **fan-out mode** (multi-session, semantic test grouping, dependency management, and fast failures).
2. An **autonomous repair loop** that attaches to failed pytest runs and resolves bugs using live runtime context.
3. Technical analysis of **startup latency and performance bottlenecks** in the test suite to keep cycles as fast as possible.

---

## 2. Implemented Architecture

We have implemented two core components to satisfy these requirements:

### A. Parallel Orchestrator (`src/pytest_bdd_toolchain/tool/agent_orchestrator.py`)
A python-native command-line runner that coordinates parallel runs of semantic test groups (`unit`, `integration`, `contract`, `e2e`, etc.) using a topological dependency graph:
- **Sequential Seed Run:** The `unit` group runs first and must pass.
- **Parallel Fan-Out:** If `unit` passes, `integration` and `contract` are spawned concurrently.
- **Dynamic Plugin Injection:** It invokes `pytest` with `-p pytest_bdd.plugin.debug_mcp.entrypoint --mcp-pdb-on-fail` to dynamically enable the debug-mcp plugin without requiring hardcoded edits to `pyproject.toml` or published entry points.

### B. Global Fail-Fast Mechanism (`src/pytest_bdd_toolchain/case/conftest.py`)
To prevent concurrent sessions from continuing to run (wasting CPU and token costs) when another session has already failed:
- When a test fails in any session under `PYTEST_GLOBAL_FAIL_FAST=1`, a hook in `pytest_runtest_logreport` touches a file-semaphore `.pytest_cache/global_fail_fast.lck`.
- During setup (`pytest_runtest_setup`), other running sessions check this semaphore. If found, they immediately exit cleanly via `pytest.exit("Global fail-fast triggered.")`.

---

## 3. Autonomous Agentic Repair Loop

When a test fails under the orchestrator, it pauses the pytest thread and invokes the **Agentic Repair Lifecycle**:

```
               ┌────────────────────────────────────────────────────────┐
               │         AgentOrchestrator  (Python script)             │
               └─────────┬───────────────────┬─────────────────────────┬┘
                         │                   │                         │
     1. Topological Run  │                   │ 3. Poll failure         │ 4. Attach & Debug
                         ▼                   │    & check session.json │
               ┌──────────────────┐          │                         ▼
               │ pytest -m unit   │          │               ┌──────────────────┐
               └─────────┬────────┘          │               │  Connect raw TCP  │
                         │ 2. Fails          │               │  to sidecar port │
                         ▼                   ▼               └─────────┬────────┘
               ┌──────────────────────────────────┐                    │ 5. Get diagnostics,
               │ .pytest_cache/global_fast.lck   │                    │    write artifacts,
               └──────────────────────────────────┘                    │    send 'continue'
                                                                       ▼
                                                             ┌──────────────────┐
                                                             │ Resume and exit  │
                                                             └──────────────────┘
```

1. **Failure Hold:** Pytest pauses execution on `remote_pdb.set_trace()`, exposing the state over raw TCP on a dynamic port published in `.pytest_cache/mcp-pdb/session.json`.
2. **Specialist Attachment:** The Orchestrator polls the session file, detects `holding_failure`, and connects to the dynamic TCP port.
3. **Telemetry Extraction:** The Orchestrator interacts with the PDB prompt directly, issuing diagnostic commands (`where` for traceback, `list` for source code context).
4. **Artifact Generation:** It compiles this telemetry into a structured JSON `InvestigationArtifact` and Markdown report stored under `.pytest_cache/mcp-pdb/artifacts/<session_id>/`.
5. **Resume:** It sends `continue` to the TCP socket, unblocking pytest to let it exit cleanly, and sets the fail-fast lock.

---

## 4. Technical Performance and Bottleneck Analysis

To keep the test runs as fast and cheap as possible, we analyzed startup latencies and identified several bottlenecks:

### Bottleneck A: Subprocess Spawn Latency (Major)
- **Problem:** Many integration tests under `case/integration/` call `testdir.runpytest()` or `testdir.runpytest_subprocess()`, which spawns a full separate OS subprocess. On virtualized or Windows hosts, this adds 150ms–400ms per call.
- **Solution:** Migrate non-isolated integration tests to `testdir.runpytest_inprocess()`. This runs pytest in-process, bypassing process creation and loading plugins/dependencies 10-30x faster.

### Bottleneck B: Eager Plugin Import Overhead
- **Problem:** Pytest registers 21 distinct entry-point plugins (pretty, progress, summary, code-generator...) at every startup.
- **Solution:**
  - Wrap plugin initialization hooks with early-exit checks so that they do not run if their respective CLI flags are absent.
  - Delay heavy imports (like `ctypes` or `allure`) using lazy imports inside function bodies rather than at the top of plugin modules.

### Bottleneck C: Eager Pytester in Pure Unit Tests
- **Problem:** Default `addopts` loads `-p pytester` even for pure unit tests under `case/unit/` that do not need file-system pytester fixtures.
- **Solution:** Run the unit suite with `-p no:pytester` to completely avoid loading the pytester machinery.

---

## 5. Next Steps for Project Skill Creation

To formalize this strategy as a built-in **Gemini CLI Project Skill** in the future:
1. Use `skill-creator` to generate `.agents/test-repair/SKILL.md`.
2. Define instructions for the CLI Agent to automatically call `agent_orchestrator` and parse the generated JSON artifacts to synthesize fixes.
3. Hook the JSON artifacts directly into the `Allure` report generation flow.
