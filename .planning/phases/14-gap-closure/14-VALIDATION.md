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
| 14-03-01 | 03 | TEST-02 | e2e | `uv run --extra test --extra testtypes --extra doc-gen --extra struct-bdd python -m pytest tests/cases/e2e/e2e/ -v --tb=short --no-header` | not rerun in audit |
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
| D-04 documented exemptions not applied at report stage | `.coveragerc` | `coverage report --rcfile=.coveragerc` now omits types, compatibility, and formatter modules at report time |

---

## Manual-Only / Deferred Verifications

| Behavior | Requirement | Why Manual / Deferred | Evidence |
|----------|-------------|-----------------------|----------|
| Aggregate coverage >=70% | TEST-01 | Still below target after added tests and documented D-04 report omits. Latest report-stage coverage is 56%, with 91 of 134 non-exempt modules still below 70% in `coverage.json` scope analysis. | `uv run coverage report --rcfile=.coveragerc --fail-under=70` exits red |
| Per-module coverage >=70% | TEST-01 | Requires broad additional test investment across live reporting, scenario collection, steps, parser, and utility modules. | Lowest remaining modules include `const.py`, `mimetype.py`, `message_validation.py`, hook/const modules, and live formatter runtime files |
| Full `tests/cases/` green in this environment | TEST-02 | Full run has external/environment failures: Docker Desktop missing, missing remote_xdist Docker assets, and one cucumber formatter output mismatch. | Full run: 16 failed, 1520 passed, 20 skipped, 54.88% raw coverage |

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
- [ ] TEST-01 coverage threshold satisfied
- [ ] Full suite green in local environment
- [ ] `nyquist_compliant: true`

**Approval:** partial; retry after coverage closer and external test environment setup.
