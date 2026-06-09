# SPEC: CCK Allure Compatibility Pipeline

## Goal
Validate that pytest-bdd-ng's allure-cucumber converter correctly renders all 45 Cucumber Compatibility Kit (CCK) sample NDJSON files as Allure HTML reports, verified via Playwright browser automation.

## User Story
As a pytest-bdd-ng developer, I want to verify that the allure-cucumber converter can process every official CCK sample NDJSON file and produce a valid, renderable Allure HTML report, so that I can ensure compatibility with the Cucumber ecosystem.

## Success Criteria
- [ ] All 45 CCK sample NDJSON files are fetched from the latest release (v29.2.2) without cloning the repository
- [ ] Each NDJSON file is converted to Allure results via the allure-cucumber converter
- [ ] Each Allure results directory is rendered to an HTML report via Docker
- [ ] Each HTML report is served and validated via Playwright browser automation
- [ ] Validation confirms specific UI elements are visible: scenario names, step names, test statuses
- [ ] The pipeline runs as BDD feature scenarios with contract test edge cases
- [ ] Tests are marked with appropriate markers: `@browser`, `@docker`, `@slow`, `@contract`

## Scope

### In Scope
- CCK NDJSON download fixture (session-scoped, GitHub API)
- NDJSON → Allure conversion (existing `convert()` function)
- Allure HTML report generation (Docker-based)
- Playwright browser validation of rendered reports
- BDD feature file for the pipeline
- Contract tests for edge cases (empty NDJSON, malformed files, etc.)

### Out of Scope
- Message-level comparison between pytest-bdd-ng output and CCK NDJSON
- Visual snapshot comparison (only element visibility checks)
- CCK step definition execution (we only consume the NDJSON, not run the features)
- Allure report comparison across samples (each is validated independently)

## Architecture

```
cucumber/compatibility-kit v29.2.2
  └─ devkit/samples/*.ndjson
        │
        ▼ (session-scoped fixture, gh api / raw.githubusercontent.com)
        │
  tests/cases/contract/cck/fixtures/
        │
        ▼ (per-sample conversion)
  pytest-bdd-ng allure-cucumber converter
        │ (ndjson → allure-results/)
        ▼
  Docker: frankescobar/allure-docker-service:2.27.0
        │ (allure-results → allure-report/)
        ▼
  _serve_directory() HTTP server
        │
        ▼
  Playwright Chromium browser
        │ (assert visible elements)
        ▼
  PASS/FAIL per sample
```

## File Structure

```
features/
  17 Allure Converter/
    3 CCK Allure compatibility.feature.md     # BDD scenarios for the pipeline

tests/
  cases/
    contract/
      cck/
        __init__.py
        conftest.py                        # Shared fixtures (download, convert, docker, serve)
        test_cck_allure_conversion.py      # Contract tests for conversion edge cases
        test_cck_allure_rendering.py       # Playwright validation tests (parameterized)
    e2e/
      steps_cck_allure.py                  # Step definitions for the BDD feature

src/pytest_bdd/
  testing/
    cck.py                                 # CCK download utility (session-scoped)
```

## Key Design Decisions

### 1. CCK Download Strategy
- Use `gh api repos/cucumber/compatibility-kit/contents/devkit/samples/{name}/{name}.ndjson?ref=v29.2.2` for each sample
- Cache in `tmp_path` with session scope to avoid re-downloading
- Fallback to `raw.githubusercontent.com` if `gh` is unavailable
- Store the release tag as a constant for easy updates

### 2. Conversion Strategy
- Use the existing `convert()` function from `allure_cucumber.converter.converter`
- Each sample gets its own `allure-results/` directory
- Validate that `*-result.json` and `*-container.json` files are created

### 3. Docker Allure Strategy
- Reuse the existing `_run_allure_docker()` pattern from `test_allure_consumption_ui.py`
- Image: `frankescobar/allure-docker-service:2.27.0`
- Mount `allure-results/` read-only, write to `allure-report/`
- Skip gracefully if Docker is unavailable

### 4. Playwright Validation Strategy
- Reuse the `_serve_directory()` context manager pattern
- Reuse `_resolve_playwright_browsers_path()` for browser resolution
- Assert visibility of: scenario names, step names, status indicators
- Capture `pageerror` and `console` errors
- Parameterize across all 45 CCK samples

### 5. BDD Feature Structure
- Feature file in `features/17 Allure Converter/`
- Scenarios parameterized via background steps
- Step definitions in `tests/cases/e2e/steps_cck_allure.py`
- Registered via `pytest_plugins` in the E2E test entry point

## Edge Cases (Contract Tests)

1. **Empty NDJSON file** - Should produce no allure results, no crash
2. **Single-line NDJSON** (only `testRunStarted`) - Should produce minimal output
3. **NDJSON with failed scenarios** - Should render failure status in Allure
4. **NDJSON with attachments** - Should render attachment links
5. **NDJSON with data tables** - Should render table data
6. **NDJSON with doc strings** - Should render doc string content
7. **NDJSON with rules** - Should render rule structure
8. **NDJSON with examples tables** - Should render scenario outlines
9. **NDJSON with hooks** - Should render hook information
10. **NDJSON with retry** - Should render retry attempts

## Test Markers

- `@pytest.mark.docker` - Requires Docker daemon
- `@pytest.mark.browser` - Requires Playwright browsers
- `@pytest.mark.slow` - Excluded from short runs
- `@pytest.mark.contract` - Contract test suite

## Dependencies

- Existing: `allure_cucumber.converter`, `testing.docker`, `playwright`
- New: `gh` CLI or `raw.githubusercontent.com` for CCK download
- Docker image: `frankescobar/allure-docker-service:2.27.0`

## Risk Mitigation

1. **CCK download failure** - Cache downloads, skip tests if unavailable
2. **Docker unavailable** - Skip with clear message, run conversion-only tests
3. **Playwright unavailable** - Skip with clear message, run Docker-only tests
4. **Allure converter incompatibility** - Log warnings, don't fail the entire suite
5. **Large NDJSON files** - Set timeout limits, process incrementally
