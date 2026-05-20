---
phase: 14
slug: gap-closure
status: partial
nyquist_compliant: false
wave_0_complete: true
created: 2026-05-20
revised: 2026-05-20
---

# Phase 14 — Validation Strategy

> Retroactive Nyquist audit for Phase 14. Existing validation claimed compliance while final phase artifacts showed TEST-01 was not fully met. This revision records the actual state after gap-filling.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest >=7.0.0 + pytest-cov |
| **Config file** | `.coveragerc`, `pyproject.toml` |
| **Quick run command** | `uv run --extra test --extra testtypes --extra doc-gen --extra struct-bdd python -m pytest tests/cases/unit/unit/test_phase14_gap_modules.py -q --no-header` |
| **Import smoke command** | `uv run --extra test --extra testtypes --extra doc-gen --extra struct-bdd python -m pytest tests/cases/unit/unit/test_phase14_import_coverage.py -q --no-header` |
| **BDD run command** | `uv run --extra test --extra testtypes --extra doc-gen --extra struct-bdd python -m pytest tests/cases/e2e/e2e/ -v --tb=short --no-header` |
| **Coverage report command** | `uv run coverage report --rcfile=.coveragerc --fail-under=70` |

---

## Per-Task Verification Map

| Task ID | Plan | Requirement | Test Type | Automated Command | Status |
|---------|------|-------------|-----------|-------------------|--------|
| 14-01-01 | 01 | TEST-01 | analysis | `grep -Ei "per-module|top uncovered|prioritized|CLI command" .planning/phases/14-gap-closure/coverage-gap-report.md` | ✅ green |
| 14-01-02 | 01 | TEST-02 | analysis | `grep -Ei "StepNotFound|AssertionError|ImportError|FixtureLookupError|Infrastructure|ProductionBug" .planning/phases/14-gap-closure/bdd-triage-report.md` | ✅ green |
| 14-02-01 | 02 | TEST-01 | unit | `uv run --extra test --extra testtypes --extra doc-gen --extra struct-bdd python -m pytest tests/cases/unit/unit/test_tag_expression.py tests/cases/unit/unit/test_scenario_locator.py tests/cases/unit/unit/test_scenario.py tests/cases/unit/unit/test_parser.py tests/cases/unit/unit/test_collector.py -q --no-header` | ⚠️ covered, broader 70% target unmet |
| 14-02-02 | 02 | TEST-01 | unit+integration | `uv run --extra test --extra testtypes --extra doc-gen --extra struct-bdd python -m pytest tests/cases/unit/unit/test_phase14_gap_modules.py -q --no-header` | ✅ green |
| 14-02-03 | 02 | TEST-01 | marker audit | `uv run --extra test --extra testtypes --extra doc-gen --extra struct-bdd python -m pytest tests/cases/unit/unit/test_marker_audit.py -q --no-header` | not rerun in audit |
| 14-03-01 | 03 | TEST-02 | e2e | `uv run --extra test --extra testtypes --extra doc-gen --extra struct-bdd python -m pytest tests/cases/e2e/e2e/ -v --tb=short --no-header` | ⚠️ partial: focused formatter regression fixed; full E2E not rerun after fix |
| 14-03-02 | 03 | TEST-02 | e2e split | `rg -n "scenarios\\(" tests/cases/e2e/e2e/test_e2e.py tests/cases/e2e/e2e/test_feature_*.py` | ✅ green |
| 14-03-03 | 03 | TEST-02 | docs | `test -f "docs/features/09 Tag Expressions/02 Edge cases.feature.rst" && test -f "docs/features/11 Mimetype/02 Edge cases.feature.rst" && test -f "docs/features/16 Batch Collection/02 Edge cases with large files.feature.rst"` | ✅ green |
| 14-04-01 | 04 | TEST-01 | full suite + coverage | `uv run coverage report --rcfile=.coveragerc --fail-under=70` | ❌ red: 56% after documented report-stage omits |
| 14-04-02 | 04 | TEST-02 | e2e + integration final | full `tests/cases/` run observed 1520 pass, 20 skip, 16 env/external failures | ⚠️ partial |
| 14-04-03 | 04 | TEST-01, TEST-02 | summary | `grep -c "Requirements Status" .planning/phases/14-gap-closure/14-04-SUMMARY.md; grep -ci "before/after" .planning/phases/14-gap-closure/14-04-SUMMARY.md` | ✅ green |

---

## Gaps Filled During Audit

| Gap | Files | Verification |
|-----|-------|--------------|
| Missing generated feature docs for 3 new feature files | `docs/features/09 Tag Expressions/02 Edge cases.feature.rst`, `docs/features/11 Mimetype/02 Edge cases.feature.rst`, `docs/features/16 Batch Collection/02 Edge cases with large files.feature.rst` | file existence checks |
| Missing focused tests for low/zero coverage helper modules | `tests/cases/unit/unit/test_phase14_gap_modules.py` | `18 passed in 6.00s` |
| Missing importability gate for non-exempt runtime modules | `tests/cases/unit/unit/test_phase14_import_coverage.py` | `131 passed in 17.74s`; combined with helper gap tests: `149 passed in 9.33s` |
| D-04 documented exemptions not applied at report stage | `.coveragerc` | `coverage report --rcfile=.coveragerc` now omits types, compatibility, and formatter modules at report time |
| Hidden `.ruff` implementation package counted in coverage scope | `.coveragerc` | Added `*/.ruff/*` to run/report omits |
| Cucumber formatter E2E real-entrypoint test dropped fake Node runtime and asserted stale summary text | `tests/cases/e2e/e2e/test_cucumber_formatters.py` | focused test: `1 passed in 21.90s` |

---

## Manual-Only / Deferred Verifications

| Behavior | Requirement | Why Manual / Deferred | Evidence |
|----------|-------------|-----------------------|----------|
| Aggregate coverage >=70% | TEST-01 | Still below target after added tests and documented D-04 report omits. Latest report-stage coverage is 56%, with 91 of 134 non-exempt modules still below 70% in `coverage.json` scope analysis. | `uv run coverage report --rcfile=.coveragerc --fail-under=70` exits red |
| Per-module coverage >=70% | TEST-01 | Requires broad additional test investment across live reporting, scenario collection, steps, parser, and utility modules. | Lowest remaining modules include `const.py`, `mimetype.py`, `message_validation.py`, hook/const modules, and live formatter runtime files |
| Full `tests/cases/` green in this environment | TEST-02 | Full run has external/environment failures: Docker Desktop missing and missing remote_xdist Docker assets. The focused cucumber formatter output mismatch found during this validation pass is fixed, but full suite was not rerun afterward because the previous E2E run took 47m40s. | Full prior run: 16 failed, 1520 passed, 20 skipped, 54.88% raw coverage; focused formatter verification now passes |

## Validation Audit 2026-05-20 (second pass)

| Metric | Count |
|--------|-------|
| Gaps found | 2 |
| Resolved | 1 |
| Escalated | 1 |

**Resolved:** `test_console_formatter_emits_output_via_real_entrypoint` now preserves the fake Node runtime when invoking the real pytest entrypoint and asserts the shared expected summary formatter line. Focused verification passes.

**Added validation:** `test_phase14_import_coverage.py` imports all non-exempt `pytest_bdd` modules and fails if a runtime module cannot be imported under the project test environment.

**Escalated:** TEST-01 coverage remains below the 70% threshold. The last complete report-stage audit before this pass measured 56%; reaching 70% requires broad behavior tests across high-miss modules including live formatter runtime, StructBDD model/parser, scenario collection, parser/step internals, and message transport/validation helpers.

---

## Validation Audit 2026-05-20

| Metric | Count |
|--------|-------|
| Gaps found | 4 |
| Resolved | 3 |
| Escalated | 1 |

**Resolved:** generated docs, focused helper-module tests, `.coveragerc` report-stage omit parity with documented D-04 exemptions.

**Escalated:** TEST-01 70% aggregate/per-module coverage remains incomplete.

## Validation Sign-Off

- [x] Input state detected: existing `14-VALIDATION.md` audited
- [x] PLAN/SUMMARY artifacts read
- [x] Test infrastructure detected
- [x] Gap plan selected: fix all feasible gaps
- [x] Missing docs and focused tests generated
- [x] Focused formatter E2E regression fixed
- [ ] TEST-01 coverage threshold satisfied
- [ ] Full suite green in local environment
- [ ] `nyquist_compliant: true`

**Approval:** partial; retry after coverage closer and external test environment setup.
