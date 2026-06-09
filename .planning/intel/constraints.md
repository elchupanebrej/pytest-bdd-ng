# Constraints Intel

Extracted from classified SPEC documents.

---

## CONSTRAINT-001: CCK Release Version

**Source:** specs/045-cck-allure-compatibility/spec.md
**Type:** api-contract
**Content:** CCK samples must be fetched from release tag `v29.2.2` of `cucumber/compatibility-kit`. The release tag is stored as a constant (`CCK_RELEASE_TAG`) for easy updates. Download uses GitHub API: `gh api repos/cucumber/compatibility-kit/contents/devkit/samples/{name}/{name}.ndjson?ref=v29.2.2`.

---

## CONSTRAINT-002: Docker Image Version

**Source:** specs/045-cck-allure-compatibility/spec.md
**Type:** protocol
**Content:** Allure HTML report generation uses Docker image `frankescobar/allure-docker-service:2.27.0`. Reuses existing `_run_allure_docker()` pattern from `test_allure_consumption_ui.py`. Mount `allure-results/` read-only, write to `allure-report/`.

---

## CONSTRAINT-003: Test Markers

**Source:** specs/045-cck-allure-compatibility/spec.md
**Type:** nfr
**Content:** Tests must use four markers: `@pytest.mark.docker` (requires Docker daemon), `@pytest.mark.browser` (requires Playwright browsers), `@pytest.mark.slow` (excluded from short runs), `@pytest.mark.contract` (contract test suite).

---

## CONSTRAINT-004: Graceful Degradation

**Source:** specs/045-cck-allure-compatibility/spec.md
**Type:** nfr
**Content:** All external dependencies (Docker, Playwright, `gh` CLI) must degrade gracefully. If Docker unavailable, skip with clear message and run conversion-only tests. If Playwright unavailable, skip and run Docker-only tests. If `gh` unavailable, fallback to `raw.githubusercontent.com`.

---

## CONSTRAINT-005: Reuse Existing Patterns

**Source:** specs/045-cck-allure-compatibility/spec.md
**Type:** protocol
**Content:** Must reuse existing patterns from the codebase:
- `_run_allure_docker()` from `test_allure_consumption_ui.py`
- `_serve_directory()` context manager
- `_resolve_playwright_browsers_path()` for browser resolution
- `convert()` function from `allure_cucumber.converter.converter`

---

## CONSTRAINT-006: File Structure

**Source:** specs/045-cck-allure-compatibility/spec.md
**Type:** schema
**Content:** Files must be placed at:
- `src/pytest_bdd/testing/cck.py` — CCK download utility
- `tests/cases/contract/cck/conftest.py` — Shared fixtures
- `tests/cases/contract/cck/test_cck_allure_conversion.py` — Conversion contract tests
- `tests/cases/contract/cck/test_cck_allure_rendering.py` — Rendering + Playwright tests
- `tests/cases/e2e/steps_cck_allure.py` — Step definitions
- `features/17 Allure Converter/3 CCK Allure compatibility.feature.md` — BDD feature

---

## CONSTRAINT-007: Out of Scope Boundaries

**Source:** specs/045-cck-allure-compatibility/spec.md
**Type:** nfr
**Content:** Explicitly out of scope:
- Message-level comparison between pytest-bdd-ng output and CCK NDJSON
- Visual snapshot comparison (only element visibility checks)
- CCK step definition execution (consume NDJSON only, don't run features)
- Allure report comparison across samples (each validated independently)
