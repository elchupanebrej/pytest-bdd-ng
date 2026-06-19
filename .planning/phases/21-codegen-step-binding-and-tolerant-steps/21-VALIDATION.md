---
phase: 19
slug: codegen-step-binding-and-tolerant-steps
status: complete
nyquist_compliant: true
wave_0_complete: true
created: 2026-06-03
---

# Phase 21 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest via repository testdir/pytester integration tests plus executable BDD docs |
| **Config file** | `pyproject.toml`, `features/13 Code Generator/01 Code generation.feature.md`, codegen and pickle-runner plugin entrypoints |
| **Quick run command** | `rtk python -m pytest tests/cases/integration/generation -m integration -q` |
| **Full phase run** | `rtk python -m pytest tests/cases/integration/generation tests/cases/integration/feature/test_mock_run.py tests/cases/integration/feature/test_wip_steps.py tests/cases/integration/feature/test_tolerant_steps.py tests/cases/integration/messages/test_tolerant_step_reporting.py tests/cases/e2e/e2e/test_feature_058_code_generator.py -q` |
| **Static check** | `rtk ruff check src/pytest_bdd/plugin/code_generator src/pytest_bdd/plugin/pickle_runner src/pytest_bdd/steps tests/cases/integration/generation tests/cases/integration/feature tests/cases/integration/messages tests/cases/e2e/steps_code_generator.py` |
| **Estimated runtime** | 2-5 minutes for focused phase slices |

---

## Sampling Rate

- **After every task commit:** Run the task-specific pytest file named in the plan.
- **After every plan wave:** Run all tests touched by completed wave plans.
- **Before `$gsd-verify-work`:** Run full phase run and static check from this validation file.
- **Max feedback latency:** 5 minutes for focused phase validation.

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 21-01-01 | 01 | 1 | P20-CLI | T-21-01-01 | New spec flags replace legacy codegen CLI as primary workflow | integration | `rtk python -m pytest tests/cases/integration/generation/test_gather_missing_steps.py -q` | exists | passed |
| 21-01-02 | 01 | 1 | P20-NDJSON | T-21-01-02 | Missing artifacts emit deterministic machine-readable NDJSON | integration | `rtk python -m pytest tests/cases/integration/generation/test_gather_missing_steps.py -q` | exists | passed |
| 21-02-01 | 02 | 1 | P20-BIND | T-21-02-01 | Target-file binding is AST-aware and idempotent | integration | `rtk python -m pytest tests/cases/integration/generation/test_bind_feature.py -q` | exists | passed |
| 21-02-02 | 02 | 1 | P20-GENERATE | T-21-02-02 | Generated skeletons use `_`, `@not_implemented`, and `NotImplementedError` | integration | `rtk python -m pytest tests/cases/integration/generation/test_generate_missing_steps.py -q` | exists | passed |
| 21-02-03 | 02 | 1 | P20-ROLLBACK | T-21-02-03 | Syntax/format failure rolls back unless keep flag is set | integration | `rtk python -m pytest tests/cases/integration/generation/test_bind_feature.py tests/cases/integration/generation/test_generate_missing_steps.py -q` | exists | passed |
| 21-03-01 | 03 | 2 | P20-WIP | T-21-03-01 | `@not_implemented` works in both decorator orders and status priority is deterministic | unit/integration | `rtk python -m pytest tests/cases/unit tests/cases/integration/feature/test_wip_steps.py -q -k 'not_implemented or wip_status'` | exists | passed |
| 21-03-02 | 03 | 2 | P20-MOCK | T-21-03-02 | `--mock-run` verifies binding without scenario/step hooks or bodies | integration | `rtk python -m pytest tests/cases/integration/feature/test_mock_run.py -q` | exists | passed |
| 21-04-01 | 04 | 2 | P20-TOLERANT | T-21-04-01 | Tolerant ignored preserves failed step report while scenario may pass | integration/messages | `rtk python -m pytest tests/cases/integration/feature/test_tolerant_steps.py tests/cases/integration/messages/test_tolerant_step_reporting.py -q` | exists | passed |
| 21-05-01 | 05 | 3 | P20-ATDD | T-21-05-01 | Executable BDD docs cover full authoring loop with observable assertions | e2e | `rtk python -m pytest tests/cases/e2e/e2e/test_feature_058_code_generator.py -q` | exists | passed |
| 21-05-02 | 05 | 3 | P20-ATDD | T-21-05-02 | Generated docs match executable feature source | docs/e2e | `rtk python -m pytest tests/cases/e2e/e2e/test_feature_058_code_generator.py -q` | exists | passed |

---

## Wave 0 Requirements

- [x] Add focused integration tests for new codegen CLI, NDJSON output, binding, generation, and rollback before or with implementation.
- [x] Add runtime tests for mock-run, not-implemented/WIP status priority, tolerant status, and reporter output before or with implementation.
- [x] Add executable BDD coverage under `features/13 Code Generator/` before phase verification.

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Legacy flag migration choice | P20-CLI | User compatibility policy may require inspecting release notes or downstream expectations | Confirm old flags are either removed or explicitly treated as compatibility aliases, never primary workflow |
| First full CI signal | P20-ATDD | Local slices cannot prove every Python/platform matrix | Inspect first GitHub Actions run after phase execution for focused slices and no platform-specific regressions |

---

## Validation Sign-Off

- [x] All tasks have automated verify or justified manual verification
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers missing references
- [x] No watch-mode flags
- [x] Feedback latency < 5 minutes for focused phase validation
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** complete after focused phase verification on 2026-06-03

---

## Validation Audit 2026-06-04

| Metric | Count |
|--------|-------|
| Gaps found | 0 |
| Resolved | 0 |
| Escalated | 0 |

Automated confirmation:

- `rtk powershell -NoProfile -Command '$env:PYTHONPATH = (Join-Path (Get-Location) "src"); python -m pytest tests/cases/integration/generation tests/cases/integration/feature/test_mock_run.py tests/cases/integration/feature/test_wip_steps.py tests/cases/integration/feature/test_tolerant_steps.py tests/cases/integration/messages/test_tolerant_step_reporting.py tests/cases/e2e/e2e/test_feature_058_code_generator.py -q'` -> 31 passed, 3 skipped.
- `rtk powershell -NoProfile -Command '$env:PYTHONPATH = (Join-Path (Get-Location) "src"); python -m pytest tests/cases/unit/unit/test_step_policy_decorators.py -q'` -> 8 passed.
- `rtk powershell -NoProfile -Command '$env:PYTHONPATH = (Join-Path (Get-Location) "src"); python -m ruff check src/pytest_bdd/plugin/code_generator src/pytest_bdd/plugin/pickle_runner src/pytest_bdd/steps tests/cases/integration/generation tests/cases/integration/feature/test_mock_run.py tests/cases/integration/feature/test_wip_steps.py tests/cases/integration/feature/test_tolerant_steps.py tests/cases/integration/messages/test_tolerant_step_reporting.py tests/cases/e2e/steps_code_generator.py'` -> All checks passed.
