---
status: complete
plan: 260611-allure3-docker
date: 2026-06-11
---

# Quick Task 260611-allure3-docker: Replace Allure 2 with Allure 3 - Summary

## Fix Status

| Area | Status | Details |
|------|--------|---------|
| Allure 3 Dockerfile | CREATED | Added under `tests/assets/docker/allure3/Dockerfile` |
| docker.py | UPDATED | Added `ensure_allure3_image` to build image on demand |
| Docker Command | UPDATED | Removed `--clean` (unsupported in Allure 3) and passed `/allure-results` |
| Test Assertions | UPDATED | Updated test case file queries to check `data/test-results/*.json` |
| Allure tests | PASSED | `test_allure_consumption_ui.py` passed all 5 tests |
| CCK tests | PASSED | `test_cck_allure_rendering.py` passed all 88 tests |

## Verification Details

1. **Allure 3 CLI Compatibility:**
   Allure 3 (TypeScript/Node-based) does not support the `--clean` argument, which was used in Allure 2. Removing it and providing the results directory argument correctly allowed Allure 3 to generate reports.
2. **Output Layout Differences:**
   Allure 3 structures test result JSON files under `data/test-results/*.json` instead of Allure 2's direct placement or `data/test-cases/*.json` structures. The tests in `test_allure_consumption_ui.py` were modernized to support both formats.
3. **Execution Results:**
   - `test_allure_consumption_ui.py` passed 5/5 tests (no skips!).
   - `test_cck_allure_rendering.py` passed 88/88 tests.

## Lessons Learned

- **Allure 3 CLI changes:** The transition from the Java-based `allure-commandline` to the TypeScript-based `allure` package simplifies the docker setup (no Java/JRE needed), but removes obsolete command flags like `--clean` and alters the internal report layout. Adapting test suites to check both Allure 2 and Allure 3 file paths makes the validation robust.
