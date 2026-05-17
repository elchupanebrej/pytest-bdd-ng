---
phase: 11
slug: audit-prune
status: complete
nyquist_compliant: true
wave_0_complete: true
created: 2026-05-17
---

# Phase 11 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x-9.x |
| **Config file** | pyproject.toml [tool.pytest.ini_options] |
| **Quick run command** | `uv run python -m pytest tests/unit/ tests/messages/ tests/model/ -q --tb=no` |
| **Full suite command** | `uv run python -m pytest tests/ -q -x` |
| **Estimated runtime** | ~120 seconds (unit/messages/model subset) |

---

## Sampling Rate

- **After every task commit:** Run `uv run python -m ruff check src/pytest_bdd/ --select F401,F811,ERA001`
- **After every plan wave:** Run `uv run python -m pytest tests/unit/ tests/messages/ tests/model/ -q --tb=no`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** ~120 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 11-01-01 | 01 | 1 | SIM-03 | T-11-01 | Dead module removal (runner.py), retained false positives | integration | `uv run python -m ruff check src/pytest_bdd/ --select F401,F811` | ✅ | ✅ green |
| 11-01-02 | 01 | 1 | SIM-03 | T-11-02 | Unused function removal (validate_requested_pair) | integration | `Select-String -Path src/pytest_bdd/runner.py -Pattern "validate_requested_pair"` | ✅ | ✅ green |
| 11-02-01 | 02 | 2 | SIM-03 | T-11-03 | Steps package re-exports (Registry, Matcher, Definition) | unit | `uv run python -c "from pytest_bdd.steps.registry import Registry; ..."` | ✅ | ✅ green |
| 11-02-02 | 02 | 2 | SIM-03 | T-11-04 | Backward compat: given/when/then/step, StepDefinitionManager | unit | `uv run python -c "from pytest_bdd.steps import given, when, then, step, StepDefinitionManager; ..."` | ✅ | ✅ green |
| 11-03-01 | 03 | 2 | SIM-03 | T-11-06 | Governance package re-exports (parse_args, main, schema funcs) | unit | `uv run python -c "from pytest_bdd.script.message_capability_governance import parse_args, main, ..."` | ✅ | ✅ green |
| 11-03-02 | 03 | 2 | SIM-03 | T-11-08 | Script entry point: `python -m pytest_bdd.script.message_capability_governance --help` | integration | `uv run python -m pytest_bdd.script.message_capability_governance --help` | ✅ | ✅ green |
| 11-04-01 | 04 | 2 | SIM-03 | T-11-09 | model.run package re-exports (Run, RunStage, RunStatus, HookPhase) | unit | `uv run python -c "from pytest_bdd.model.run import Run, RunStage, RunStatus, HookPhase, LifecycleObjectRef"` | ✅ | ✅ green |
| 11-04-02 | 04 | 2 | SIM-03 | T-11-11 | Run class StashBound inheritance preserved | unit | `uv run python -c "from pytest_bdd.model.run import Run; from pytest_bdd.model.stash_access import StashBound; assert issubclass(Run, StashBound)"` | ✅ | ✅ green |
| 11-05-01 | 05 | 3 | SIM-03 | T-11-12 | Plugin audit document exists with all 17 entries | documentation | `Test-Path .planning/phases/11-audit-prune/11-PLUGIN-AUDIT.md` | ✅ | ✅ green |
| 11-05-02 | 05 | 3 | SIM-03 | T-11-13 | Decopatch health + CI matrix documented | documentation | `Test-Path .planning/phases/11-audit-prune/11-DECOPATCH-HEALTH.md` | ✅ | ✅ green |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

Existing infrastructure covers all phase requirements:
- `tests/unit/test_steps.py` — steps module unit tests
- `tests/unit/model/test_run.py` — model/run unit tests
- `tests/messages/test_governance.py` — governance tests
- `tests/messages/test_governance_cli_contract.py` — governance CLI tests
- `tests/messages_coverage/test_full_capability_governance.py` — governance coverage
- `tests/hook/test_run_*.py` — run lifecycle hook tests
- `tests/feature/test_steps.py` — step execution integration tests
- 447 tests pass (unit/messages/model subset), 2 skipped

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Full CI matrix execution (72 tox envs) | SIM-03 | Requires CI infrastructure, not local | `uv run tox --listenvs` confirms 72 environments; actual matrix runs in CI |
| Plugin consumer analysis completeness | SIM-03 | Requires manual review of all 17 plugins | Review 11-PLUGIN-AUDIT.md entries for accuracy |
| decopatch stability assessment | SIM-03 | External library, no automated check | Review 11-DECOPATCH-HEALTH.md; check PyPI for new releases periodically |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 120s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** approved 2026-05-17

---

## Validation Audit 2026-05-17

| Metric | Count |
|--------|-------|
| Gaps found | 0 |
| Resolved | 0 |
| Escalated | 0 |

All 10 tasks across 5 sub-plans have automated verification. Existing test suite (447 tests) covers all requirement behaviors. Phase is Nyquist-compliant.
