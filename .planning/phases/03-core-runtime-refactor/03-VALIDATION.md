---
phase: 03
slug: core-runtime-refactor
status: draft
nyquist_compliant: true
wave_0_complete: false
created: 2026-05-12
---

# Phase 03 - Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest |
| **Config file** | `pyproject.toml` |
| **Quick run command** | `uv run python -m pytest tests/hook/test_scenario_run_characterization.py -q` |
| **Full suite command** | `uv run python -m pytest tests/ -q` |
| **Estimated runtime** | quick loop ~10 seconds; full suite depends on local environment |

## Sampling Rate

- **After every task commit:** Run the task's automated command from the map below.
- **After every plan wave:** Run the runtime model loop.
- **Before `$gsd-verify-work`:** Full suite and xdist smoke must be green.
- **Max feedback latency:** one focused test command per task, full suite only at final verification.

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 03-01-01 | 01 | 1 | REF-01 | T-03-01 / T-03-02 | Existing runtime behavior captured before split | characterization | `uv run python -m pytest tests/hook/test_scenario_run_characterization.py -q` | ❌ W0 | pending |
| 03-01-02 | 01 | 1 | REF-01 | T-03-03 | Old-path moved-symbol imports rejected by source contract | source contract | `uv run python -m pytest tests/hook/test_scenario_run_characterization.py tests/model/test_scenario_run_returns_contract.py -q` | ✅ | pending |
| 03-02-01 | 02 | 2 | REF-01 | T-03-01 / T-03-04 | Three modules import without cycles and preserve runtime state | unit/integration | `uv run python -m pytest tests/hook/test_run_transitions.py tests/hook/test_scenario_run_model.py tests/hook/test_run_scenario_runtime_unit.py tests/hook/test_reporting_context_snapshot_unit.py tests/hook/test_run_diagnostics.py tests/hook/test_scenario_reference_resolution.py -q` | ❌ W0 | pending |
| 03-02-02 | 02 | 2 | REF-01 | T-03-03 | Production and tests use direct owning module imports | source contract | `uv run python -m pytest tests/model/test_scenario_run_returns_contract.py tests/compatibility/test_public_api_exports.py -q` | ✅ | pending |
| 03-03-01 | 03 | 3 | REF-01 | T-03-01 / T-03-02 / T-03-04 | Runtime lifecycle remains green across full suite and xdist | full verification | `uv run python -m pytest tests/ -q && uv run python -m pytest tests/ -q -n 2` | ✅ | pending |

## Wave 0 Requirements

- [ ] `tests/hook/test_scenario_run_characterization.py` - characterization tests for `Run`, `ScenarioRun`, `FeatureRuntimeBinding`, state transitions, serialization, and import paths.
- [ ] `src/pytest_bdd/model/run.py` - target module created during Wave 2.
- [ ] `src/pytest_bdd/model/feature_binding.py` - target module created during Wave 2.

## Manual-Only Verifications

All phase behaviors have automated verification.

## Validation Sign-Off

- [x] All tasks have automated verify commands or Wave 0 dependencies.
- [x] Sampling continuity: no 3 consecutive tasks without automated verify.
- [x] Wave 0 covers all missing references.
- [x] No watch-mode flags.
- [x] Feedback latency bounded by focused test loops.
- [x] `nyquist_compliant: true` set in frontmatter.

**Approval:** pending
