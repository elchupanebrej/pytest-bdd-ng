---
phase: 20
slug: pdb-mcp-integration-for-agentic-debugging-and-producing-expl
status: approved
nyquist_compliant: true
wave_0_complete: true
created: 2026-06-05
updated: 2026-06-05
---

# Phase 21 - Validation Strategy

Per-phase validation contract for debug MCP pytest plugin, sidecar artifacts, BDD metadata, and xdist worker discovery.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest via `uv run python -m pytest` |
| **Config file** | `pyproject.toml` |
| **Quick run command** | `uv run python -m pytest tests/cases/integration/debug_mcp -q` |
| **Full suite command** | `uv run python -m pytest tests/cases/integration/debug_mcp tests/cases/e2e/e2e/test_feature_065_debug_mcp.py -q` |
| **Static checks** | `uv run ruff check src/pytest_bdd/plugin/debug_mcp tests/cases/integration/debug_mcp tests/cases/e2e/steps_debug_mcp.py tests/cases/e2e/e2e/test_feature_065_debug_mcp.py`; `uv run --extra testtypes mypy src/pytest_bdd/plugin/debug_mcp` |
| **Estimated runtime** | ~15 seconds for focused tests, ~110 seconds for targeted pre-commit hooks |

---

## Sampling Rate

- **After every task commit:** Run focused plan test file named in plan `<verify>`.
- **After every plan wave:** Run `uv run python -m pytest tests/cases/integration/debug_mcp -q`.
- **Before `$gsd-verify-work`:** Run full focused suite plus ruff and mypy commands above.
- **Max feedback latency:** ~120 seconds including targeted pre-commit.

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 21-01-01 | 01 | 1 | P21-MCP-01, P21-MCP-03 | T-21-01-01, T-21-01-03 | Enable option/config defaults stay local-only; fixed and auto ports validate. | integration | `uv run python -m pytest tests/cases/integration/debug_mcp/test_options_and_discovery.py -q` | yes | green |
| 21-01-02 | 01 | 1 | P21-MCP-04 | T-21-01-02 | Atomic discovery JSON includes session id, endpoints, waiting status, terminal line. | integration | `uv run python -m pytest tests/cases/integration/debug_mcp/test_options_and_discovery.py -q` | yes | green |
| 21-02-01 | 02 | 2 | P21-MCP-02, P21-MCP-06 | T-21-02-02 | Setup/call/teardown failures become deterministic active-failure metadata without changing capture. | integration | `uv run python -m pytest tests/cases/integration/debug_mcp/test_failure_hold_lifecycle.py -q` | yes | green |
| 21-02-02 | 02 | 2 | P21-MCP-05, P21-MCP-06 | T-21-02-01, T-21-02-03 | Timeout, heartbeat lease, explicit release, raw PDB continue, adapter-only mcp-pdb import. | integration/static | `uv run python -m pytest tests/cases/integration/debug_mcp/test_failure_hold_lifecycle.py -q` | yes | green |
| 21-03-01 | 03 | 3 | P21-MCP-04, P21-MCP-07 | T-21-03-02 | Sidecar exposes active failure, heartbeat, release, BDD context placeholder, discovery endpoints. | integration | `uv run python -m pytest tests/cases/integration/debug_mcp/test_sidecar_and_artifacts.py -q` | yes | green |
| 21-03-02 | 03 | 3 | P21-MCP-07 | T-21-03-01, T-21-03-03 | Strict artifact schema writes paired JSON/Markdown and rejects invalid payloads before filesystem writes. | integration | `uv run python -m pytest tests/cases/integration/debug_mcp/test_sidecar_and_artifacts.py -q` | yes | green |
| 21-04-01 | 04 | 4 | P21-BDD-01 | T-21-04-01, T-21-04-03 | BDD metadata is best-effort, exposed through active failure and sidecar, null for plain pytest. | integration | `uv run python -m pytest tests/cases/integration/debug_mcp/test_bdd_metadata_and_artifact_bridge.py -q` | yes | green |
| 21-04-02 | 04 | 4 | P21-BDD-02 | T-21-04-02 | Validated artifacts emit debug MCP BDD artifact hook; plain pytest writes remain safe. | integration | `uv run python -m pytest tests/cases/integration/debug_mcp/test_bdd_metadata_and_artifact_bridge.py -q` | yes | green |
| 21-05-01 | 05 | 5 | P21-MCP-01, P21-MCP-02, P21-MCP-03, P21-MCP-04, P21-MCP-05, P21-MCP-06, P21-MCP-07 | T-21-05-01, T-21-05-02 | xdist workers write independent files; root index merges workers and active hold status. | integration | `uv run python -m pytest tests/cases/integration/debug_mcp/test_xdist_worker_discovery.py -q` | yes | green |
| 21-05-02 | 05 | 5 | P21-MCP-01, P21-MCP-02, P21-MCP-03, P21-MCP-04, P21-MCP-05, P21-MCP-06, P21-MCP-07, P21-BDD-01, P21-BDD-02 | T-21-05-03 | Executable BDD docs cover discovery, holds, artifacts, invalid payloads, BDD metadata, xdist discovery. | e2e/docs | `uv run python -m pytest tests/cases/e2e/e2e/test_feature_065_debug_mcp.py -q` | yes | green |

*Status: green = command passed during validation audit.*

---

## Requirement Coverage

| Requirement | Coverage | Test Files |
|-------------|----------|------------|
| P21-MCP-01 | COVERED | `test_options_and_discovery.py`, `test_feature_065_debug_mcp.py` |
| P21-MCP-02 | COVERED | `test_failure_hold_lifecycle.py`, `test_xdist_worker_discovery.py`, `test_feature_065_debug_mcp.py` |
| P21-MCP-03 | COVERED | `test_options_and_discovery.py`, `test_xdist_worker_discovery.py` |
| P21-MCP-04 | COVERED | `test_options_and_discovery.py`, `test_sidecar_and_artifacts.py`, `test_xdist_worker_discovery.py`, `test_feature_065_debug_mcp.py` |
| P21-MCP-05 | COVERED | `test_failure_hold_lifecycle.py` |
| P21-MCP-06 | COVERED | `test_failure_hold_lifecycle.py` |
| P21-MCP-07 | COVERED | `test_sidecar_and_artifacts.py`, `test_bdd_metadata_and_artifact_bridge.py`, `test_feature_065_debug_mcp.py` |
| P21-BDD-01 | COVERED | `test_bdd_metadata_and_artifact_bridge.py`, `test_feature_065_debug_mcp.py` |
| P21-BDD-02 | COVERED | `test_bdd_metadata_and_artifact_bridge.py` |

---

## Wave 0 Requirements

Existing infrastructure covers all phase requirements.

---

## Manual-Only Verifications

All phase behaviors have automated verification.

---

## Validation Audit 2026-06-05

| Metric | Count |
|--------|-------|
| Requirements audited | 9 |
| Tasks audited | 10 |
| Gaps found | 0 |
| Resolved by new tests | 0 |
| Escalated manual-only | 0 |

Commands run:

- `uv run python -m pytest tests/cases/integration/debug_mcp tests/cases/e2e/e2e/test_feature_065_debug_mcp.py -q` - 35 passed.
- `uv run ruff check src/pytest_bdd/plugin/debug_mcp tests/cases/integration/debug_mcp tests/cases/e2e/steps_debug_mcp.py tests/cases/e2e/e2e/test_feature_065_debug_mcp.py` - passed.
- `uv run --extra testtypes mypy src/pytest_bdd/plugin/debug_mcp` - passed.
- `uv run pre-commit run --files .planning/phases/21-pdb-mcp-integration-for-agentic-debugging-and-producing-expl/21-VALIDATION.md` - passed.

---

## Validation Sign-Off

- [x] All tasks have automated verify commands.
- [x] Sampling continuity has no 3 consecutive tasks without automated verify.
- [x] Wave 0 not required because existing pytest infrastructure covers all phase requirements.
- [x] No watch-mode flags.
- [x] Feedback latency under 120 seconds for focused checks.
- [x] `nyquist_compliant: true` set in frontmatter.

**Approval:** approved 2026-06-05
