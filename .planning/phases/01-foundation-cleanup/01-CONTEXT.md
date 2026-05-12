# Phase 1: Foundation Cleanup - Context

**Gathered:** 2026-05-12
**Status:** Ready for planning

## Phase Boundary

Remove user-facing dead code and configuration that causes confusion. This phase eliminates the non-functional Allure logger plugin entrypoint and the legacy `--cucumberjson` CLI flag. No new features — pure removal and cleanup.

## Implementation Decisions

### Allure Plugin Removal
- **D-01:** Remove the dead `pytest-bdd-allure-logger` entrypoint from `pyproject.toml` (`[project.entry-points.pytest11]` line 87)
- **D-02:** Delete the entire `src/pytest_bdd/plugin/allure_logger/` directory (entrypoint.py with commented-out implementation, plugin.py with 289 unreachable lines)
- **D-03:** Remove `allure` optional dependency group from `pyproject.toml` (`[project.optional-dependencies]` — drops `allure-python-commons` and `allure-pytest`)
- **D-04:** Remove `[allure]` reference from `full` extra in `pyproject.toml`
- **D-05:** Remove `allure-python-commons-test` from `test` extra in `pyproject.toml`
- **D-06:** Remove allure-related tests and conftest files (`tests/e2e/allure/`, `tests/allure_/`)
- **D-07:** Remove ruff ERA001 suppression for `src/pytest_bdd/compatibility/allure.py` and `src/pytest_bdd/plugin/allure_logger/entrypoint.py` from `pyproject.toml` `[tool.ruff.lint.per-file-ignores]`
- **D-08:** Re-implementation of Allure integration (making it functional) is **deferred to a later phase** — this phase only removes dead code

### Legacy CLI Flag Removal
- **D-09:** Delete `--cucumberjson` option from `src/pytest_bdd/plugin/cucumber_json/entrypoint.py` `pytest_addoption()` function — remove the `group.addoption("--cucumberjson", ...)` call entirely
- **D-10:** No deprecation warning, no error hint, no transitional period — direct removal. The `--cucumber-json` flag remains as the sole CLI option
- **D-11:** Remove the `# TODO: we dont't need legacy support for this option anymore` comment along with the flag

### DEPRECATIONS.md
- **D-12:** DEPRECATIONS.md is **not created in this phase** — no deprecations are being introduced (everything is direct removal, not deprecation). Future phases that need deprecation paths (e.g., if any feature gets a transitional period) will create it at that time

### the agent's Discretion
- Exact line cleanup order within entrypoint.py and pyproject.toml
- Whether to consolidate any remaining allure-related imports in compatibility/allure.py or remove it entirely
- Test file cleanup approach

## Specific Ideas

- "Delete without ceremony" — no transitional period for either the Allure plugin or --cucumberjson
- Allure re-implementation deferred: the existing plugin.py code (289 lines) and PatchedAllureListener logic is archived by deletion, not preserved for later — re-implementation will be from scratch against current Allure APIs if it happens later

## Canonical References

### Plugin system
- `pyproject.toml` — Entry point registration (`[project.entry-points.pytest11]`), optional dependencies (`[project.optional-dependencies]`), ruff per-file-ignores (`[tool.ruff.lint.per-file-ignores]`)
- `src/pytest_bdd/plugin/allure_logger/entrypoint.py` — Dead entrypoint to remove
- `src/pytest_bdd/plugin/allure_logger/plugin.py` — Unreachable implementation to delete
- `src/pytest_bdd/plugin/cucumber_json/entrypoint.py` — `pytest_addoption` containing legacy `--cucumberjson` flag to delete
- `src/pytest_bdd/compatibility/allure.py` — Allure compatibility shim, may need cleanup

### Requirements and roadmap
- `.planning/ROADMAP.md` — Phase 1 details, success criteria
- `.planning/REQUIREMENTS.md` — STAB-01 (Allure) and STAB-04 (cucumberjson) definitions
- `.planning/codebase/CONCERNS.md` §"Allure Logger Plugin" and §"Legacy --cucumberjson Option" — Detailed diagnosis

## Existing Code Insights

### Reusable Assets
- None — this phase only removes dead code, no new patterns introduced

### Established Patterns
- Plugin entrypoint registration via `[project.entry-points.pytest11]` — removal must follow the same TOML section structure
- Optional dependencies via `[project.optional-dependencies]` — removal must keep remaining extras intact (`async`, `doc-gen`, `full`, `test`)
- Ruff per-file-ignores in `pyproject.toml` — avoid stale suppression entries after file deletion

### Integration Points
- `full` extra in pyproject.toml references `pytest-bdd-ng[allure]` — must remove this reference
- `test` extra references `allure-python-commons-test` — must remove
- `mypy` config references `allure_commons.*` — must remove
- Test group config (`[tool.pytest.ini_options]`) references `tests/allure_/**` — must remove
- Existing tests under `tests/e2e/allure/` and `tests/allure_/` — must delete or repurpose

## Deferred Ideas

- **Allure re-implementation:** Making the Allure integration functional (wiring up AllureLogger + PatchedAllureListener) — deferred to a future phase after stabilization is complete
- **Other legacy CLI flags:** Audit for other deprecated/undocumented options — Phase 11 (Audit & Prune)

---

*Phase: 01-foundation-cleanup*
*Context gathered: 2026-05-12*
