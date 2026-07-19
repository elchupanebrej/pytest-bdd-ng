# Phase 24: docs/architecture/allure.md - Context

**Gathered:** 2026-06-11
**Status:** Ready for execution

<domain>
## Phase Boundary

CCK Allure Compatibility Pipeline (Wave 6): Validate the allure-cucumber converter against all 45 official CCK sample NDJSON files via Docker-based HTML report generation and Playwright browser automation. Includes contract tests for conversion edge cases and a BDD feature file documenting the pipeline.

</domain>

<decisions>
## Implementation Decisions

### Verification Strategy
- **D-01:** Wave 6 code already exists — verify existing implementation, do not rebuild
- **D-02:** Run contract tests first (`pytest tests/cases/contract/cck/ -m contract -m not docker -m not browser`), then Docker tests, then Playwright tests
- **D-03:** Graceful degradation is acceptable — Docker/Playwright/gh CLI skips with clear message when unavailable

### the agent's Discretion
- Agent decides verification order and what constitutes "done" for marking Wave 6 complete in ROADMAP

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### CCK Implementation
- `src/pytest_bdd/testing/cck.py` — CCK download utility with session-scoped caching
- `tests/cases/contract/cck/conftest.py` — Shared fixtures (download, convert, docker, serve)
- `tests/cases/contract/cck/test_cck_allure_conversion.py` — Conversion contract tests
- `tests/cases/contract/cck/test_cck_allure_rendering.py` — Docker + Playwright rendering tests
- `features/17 Allure Converter/3 CCK Allure compatibility.feature.md` — BDD feature file

### Prior Phase Infrastructure
- `src/pytest_bdd/plugin/allure_cucumber/converter/converter.py` — convert() function (Wave 2)
- `tests/cases/contract/allure/test_allure_consumption_ui.py` — _run_allure_docker() pattern (Wave 4)
- `tests/cases/contract/messages/test_messages_feature_suite.py` — _serve_directory(), _resolve_playwright_browsers_path() patterns
- `src/pytest_bdd/testing/docker.py` — require_docker_daemon() helper

### Planning
- `.planning/phases/24-docs-architecture-allure-md/24-06-PLAN.md` — Wave 6 plan with task breakdown
- `.planning/REQUIREMENTS.md` — CCK-01 through CCK-07 requirements
- `.planning/intel/requirements.md` — Synthesized CCK requirements from ingested specs
- `.planning/intel/constraints.md` — CCK constraints (release tag, Docker image, markers, graceful degradation)

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `src/pytest_bdd/testing/cck.py` — Complete CCK download utility with 45 sample names, gh API + urllib fallback, extract helpers
- `tests/cases/contract/cck/conftest.py` — Complete fixture layer: cck_samples, cck_sample, allure_output, allure_report, _serve_directory, _resolve_playwright_browsers_path
- `tests/cases/contract/cck/test_cck_allure_conversion.py` — Conversion tests including edge cases
- `tests/cases/contract/cck/test_cck_allure_rendering.py` — Docker and Playwright validation tests

### Established Patterns
- `_run_allure_docker()` from test_allure_consumption_ui.py — Docker report generation pattern
- `_serve_directory()` from test_messages_feature_suite.py — HTTP server context manager
- `_resolve_playwright_browsers_path()` from test_messages_feature_suite.py — Browser resolution
- Class-based test pattern with `@pytest.mark.contract`, `@pytest.mark.docker`, `@pytest.mark.browser`, `@pytest.mark.slow`

### Integration Points
- `tests/cases/e2e/e2e/test_e2e.py` — E2E entry point needs `steps_cck_allure` in pytest_plugins
- `features/17 Allure Converter/` — BDD feature file location

</code_context>

<specifics>
## Specific Ideas

No specific requirements — code exists and follows established patterns.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 20-docs-architecture-allure.md*
*Context gathered: 2026-06-11*
