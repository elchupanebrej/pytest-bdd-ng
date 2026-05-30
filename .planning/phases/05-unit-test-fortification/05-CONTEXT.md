# Phase 05: Unit Test Fortification - Context

**Gathered:** 2026-05-14
**Status:** Ready for planning

<domain>
## Phase Boundary

Comprehensive unit test coverage for 5 core modules (~2,400 lines): `steps.py` (630L), `model/run.py` (630L), `model/scenario_run.py` (282L), `model/feature_binding.py` (294L), and `parsers.py` (603L). Targets: >85% line coverage on model modules, >80% on steps.py. Parsers are frozen — test only via public API, no source modifications. All existing unit tests reorganized into `tests/unit/` by source module and tagged `@pytest.mark.unit`.

</domain>

<decisions>
## Implementation Decisions

## Coverage Prioritization & Ordering
- **D-01:** Order by user impact: `steps.py` first (highest support burden for step matching failures), then model modules (`run.py`, `scenario_run.py`, `feature_binding.py`), then `parsers.py` last.
- **D-02:** Approach: Systematic coverage density — fill every gap, not just edge cases. Run `pytest --cov=pytest_bdd.<module> --cov-report=term-missing` per-module for fast feedback loops.
- **D-03:** Parsers tested via public API only (`parse()`, `get_parser()`, step matchers). No internal/private function testing. Respects the parser freeze.

## Test Organization & Methodology
- **D-04:** Methodology: Hybrid approach. Direct unit tests (import + call + assert) for model modules (pure data classes, no pytest coupling). Testdir integration tests (`makefile` + `makeconftest` + `runpytest`) for `steps.py` (requires pytest runtime context for step registration and execution).
- **D-05:** All unit tests tagged with `@pytest.mark.unit`, registered in `pyproject.toml` under `[tool.pytest.ini_options].markers`.
- **D-06:** New unit tests placed in `tests/unit/` by source module tree: `tests/unit/model/test_run.py`, `tests/unit/model/test_scenario_run.py`, `tests/unit/model/test_feature_binding.py`, `tests/unit/test_steps.py`. New parser tests extend `tests/args/`.
- **D-07:** ALL existing unit tests retrofitted with `@pytest.mark.unit` and migrated into `tests/unit/` by source module. Integration/E2E tests (`tests/feature/`, `tests/e2e/`, `tests/messages/`) stay in current locations — not reorganized.

## Coverage Enforcement
- **D-08:** CI gate: 100% test pass rate. No per-module coverage thresholds in CI — the 85% and 80% targets are planning/execution goals, not CI fail_under gates.
- **D-09:** Global safety net: `fail_under = 70` added to `.coveragerc`. Catches catastrophic coverage regressions without being the primary enforcement mechanism.

## Pragma: no cover
- **D-10:** Audit all 9 existing `# pragma: no cover` instances across the source tree. Each instance is either justified (with inline comment explaining why code is unreachable) or removed (by writing a test for the uncovered path).
- **D-11:** Future policy: New `# pragma: no cover` annotations must include a justification comment: `# pragma: no cover — reason: <justification>`.

## the agent's Discretion
- Specific assertion strategies per test (hamcrest for allure tests vs vanilla assert everywhere else)
- Coverage gap triage priority within each module (which branches to cover first)
- Mock setup details (follow existing `unittest.mock` patterns from TESTING.md)
- Test file granularity (one file per class vs per module — planner decides)

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

## Scope and Requirements
- `.planning/ROADMAP.md` — Phase 5 goal, success criteria, depends on Phase 4
- `.planning/REQUIREMENTS.md` — TEST-01 requirement definition
- `.planning/PROJECT.md` — Project constraints, core value, active requirements
- `.planning/STATE.md` — Current workflow state, Phase 3/4 blocker context

## Target Source Modules
- `src/pytest_bdd/steps.py` — Step definition manager, registry, matchers (630L, >80% target)
- `src/pytest_bdd/model/run.py` — Run class, session-level runtime state (630L, >85% target)
- `src/pytest_bdd/model/scenario_run.py` — ScenarioRun, step-level runtime state (282L, >85% target)
- `src/pytest_bdd/model/feature_binding.py` — FeatureRuntimeBinding (294L, >85% target)
- `src/pytest_bdd/parsers.py` — Step parser hierarchy (re, parse, cfparse, cucumber_expression, etc.) (603L, frozen — test only)

## Existing Test Patterns
- `.planning/codebase/TESTING.md` — Test framework, mock conventions, file organization, run commands
- `.planning/codebase/CONVENTIONS.md` — Naming, style, error handling, import organization
- `.planning/codebase/STRUCTURE.md` — Module layout, test directory structure, plugin inventory

## Prior Phase Decisions (carried forward)
- `.planning/phases/02-code-quality-gates/02-CONTEXT.md` — `returns` library (`Maybe`/`Result`), explicit exceptions, `attrs` over dataclasses, quality gate enforcement
- `.planning/phases/03-core-runtime-refactor/03-CONTEXT.md` — Direct imports from owning modules, no compatibility re-exports, characterization-tests-first pattern
- `.planning/phases/04-plugin-refactoring/04-CONTEXT.md` — Golden formatter-output checks, source contract tests, class-based plugin verification

## Coverage Configuration
- `.coveragerc` — Branch coverage enabled, includes `pytest_bdd/*` and `tests/*`, add `fail_under = 70`

</canonical_refs>

<code_context>
## Existing Code Insights

## Reusable Assets
- Phase 3 characterization tests in `tests/hook/test_scenario_run_characterization.py`, `tests/hook/test_run_transitions.py`, `tests/hook/test_scenario_run_model.py` — already cover core state transitions for model modules. Extend these, don't duplicate.
- Existing testdir patterns in `tests/feature/test_steps.py`, `tests/feature/test_run_lifecycle.py` — reference for new steps.py coverage.
- `tests/model/test_scenario_run_returns_contract.py` — contract tests validating `Maybe`/`Result` return types from Phase 2 migration.

## Established Patterns
- Direct unit tests use simple `assert` statements with descriptive failure messages. No custom assertion library.
- Mocking follows `unittest.mock` patterns: `patch()` for Go parser availability, `MagicMock` for plugin registrations. Internal components are NOT mocked — prefer integration tests via `testdir`.
- Test functions are type-annotated (`def test_foo() -> None:`) and follow `snake_case` with descriptive names.
- Per-file ruff ignores in `pyproject.toml`: `tests/*` relaxes `ANN`, `D`, `S101`, `PLR0913`.

## Integration Points
- `pyproject.toml` — Add `@pytest.mark.unit` to `[tool.pytest.ini_options].markers`.
- `.coveragerc` — Add `fail_under = 70`.
- Existing test directory tree — migrating tests from `tests/hook/`, `tests/model/`, `tests/steps/` into `tests/unit/` requires updating import paths and potentially module-level fixtures.

</code_context>

<specifics>
## Specific Ideas

- User specifically requested: ALL existing unit tests get `@pytest.mark.unit` and are moved to `tests/unit/` by source module. This is a significant migration — plan should include a task for it.
- Integration/E2E tests stay in `tests/feature/`, `tests/e2e/`, `tests/messages/` — do not reorganize these.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 05-Unit Test Fortification*
*Context gathered: 2026-05-14*
