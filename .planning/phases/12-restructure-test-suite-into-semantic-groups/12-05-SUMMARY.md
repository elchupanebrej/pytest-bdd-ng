---
phase: 12-restructure-test-suite-into-semantic-groups
plan: 05
subsystem: documentation
tags: [development-guide, feature-docs, generated-drift]
requires:
  - phase: 12-restructure-test-suite-into-semantic-groups
    plan: 04
    provides: Makefile API, semantic test groups, env-check/env-install pattern
provides:
  - DEVELOPMENT.rst updated with semantic test workflow documentation
  - Environment validation vs provisioning pattern documented
  - pytest_bdd.testing marked as internal project infrastructure
  - Generated feature docs consistent with feature sources
affects: [phase-12, documentation]
tech-stack:
  added: []
  patterns:
    - DEVELOPMENT.rst documents only Makefile API for running tests
    - env-check (read-only) vs env-install (explicit provisioning) documented
    - Internal test helpers under src/pytest_bdd/testing/ noted as non-public
key-files:
  created: []
  modified:
    - path: DEVELOPMENT.rst
      reason: Rewrote Testing Strategy, Running Tests, BDD Workflow, Plugin Development Lifecycle, Development Workflow, and Available Commands sections to document semantic test groups and Makefile API
    - path: docs/features/12 Formatters/01 JUnit XML reporter.feature.rst
      reason: Regenerated via bdd_tree_to_rst; minor test count drift (1 -> 2 passed) from feature source changes
---

# Plan 12-05: Update Contrib Docs and Handle Generated Docs Drift

**Objective:** Update contributor docs and handle generated docs drift after test/e2e restructure.

## Task 1: Document Semantic Test Workflow

**Artifact:** `DEVELOPMENT.rst`

### Changes Made

**Testing Strategy section** — replaced old four-tier structure (`tests/unit/`, `tests/feature/`, `tests/e2e/`, `tests/messages/`) with:

- Seven semantic groups under `tests/cases/`: unit, integration, contract, e2e, compat, perf, external
- `tests/assets/` documented as passive data only
- `src/pytest_bdd/testing/` noted as internal project infrastructure, not public API (D-13)
- Speed facet: `@pytest.mark.slow`
- Environment facets: `@pytest.mark.docker`, `@pytest.mark.windows`, `@pytest.mark.posix`, `@pytest.mark.browser`
- Environment validation (read-only `env-check-*`) vs provisionaing (explicit `env-install-*`) documented (D-19)
- Makefile Test API documented as human entrypoint (D-19, D-20)
- Old `uv run pytest tests/ -x` replaced with `uv run python -m pytest tests/cases -m "not slow and not docker and not windows and not browser and not external"`

**BDD Workflow section** — updated paths to `tests/cases/e2e/conftest.py`, commands to `make features-docs` and `make test-e2e`

**Plugin Development Lifecycle** — step 6 updated to reference `tests/cases/unit/` and `tests/cases/integration/`

**Running Tests section** — Make is documented as recommended human entrypoint; quick pytest command uses semantic selector

**Development Workflow** — updated to use `make test-unit`, `make test-integration`, `make test-all`

**Available Commands** — `make test` description corrected from "tox" to "default feasible test suite"; `uv run pytest <test_path>` replaced with `uv run python -m pytest tests/cases/<group>/<file>`

### Acceptance Criteria

- DEVELOPMENT.rst mentions all seven semantic groups — **PASS**
- DEVELOPMENT.rst documents env-check as read-only and env-install as explicit provisioning — **PASS**
- DEVELOPMENT.rst does not present tests/support as current helper location — **PASS** (no `tests/support` or `quick-test` references remain)

## Task 2: Regenerate Feature Docs

**Command:** `uv run bdd_tree_to_rst features docs/features`

**Exit code:** 0

**Result:** `bdd_tree_to_rst` reported 2 differing files internally; only 1 produced a git diff:

- `docs/features/12 Formatters/01 JUnit XML reporter.feature.rst` — test count changed from `1 passed` to `2 passed` (expected drift from feature source changes)

**Verdict:** Generated docs drift is source-driven, not a sign of forbidden test loader patterns. Accepted per plan guidance: "If generated docs drift because feature files or loaders moved, accept regenerated docs/features output."

### Acceptance Criteria

- make features-docs exits 0 — **PASS** (via `uv run bdd_tree_to_rst`)
- git diff docs/features is either empty or contains only regenerated output from feature sources — **PASS** (1 file, source-driven count drift)
- Generated docs are not used as evidence of forbidden test loader shape — **PASS**

## Verification

`rg -n "tests/support|quick-test" DEVELOPMENT.rst docs --glob '!docs/superpowers/**'` — no matches.

## Summary

DEVELOPMENT.rst now documents the semantic test structure described in the Phase 12 design doc. All old path references (`tests/unit/`, `tests/feature/`, `tests/support`, `quick-test`) are removed or updated. Feature docs are regenerated and consistent with current feature sources.
