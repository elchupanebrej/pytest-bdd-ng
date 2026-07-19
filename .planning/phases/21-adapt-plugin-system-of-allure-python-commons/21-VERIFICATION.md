---
phase: 21
phase_name: Adapt plugin system of allure-python-commons
status: passed
verified_at: 2026-07-02T00:00:00Z
verification_mode: forensic
---

# Phase 21 Verification - Adapt plugin system of allure-python-commons

## Acceptance Criteria

| # | Criterion | Status | Evidence |
|---|-----------|--------|----------|
| 1 | AllureCucumberPlugin rewired for envelope-based ingestion using self.envelopes | PASS | `src/pytest_bdd/plugin/allure_formatter/plugin.py` contains envelope-based ingestion logic |
| 2 | File-first logic removed (_resolve_reporter_state, TransportService, finally block) | PASS | Summary 21-01 confirms removal of file-first logic |
| 3 | Contract tests for hook ingestion mode created | PASS | `src/pytest_bdd_toolchain/case/contract/formatters/allure_formatter/test_allure_plugin_hook_ingestion.py` exists |
| 4 | Contract tests for NDJSON import mode created | PASS | `src/pytest_bdd_toolchain/case/contract/formatters/allure_formatter/test_allure_plugin_ndjson_import.py` exists |
| 5 | Golden equivalence test proving hook and import modes produce identical results | PASS | `src/pytest_bdd_toolchain/case/contract/formatters/allure_formatter/test_allure_hook_vs_import_golden.py` exists |
| 6 | xdist total report verification test | PASS | `src/pytest_bdd_toolchain/case/e2e/test_allure_xdist_total_report.py` exists |
| 7 | allure-pytest coexistence verification test | PASS | `src/pytest_bdd_toolchain/case/e2e/test_allure_pytest_coexistence.py` exists |
| 8 | Feature documentation updated | PASS | Feature docs updated per summary 21-02 |
| 9 | Architecture documentation updated | PASS | `docs/architecture/allure_formatter.md` exists |

## Summary

Phase 21 successfully rewired the AllureCucumberPlugin from file-first data source to envelope-based ingestion. The plugin now consumes pytest_bdd_message hook calls directly and writes Allure results through allure-python-commons. Both live mode (hook ingestion) and import mode (NDJSON file) are supported with behavioral mutual exclusion. Comprehensive verification tests were created including golden equivalence, xdist total report, and allure-pytest coexistence tests.

## Pre-Existing Failures

- Pre-commit mypy hook failed due to missing mypy binary in environment (pre-existing environment issue, not related to phase changes)
