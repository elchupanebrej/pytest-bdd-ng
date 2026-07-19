---
phase: 21
slug: adapt-plugin-system-of-allure-python-commons
status: approved
nyquist_compliant: true
wave_0_complete: true
created: 2026-06-13
updated: 2026-06-15
---

# Phase 21 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest >= 9.0.3 |
| **Config file** | [pyproject.toml](file:///c:/Users/bulky/Projects/pytest-bdd/pyproject.toml) [tool.pytest.ini_options] |
| **Quick run command** | `.venv\Scripts\pytest tests/cases/unit/allure/` |
| **Full suite command** | `.venv\Scripts\pytest tests/cases/unit/allure/ tests/cases/integration/allure/ tests/cases/contract/allure/` |
| **Estimated runtime** | ~120 seconds |

---

## Sampling Rate

- **After every task commit:** Run `.venv\Scripts\pytest tests/cases/unit/allure/`
- **After every plan wave:** Run `.venv\Scripts\pytest tests/cases/unit/allure/ tests/cases/integration/allure/ tests/cases/contract/allure/`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 120 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 21-01-01 | 01 | 1 | REQ-01 | — | N/A | contract | `pytest tests/cases/contract/allure/test_allure_plugin_hook_ingestion.py` | [test_allure_plugin_hook_ingestion.py](file:///c:/Users/bulky/Projects/pytest-bdd/tests/cases/contract/allure/test_allure_plugin_hook_ingestion.py) | ✅ green |
| 21-01-01 | 01 | 1 | REQ-02 | — | N/A | unit | `pytest tests/cases/unit/allure/test_native_plugin.py` | [test_native_plugin.py](file:///c:/Users/bulky/Projects/pytest-bdd/tests/cases/unit/allure/test_native_plugin.py) | ✅ green |
| 21-02-02 | 02 | 2 | REQ-03 | — | N/A | e2e | `pytest tests/cases/e2e/test_allure_pytest_coexistence.py` | [test_allure_pytest_coexistence.py](file:///c:/Users/bulky/Projects/pytest-bdd/tests/cases/e2e/test_allure_pytest_coexistence.py) | ✅ green |
| 21-03-02 | 03 | 3 | REQ-04 | — | N/A | integration | `pytest tests/cases/integration/allure/test_realtime_interception.py` | [test_realtime_interception.py](file:///c:/Users/bulky/Projects/pytest-bdd/tests/cases/integration/allure/test_realtime_interception.py) | ✅ green |
| 21-02-03 | 02 | 2 | REQ-05 | — | N/A | contract | `pytest tests/cases/contract/allure/test_mapping_contract.py` | [test_mapping_contract.py](file:///c:/Users/bulky/Projects/pytest-bdd/tests/cases/contract/allure/test_mapping_contract.py) | ✅ green |
| 21-01-02 | 01 | 1 | REQ-06 | — | N/A | contract | `pytest tests/cases/contract/allure/test_allure_plugin_ndjson_import.py` | [test_allure_plugin_ndjson_import.py](file:///c:/Users/bulky/Projects/pytest-bdd/tests/cases/contract/allure/test_allure_plugin_ndjson_import.py) | ✅ green |
| 21-02-01 | 02 | 2 | REQ-07 | — | N/A | contract | `pytest tests/cases/contract/allure/test_allure_hook_vs_import_golden.py` | [test_allure_hook_vs_import_golden.py](file:///c:/Users/bulky/Projects/pytest-bdd/tests/cases/contract/allure/test_allure_hook_vs_import_golden.py) | ✅ green |
| 21-02-01 | 02 | 2 | REQ-08 | — | N/A | e2e | `pytest tests/cases/e2e/test_allure_xdist_total_report.py` | [test_allure_xdist_total_report.py](file:///c:/Users/bulky/Projects/pytest-bdd/tests/cases/e2e/test_allure_xdist_total_report.py) | ✅ green |
| 21-03-01 | 03 | 3 | REQ-09 | — | N/A | unit | `pytest tests/cases/unit/allure/test_listener.py tests/cases/unit/allure/test_api_hooks.py tests/cases/unit/allure/test_message_adapter.py` | [test_listener.py](file:///c:/Users/bulky/Projects/pytest-bdd/tests/cases/unit/allure/test_listener.py) | ✅ green |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

Existing infrastructure covers all phase requirements.

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| None | — | — | — |

*All phase behaviors have automated verification.*

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 120s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** approved 2026-06-15

---

## Validation Audit 2026-06-15
| Metric | Count |
|--------|-------|
| Gaps found | 0 |
| Resolved | 9 |
| Escalated | 0 |
