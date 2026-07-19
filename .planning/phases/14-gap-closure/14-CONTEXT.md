# Phase 14: Gap Closure - Context

**Gathered:** 2026-05-20
**Status:** Ready for planning

<domain>
## Phase Boundary

Close the v1.0 milestone by addressing two deferred testing requirements (TEST-01, TEST-02) and folding in all remaining pending items from STATE.md:

1. Raise unit test line+branch coverage from 56% to 70% (per-module minimum, exempting entrypoints/scripts)
2. Resolve all 27 failing BDD feature tests with zero remaining failures
3. Apply Phase 12 D-18 E2E module-per-feature-file split
4. Fold in: migrate 6 test files to tests/unit/, write model module tests, write steps.py testdir tests, extend parser tests + pragma audit, expand feature tests for undocumented behaviors

This is a testing-only phase. No production behavior changes except bug fixes discovered during BDD triage.
</domain>

<decisions>
## Implementation Decisions

### Coverage Strategy
- **D-01:** Broad coverage augmentation — write tests across all modules evenly, not focused on a specific subset
- **D-02:** Mix of unit tests (tests/unit/, tests/model/) and integration tests (testdir-based in tests/feature/) to carry the coverage lift
- **D-03:** Per-module minimum threshold of 70% line+branch coverage on `src/pytest_bdd/`
- **D-04:** entrypoint.py files, script/ modules, and the _gherkin_go/ ctypes bridge are exempt from the per-module 70% threshold — tested adequately by integration/e2e
- **D-05:** Quick coverage gap scan first — run coverage report to identify biggest uncovered functions/classes per module, start with easy wins (error paths, edge cases), then tackle complex gaps

### BDD Fix Strategy
- **D-06:** Automated triage first — run suite with verbose failure output, script-categorize failures by error type (StepNotFound, AssertionError, etc.), then review and fix by category
- **D-07:** Case-by-case judgment for step-def vs feature-file fixes: if the feature describes intended behavior, implement the missing step definition; if the feature describes outdated/wrong behavior, update the feature file
- **D-08:** Fix production code bugs discovered during BDD triage — do not defer them. The phase delivers "all BDD tests pass" regardless of root cause
- **D-09:** Single full-suite verification run at the end after all fixes are applied
- **D-10:** Split E2E test modules per feature file as part of the fix — apply Phase 12 D-18 rule. Each E2E module must bind only its owned feature file(s). Whole-directory scenario loaders are forbidden. Replaces the current `tests/e2e/test_e2e.py` with per-file modules

### Folded Pending Items
- **D-11:** Migrate 6 remaining test files to tests/unit/ with `@pytest.mark.unit` markers (from STATE.md pending)
- **D-12:** Write model module unit tests for run.py, scenario_run.py, feature_binding.py (from STATE.md pending)
- **D-13:** Write steps.py testdir-based integration tests (from STATE.md pending)
- **D-14:** Extend parser edge case tests for parsers.py (FROZEN — tests only, no modifications to parsers.py) + audit and justify or remove all `# pragma: no cover` instances (from STATE.md pending)
- **D-15:** Expand feature tests for undocumented behaviors — add new .feature.md files under features/ for gaps identified in Phase 8 audit (from STATE.md pending)

### the agent's Discretion
- Exact module-by-module test allocation within the broad augmentation strategy
- Specific test structure and naming, following established conventions (TESTING.md, CONVENTIONS.md)
- Order of triage categories after automated categorization of BDD failures
- File-by-file organization of the E2E module split
- Which specific undocumented behaviors to cover with new .feature.md files
- Per-file pragma audit decisions (keep justified, remove unjustified)
</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Roadmap and Requirements
- `.planning/ROADMAP.md` — Phase 14 entry: goal, success criteria, plans (14-01 coverage, 14-02 BDD fixes)
- `.planning/PROJECT.md` — Core value, constraints (ruff, attrs, StashBound, Python 3.10-3.14, pytest >=7.0.0), key decisions
- `.planning/REQUIREMENTS.md` — TEST-01 (70% coverage), TEST-02 (27 BDD failures), traceability

### Prior Phase Context
- `.planning/phases/13-unify-cucumber-json-plugins-ini-cli-options/13-CONTEXT.md` — Phase 13 dispatcher pattern, immediate dependency
- `.planning/phases/12-restructure-test-suite-into-semantic-groups/12-CONTEXT.md` — D-04 strict semantic classification, D-06 canonical groups (unit/integration/contract/e2e/compat/perf/external), D-18 per-file E2E module binding
- `.planning/phases/11-audit-prune/11-CONTEXT.md` — D-02/D-03/D-04 large file splits completed (steps.py, message_capability_governance, run.py), parsers.py FROZEN

### Codebase Maps
- `.planning/codebase/TESTING.md` — Test organization, patterns, fixtures, coverage config, test types by group
- `.planning/codebase/CONVENTIONS.md` — Naming, imports, error handling, attrs usage, docstring conventions
- `.planning/codebase/STRUCTURE.md` — Directory layout, plugin structure, where to add new code

### Test Infrastructure
- `pyproject.toml` — Pytest markers, test_group_paths, test_group_order, coverage config, ruff rules
- `.coveragerc` — Branch coverage enabled, includes `pytest_bdd/*` and `tests/*`
- `tox.ini` — Matrix engine and environment definitions
- `Makefile` — Human test entrypoint (Phase 12 D-19/D-21)

### Source to Test
- `src/pytest_bdd/model/run.py` — Runtime execution (split from scenario_run.py, Phase 3)
- `src/pytest_bdd/model/scenario_run.py` — Run, ScenarioRun, FeatureRuntimeBinding
- `src/pytest_bdd/model/feature_binding.py` — FeatureRuntimeBinding (split from scenario_run.py, Phase 3)
- `src/pytest_bdd/steps.py` — StepDefinitionManager with Registry, Matcher, Definition
- `src/pytest_bdd/parsers.py` — StepParser hierarchy (FROZEN — tests only)
- `tests/e2e/conftest.py` — BDD step definitions for feature files
- `tests/e2e/test_e2e.py` — Current monolithic E2E loader (to be split, D-10)

### BDD Feature Files
- `features/` — Executable BDD documentation (47 .feature.md files). Phase 8 audit identified gap list in 08-01-PLAN.md
- `tests/e2e/conftest.py` — Step definitions mapping Gherkin steps to test actions
</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `src/pytest_bdd/util/test_group_ordering.py` — Existing path-based group assignment and marker application logic; extend for new test files rather than duplicating
- Phase 3 characterization tests (`tests/feature/test_run_lifecycle.py`) — Reference for RunStage transition edge case coverage
- Phase 6 integration tests — Step matching priority contract tests and execution lifecycle tests as patterns for new integration tests
- `tests/support/` utilities — Shared test scaffolding (pytest_results.py, cucumber_formatters.py) now under `src/pytest_bdd/testing/` (Phase 12 D-12/D-13)

### Established Patterns
- Unit tests: Direct instantiation, `Path("/fake/...")` for path-like args, `pytest.raises` for error paths, descriptive function names
- Integration tests: `testdir.makefile()` + `testdir.makeconftest()` + `testdir.runpytest()` + `result.assert_outcomes()`
- Coverage: `uv run python -m pytest tests/ --cov=pytest_bdd --cov-report=html`
- Test markers: speed/platform/environment style markers, path-driven grouping via `test_group_paths`
- `attrs` `@define(slots=True)` for all data classes, `from __future__ import annotations` in all source files
- Plugin structure: `__init__.py` + `entrypoint.py` + `hook.py` + `plugin.py`
- No `return None` in non-hook code (Phase 2 gate)
- `parsers.py` is FROZEN — tests only, zero modifications

### Integration Points
- New tests under `tests/unit/` must follow path-driven semantic grouping in `pyproject.toml` `[tool.pytest.ini_options].test_group_paths`
- New test modules under `tests/feature/` or `tests/unit/` must update `test_group_paths` if they don't match existing glob patterns
- E2E module split must update `tests/e2e/` loader imports, `scenarios()` calls, and any hardcoded test paths in CI/tox/Makefile
- Per-module coverage threshold requires `.coveragerc` or coverage configuration updates
- Adding new .feature.md files requires corresponding step definitions in `tests/e2e/conftest.py` (or per-module step defs after split)
</code_context>

<specifics>
## Specific Ideas

- Coverage gap scan should identify the biggest uncovered functions per module — error handlers, edge cases, and branch paths are often the lowest-hanging fruit
- E2E split should follow the Phase 8 audit's gap list (08-01-PLAN.md) to understand which feature files lack coverage
- Pragma audit should distinguish between justified `# pragma: no cover` (defensive code, platform-specific paths, ctypes fallback) and unjustified (missing tests for reachable code)
- Model module tests for run.py, scenario_run.py, feature_binding.py should cover RunStage transitions, stash integration, and error paths — reference Phase 3 characterization tests
- Steps.py testdir tests should cover step registration, matching priority (specific beats generic), fixture injection, and error reporting
</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope. All STATE.md pending items were folded in.
</deferred>

---

*Phase: 14-gap-closure*
*Context gathered: 2026-05-20*
