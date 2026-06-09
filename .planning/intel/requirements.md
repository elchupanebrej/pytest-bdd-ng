# Requirements Intel

Extracted from classified SPEC documents.

---

## REQ-cck-allure-45-samples

**Source:** specs/045-cck-allure-compatibility/spec.md
**Type:** Functional requirement
**Description:** Validate that pytest-bdd-ng's allure-cucumber converter correctly renders all 45 CCK sample NDJSON files as Allure HTML reports, verified via Playwright browser automation.
**Acceptance Criteria:**
- All 45 CCK sample NDJSON files are fetched from the latest release (v29.2.2) without cloning the repository
- Each NDJSON file is converted to Allure results via the allure-cucumber converter
- Each Allure results directory is rendered to an HTML report via Docker
- Each HTML report is served and validated via Playwright browser automation
- Validation confirms specific UI elements are visible: scenario names, step names, test statuses
- The pipeline runs as BDD feature scenarios with contract test edge cases
- Tests are marked with appropriate markers: `@browser`, `@docker`, `@slow`, `@contract`

**Scope:** CCK NDJSON download, allure-cucumber converter, Allure HTML report generation, Playwright browser validation, Docker-based rendering, BDD feature scenarios, contract test edge cases

---

## REQ-cck-download-strategy

**Source:** specs/045-cck-allure-compatibility/spec.md
**Type:** Technical constraint / design decision
**Description:** Use `gh api` for CCK download with fallback to `raw.githubusercontent.com`. Cache in session-scoped `tmp_path`. Store release tag as a constant.
**Acceptance Criteria:**
- Session-scoped fixture downloads all 45 samples once per test session
- Fallback mechanism works when `gh` CLI is unavailable
- Downloads cached to avoid re-fetching

**Scope:** CCK download infrastructure

---

## REQ-cck-docker-allure

**Source:** specs/045-cck-allure-compatibility/spec.md
**Type:** Technical constraint
**Description:** Docker-based Allure HTML report generation using `frankescobar/allure-docker-service:2.27.0`. Mount `allure-results/` read-only, write to `allure-report/`.
**Acceptance Criteria:**
- Docker report generation reuses existing `_run_allure_docker()` pattern
- Graceful skip when Docker is unavailable
- Each sample produces an HTML report directory

**Scope:** Docker Allure rendering

---

## REQ-cck-playwright-validation

**Source:** specs/045-cck-allure-compatibility/spec.md
**Type:** Technical constraint
**Description:** Playwright browser validation of rendered Allure reports. Reuse `_serve_directory()` and `_resolve_playwright_browsers_path()` patterns. Parameterize across all 45 CCK samples.
**Acceptance Criteria:**
- Assert visibility of scenario names, step names, status indicators
- Capture `pageerror` and `console` errors
- Parameterized test across all 45 samples
- Graceful skip when Playwright is unavailable

**Scope:** Playwright browser validation

---

## REQ-cck-edge-cases

**Source:** specs/045-cck-allure-compatibility/spec.md
**Type:** Contract test requirements
**Description:** Contract tests for 10 edge cases in the conversion pipeline.
**Acceptance Criteria:**
1. Empty NDJSON file — produces no allure results, no crash
2. Single-line NDJSON (only `testRunStarted`) — produces minimal output
3. NDJSON with failed scenarios — renders failure status in Allure
4. NDJSON with attachments — renders attachment links
5. NDJSON with data tables — renders table data
6. NDJSON with doc strings — renders doc string content
7. NDJSON with rules — renders rule structure
8. NDJSON with examples tables — renders scenario outlines
9. NDJSON with hooks — renders hook information
10. NDJSON with retry — renders retry attempts

**Scope:** Contract test edge cases

---

## REQ-cck-bdd-feature

**Source:** specs/045-cck-allure-compatibility/plan.md
**Type:** Structural requirement
**Description:** BDD feature file at `features/17 Allure Converter/3 CCK Allure compatibility.feature.md` with step definitions in `tests/cases/e2e/steps_cck_allure.py`.
**Acceptance Criteria:**
- Feature file covers scenario name rendering, step name rendering, test status rendering
- Step definitions implement Given/When/Then for full pipeline
- Step definitions registered via `pytest_plugins` in E2E test entry point

**Scope:** BDD acceptance test structure

---

## REQ-cck-parameterized-rendering

**Source:** specs/045-cck-allure-compatibility/plan.md
**Type:** Structural requirement
**Description:** Parameterized Playwright tests for all 45 CCK samples with NDJSON data extraction helpers.
**Acceptance Criteria:**
- `TestCCKAllureUIValidation` class parameterized across all samples
- `extract_scenario_names()`, `extract_step_texts()`, `extract_expected_status()` helpers
- Tests serve report, launch Chromium, navigate, assert visibility, check no errors
- Markers: `@browser`, `@docker`, `@slow`

**Scope:** Parameterized test infrastructure
