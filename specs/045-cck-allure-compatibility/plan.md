# Implementation Plan: CCK Allure Compatibility Pipeline

## Phase 1: Infrastructure (Foundation)
**Goal:** Build the reusable infrastructure components

### Task 1.1: CCK Download Utility
**File:** `src/pytest_bdd/testing/cck.py`

Create a utility module for downloading CCK sample NDJSON files:
- `CCK_SAMPLE_NAMES: list[str]` - All 45 sample names
- `CCK_RELEASE_TAG: str = "v29.2.2"` - Latest release tag
- `CCK_REPO: str = "cucumber/compatibility-kit"` - Repository
- `download_cck_sample(name: Path, tag: str) -> Path` - Downloads a single NDJSON file
- `download_all_cck_samples(cache_dir: Path, tag: str) -> dict[str, Path]` - Downloads all samples
- Use `subprocess.run(["gh", "api", ...])` with fallback to `urllib.request`
- Cache downloads in the provided directory

### Task 1.2: Session-Scoped CCK Fixture
**File:** `tests/cases/contract/cck/conftest.py`

Create fixtures for CCK sample management:
- `cck_samples_dir(tmp_path_factory) -> Path` - Session-scoped directory for all samples
- `cck_samples(cck_samples_dir) -> dict[str, Path]` - Session-scoped download of all samples
- `cck_sample(request) -> Path` - Parameterized fixture for a single sample
- `allure_output(cck_sample, tmp_path) -> Path` - Converts a single sample to Allure results
- `allure_report(allure_output, tmp_path) -> Path` - Generates HTML report via Docker

### Task 1.3: Docker Allure Helper
**File:** `tests/cases/contract/cck/conftest.py` (extend existing)

Reuse the existing `_run_allure_docker()` pattern:
- `generate_allure_report(allure_results: Path, output_dir: Path) -> Path`
- Uses `frankescobar/allure-docker-service:2.27.0`
- Returns path to generated report directory
- Skips gracefully if Docker is unavailable

### Task 1.4: Playwright Helpers
**File:** `tests/cases/contract/cck/conftest.py` (extend existing)

Reuse existing patterns from `test_messages_feature_suite.py`:
- `_resolve_playwright_browsers_path() -> Path | None`
- `_serve_directory(directory: Path) -> Generator[str, None, None]`
- `playwright_browser() -> Generator[Browser, None, None]` - Fixture that provides a browser instance

## Phase 2: Contract Tests (Edge Cases)
**Goal:** Validate conversion edge cases with class-based tests

### Task 2.1: Conversion Contract Tests
**File:** `tests/cases/contract/cck/test_cck_allure_conversion.py`

Test the allure-cucumber converter with CCK samples:
- `TestCCKAllureConversion` class with `@pytest.mark.contract`
- `test_all_samples_produce_allure_results(cck_samples)` - Parameterized over all 45 samples
- `test_all_results_validate_against_schema(allure_output)` - Schema validation
- `test_all_results_have_required_fields(allure_output)` - Field presence checks
- `test_empty_ndjson_produces_no_results()` - Edge case: empty file
- `test_single_line_ndjson_produces_minimal_output()` - Edge case: only testRunStarted
- `test_failed_scenarios_render_failure_status()` - Edge case: failed scenarios

### Task 2.2: Docker Report Generation Tests
**File:** `tests/cases/contract/cck/test_cck_allure_rendering.py`

Test Docker-based report generation:
- `TestCCKAllureRendering` class with `@pytest.mark.contract`, `@pytest.mark.docker`
- `test_all_samples_generate_html_report(allure_report)` - Parameterized over all 45 samples
- `test_report_index_html_exists(allure_report)` - Basic file existence
- `test_report_contains_scenario_data(allure_report)` - Data presence checks

## Phase 3: BDD Feature (Full Pipeline)
**Goal:** Create BDD scenarios for the complete pipeline

### Task 3.1: Feature File
**File:** `features/17 Allure Converter/3 CCK Allure compatibility.feature.md`

```markdown
# Feature: CCK Allure Compatibility
  Validate that pytest-bdd-ng's allure-cucumber converter correctly renders
  all Cucumber Compatibility Kit samples as Allure HTML reports.

## Background:
* Given the CCK sample "minimal" is available
* And the allure-cucumber converter processes the sample
* And the Allure HTML report is generated via Docker

## Scenario: Allure report renders scenario names
* When the report is served via HTTP
* And the browser navigates to the report
* Then the scenario name "cukes" is visible

## Scenario: Allure report renders step names
* When the report is served via HTTP
* And the browser navigates to the report
* Then the step "I have 42 cukes in my belly" is visible

## Scenario: Allure report renders test status
* When the report is served via HTTP
* And the browser navigates to the report
* Then the test status "passed" is visible
```

### Task 3.2: Step Definitions
**File:** `tests/cases/e2e/steps_cck_allure.py`

Implement step definitions for the BDD feature:
- `@given(parsers.parse('the CCK sample "{name}" is available'))` - Downloads/loads sample
- `@given("the allure-cucumber converter processes the sample"))` - Runs conversion
- `@given("the Allure HTML report is generated via Docker"))` - Runs Docker generation
- `@when("the report is served via HTTP"))` - Starts HTTP server
- `@when("the browser navigates to the report"))` - Opens Playwright browser
- `@then(parsers.parse('the scenario name "{name}" is visible'))` - Asserts visibility
- `@then(parsers.parse('the step "{step}" is visible'))` - Asserts visibility
- `@then(parsers.parse('the test status "{status}" is visible'))` - Asserts visibility

### Task 3.3: Register Step Definitions
**File:** `tests/cases/e2e/e2e/test_e2e.py`

Add `tests.cases.e2e.steps_cck_allure` to the `pytest_plugins` list.

## Phase 4: Parameterized Playwright Tests
**Goal:** Validate all 45 samples via Playwright

### Task 4.1: Parameterized Rendering Tests
**File:** `tests/cases/contract/cck/test_cck_allure_rendering.py` (extend)

Add Playwright-based tests:
- `TestCCKAllureUIValidation` class with `@pytest.mark.browser`, `@pytest.mark.docker`, `@pytest.mark.slow`
- `test_cck_sample_renders_in_browser(cck_sample, allure_output, allure_report)` - Parameterized
- Inside the test:
  1. Serve the report directory via HTTP
  2. Launch Chromium via Playwright
  3. Navigate to the report
  4. Assert visibility of scenario names (extracted from NDJSON)
  5. Assert visibility of step names (extracted from NDJSON)
  6. Assert no page errors or console errors
  7. Cleanup: close browser, stop server

### Task 4.2: Extract Test Data from NDJSON
**File:** `tests/cases/contract/cck/conftest.py` (extend)

Add helper to extract expected data from NDJSON:
- `extract_scenario_names(ndjson_path: Path) -> list[str]` - Parses pickle names
- `extract_step_texts(ndjson_path: Path) -> list[str]` - Parses step texts
- `extract_expected_status(ndjson_path: Path) -> str` - Parses testStepResult.status

## Phase 5: Integration & Polish
**Goal:** Integrate into existing test infrastructure

### Task 5.1: Update E2E Test Entry Point
**File:** `tests/cases/e2e/e2e/test_e2e.py`

- Add `steps_cck_allure` to `pytest_plugins`
- Ensure the CCK feature is collected by `scenarios(".", filter_=...)`

### Task 5.2: Update Markers
**File:** `pyproject.toml`

- Verify `@pytest.mark.contract`, `@pytest.mark.docker`, `@pytest.mark.browser`, `@pytest.mark.slow` are defined
- Add any new markers if needed

### Task 5.3: Documentation
**File:** `docs/architecture/cck-compatibility.md` (optional)

Document the CCK compatibility pipeline architecture and how to run the tests.

## Execution Order

1. **Phase 1** (Infrastructure) - Build foundation first
2. **Phase 2** (Contract Tests) - Validate conversion without browser
3. **Phase 4.1-4.2** (Parameterized Playwright) - Add browser validation
4. **Phase 3** (BDD Feature) - Create BDD scenarios
5. **Phase 5** (Integration) - Wire everything together

## Verification

After implementation, run:
```bash
# Contract tests only (no browser, no Docker)
pytest tests/cases/contract/cck/ -m contract -m not docker -m not browser

# With Docker
pytest tests/cases/contract/cck/ -m contract -m docker

# With Playwright + Docker
pytest tests/cases/contract/cck/ -m contract -m docker -m browser

# Full BDD feature
pytest tests/cases/e2e/ -k cck

# All together
pytest tests/cases/contract/cck/ tests/cases/e2e/ -m "contract or e2e" -m "docker or browser"
```
