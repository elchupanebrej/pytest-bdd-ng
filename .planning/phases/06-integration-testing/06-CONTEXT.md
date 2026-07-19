# Phase 06: Integration Testing - Context

**Gathered:** 2026-05-14
**Status:** Ready for planning

<domain>
## Phase Boundary

End-to-end integration tests for the pytest-bdd execution pipeline. Focus areas:

1. **Step matching priority** — Verify the strict > unspecified > liberal matcher ordering
   works correctly through the real pytest pipeline, not just unit mocks.
2. **Execution lifecycle** — Every `RunStage` transition (`idle → scenario_setup →
   scenario_running → step_running → scenario_running → scenario_teardown → finished`)
   exercised through real hook invocations.
3. **Edge cases** — Empty scenarios, unicode step text, data tables, docstrings,
   Scenario Outlines, Background sections, tag filtering, malformed Gherkin.
4. **Error paths** — `StepDefinitionNotFoundError`, step function exceptions, missing
   feature bindings, missing Gherkin documents, missing pickles.
5. **Parallel execution** — xdist (`-n 2`) worker isolation, reporting aggregation.

Critical constraint from REQUIREMENTS.md (TEST-03): "Add integration tests for edge
cases in step matching priority and scenario execution lifecycle."

Parsers (`parsers.py`) are FROZEN — no modifications, tests only via public API (Phase 5 scope).
`scenario_run.py` split (REF-01) requires characterization tests before module boundary
changes (already satisfied by Phase 3).

## Exclusions

- Unit tests for individual modules → Phase 5 (Unit Test Fortification)
- BDD acceptance/feature expansion → Phase 8 (BDD Acceptance Testing)
- Compatibility streamlining → Phase 9
- Documentation → Phase 7

</domain>

<decisions>
## Test Organization

- **D-01:** Integration tests live in `tests/feature/` following existing testdir pattern.
- **D-02:** New test files prefixed with `test_` for each integration area.
- **D-03:** Existing `tests/feature/test_steps.py` (1474 lines, 41 tests) is NOT modified —
  new tests go in separate files to preserve git blame and avoid merge conflicts.
- **D-04:** xdist tests use testdir's ini configuration support to enable `-n 2`.

## Matcher Priority Verification Method

- **D-05:** Matching priority tested via hook interception (`@pytest_bdd_before_step`) to
  capture which `StepDefinitionManager.Definition` was selected, rather than just checking
  step execution outcome.
- **D-06:** Ambiguity tested by defining two overlapping handlers and checking that the
  first-registered one wins with a `PytestBDDStepDefinitionWarning`.

## Error Path Verification

- **D-07:** Error hook invocations (`step_error`, `step_func_lookup_error`) verified by
  capturing exception details in hook implementations and asserting on them.
- **D-08:** `require_*` failure paths tested through custom hooks that call the internal
  APIs directly (not through step execution).

## the agent's Discretion

- Test file granularity (one file per area vs combined)
- Number of scenarios per feature file
- Whether to use xdist for all tests or only dedicated parallel tests
- Specific step text choices for test scenarios

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

- `.planning/ROADMAP.md` — Phase 6 goal: "Edge case coverage for step matching priority and
  scenario execution lifecycle" - Depends on Phase 5
- `.planning/REQUIREMENTS.md` — TEST-03: "Add integration tests for edge cases in step
  matching priority and scenario execution lifecycle"
- `.planning/STATE.md` — Current workflow state and blockers
- `.planning/phases/03-core-runtime-refactor/03-CONTEXT.md` — Model module split decisions,
  direct import paths
- `.planning/phases/03-core-runtime-refactor/03-PATTERNS.md` — File patterns, code locations
- `.planning/phases/04-plugin-refactoring/04-CONTEXT.md` — Plugin structure, golden baselines
- `.planning/phases/05-unit-test-fortification/05-CONTEXT.md` — Unit test methodology, testdir patterns

## Source Code References

- `src/pytest_bdd/steps.py` — `StepDefinitionManager`, `Matcher`, `find_step_definition_matches`,
  `strict_matcher`, `unspecified_matcher`, `liberal_matcher`
- `src/pytest_bdd/plugin/pickle_runner/run_transitions.py` — `apply_transition()`,
  `PHASE_TO_STAGE`, `_resolve_transition_refs`, `_finalize_after_scenario`
- `src/pytest_bdd/plugin/pickle_runner/plugin.py` — `PickleRunner` orchestration, hook invocation
- `src/pytest_bdd/model/run.py` — `Run`, `RunStage`, `HookPhase`, `LifecycleObjectRef`,
  `ActiveObjectSet`, `StashBound`
- `src/pytest_bdd/model/scenario_run.py` — `ScenarioRun`, `RunNode`, `StepRun`,
  `advance_transition`, `set_active_set`
- `src/pytest_bdd/model/feature_binding.py` — `FeatureRuntimeBinding`, `index_runtime_objects`
- `src/pytest_bdd/plugin/pickle_runner/run_access.py` — `require_*` functions,
  `build_reporting_context_snapshot`, `resolve_scenario_description`,
  `resolve_step_runtime_enrichment`

## Existing Test References

- `tests/feature/test_steps.py` (1474 lines, 41 tests) — existing step integration tests
- `tests/feature/test_run_lifecycle.py` — existing lifecycle tests
- `tests/feature/test_run_hooks.py` — existing hook tests
- `tests/hook/test_run_transitions.py` — unit-level transition tests
- `tests/hook/test_scenario_run_characterization.py` — characterization tests
- `tests/hook/test_scenario_run_model.py` — model unit tests
- `tests/hook/test_scenario_collection_read_hooks.py` — collection hook tests

</canonical_refs>

<code_context>
## Key Architectural Insights

### Step Matching Pipeline

1. `PickleRunner.pytest_bdd_run_step` resolves step object and feature binding
2. `PickleRunner._match_to_step` calls `pytest_bdd_match_step_definition_to_step` hook
3. `StepDefinitionManager.__call__` tries matchers in order: strict → unspecified → liberal
4. `find_step_definition_matches` iterates local registry, recurses to parent if no match
5. First match from highest-priority matcher wins; multiple matches within a matcher → warning

### Execution Lifecycle

1. `pytest_runtest_setup` → `Run.create_scenario_run()` → `apply_transition(HookPhase.before_scenario)`
2. `pytest_runtest_call` → `_invoke_bdd_hook(run_scenario)` → step dispatcher loop:
   - `before_step` → `before_step_call` → step execution → `after_step`
   - On error: `step_error` hook, then `after_scenario`
   - On lookup error: `step_func_lookup_error` hook, then `after_scenario`
3. `pytest_runtest_teardown` → `Run.pop_scenario_run()` → `apply_transition(HookPhase.after_scenario)`

### xdist Model

- Each worker has its own `pytest.config.stash` → separate `Run` instances
- `PickleRunnerPlugin.pytest_sessionstart` initializes Run from stash
- Worker bootstrap handled via `pytest_bdd_worker_bootstrap` module
</code_context>

<specifics>
## Specific Ideas

- 6-8 scenarios per feature file is sufficient for edge case coverage
- Test names should describe the behavior, not the implementation
- Use existing `tests/feature/test_run_lifecycle.py` as a template for test structure
- For xdist tests, prefer testdir-based approach over modifying existing conftest
- Tag filtering test should verify `@pytest.mark.smoke` scenarios are correctly filtered
</specifics>

<deferred>
## Deferred Ideas

- Gherkin dialect extensions — out of scope per architecture decision
- Scenario-to-scenario dependency testing — violates BDD isolation, out of scope
- Performance benchmarking under xdist — not a phase goal
</deferred>

---

*Phase: 06-Integration Testing*
*Context gathered: 2026-05-14*
