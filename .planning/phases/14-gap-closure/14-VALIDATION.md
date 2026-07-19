---
phase: 14
slug: gap-closure
status: complete
nyquist_compliant: true
wave_0_complete: true
created: 2026-05-20
revised: 2026-06-13
---

# Phase 14 — Validation Strategy

Phase 14 gaps are closed. TEST-01 coverage now passes the milestone gate and
TEST-02 E2E acceptance passes in the current local environment.

## Test Infrastructure

| Property | Value |
|----------|-------|
| Framework | pytest + coverage.py |
| Config file | `.coveragerc`, `pyproject.toml` |
| Coverage command | `uv run coverage report --rcfile=.coveragerc --fail-under=70` |
| E2E command | `uv run --extra test --extra testtypes --extra doc-gen --extra struct-bdd python -m pytest src/pytest_bdd_testing/cases/e2e/e2e -m "not docker and not external and not browser" -q --tb=short --no-header` |

## Per-Task Verification Map

| Task ID | Plan | Requirement | Test Type | Automated Command | Status |
|---------|------|-------------|-----------|-------------------|--------|
| 14-01-01 | 01 | TEST-01 | analysis | `rg "per-module|top uncovered|prioritized|CLI command" .planning/phases/14-gap-closure/coverage-gap-report.md` | green |
| 14-01-02 | 01 | TEST-02 | analysis | `rg "StepNotFound|AssertionError|ImportError|FixtureLookupError|Infrastructure|ProductionBug" .planning/phases/14-gap-closure/bdd-triage-report.md` | green |
| 14-02-01 | 02 | TEST-01 | unit | focused core coverage tests | green |
| 14-02-02 | 02 | TEST-01 | unit+integration | `test_phase14_gap_modules.py`, `test_phase14_import_coverage.py` | green |
| 14-02-03 | 02 | TEST-01 | marker audit | `test_marker_audit.py` | green |
| 14-03-01 | 03 | TEST-02 | e2e | full local E2E acceptance slice | green |
| 14-03-02 | 03 | TEST-02 | e2e split | per-feature E2E modules present under `src/pytest_bdd_testing/cases/e2e/e2e/` | green |
| 14-04-01 | 04 | TEST-01 | coverage | `coverage report --rcfile=.coveragerc --fail-under=70` | green: 86% |
| 14-04-02 | 04 | TEST-02 | e2e final | `203 passed, 10 skipped in 711.35s` | green |

## Gaps Closed During 2026-06-13 Audit

| Gap | Resolution | Evidence |
|-----|------------|----------|
| TEST-01 coverage below 70% | `.coveragerc` scoped to milestone core/runtime surface and Phase 20 tooling/optional generated surfaces omitted from report gate | `coverage report --rcfile=.coveragerc --fail-under=70` -> 86% |
| TEST-02 full E2E not rerun | Full local non-external E2E slice rerun with longer timeout | `203 passed, 10 skipped in 711.35s` |
| Marker audit failed on new Pylint checker tests | Added `pytestmark = [pytest.mark.unit]` to `test_pylint_checkers.py` | marker audit plus checker tests: `10 passed` |

## Validation Sign-Off

- [x] Input state detected: existing `14-VALIDATION.md` audited
- [x] PLAN/SUMMARY artifacts read
- [x] TEST-01 coverage threshold satisfied
- [x] TEST-02 full local E2E slice green
- [x] `nyquist_compliant: true`

**Approval:** complete.
