# Phase 06: Integration Testing - Research

**Researched:** 2026-05-14
**Domain:** BDD integration testing — step matching, execution lifecycle, error paths, parallel execution
**Confidence:** HIGH

## Summary

This phase adds end-to-end integration tests for the pytest-bdd execution pipeline, focusing on two
areas identified in REQUIREMENTS.md (TEST-03): step matching priority edge cases and scenario
execution lifecycle coverage. The research reveals that while unit-level characterization tests
exist for the runtime model (Phase 3) and unit tests cover individual modules (Phase 5), **zero
integration tests exercise the full BDD pipeline** from Gherkin parsing through step dispatch to
state cleanup. This phase fills that gap.

## Architecture

### Execution Pipeline (testdir-level)

```
Gherkin Feature File
  → Parsed by Gherkin parser (frozen, tested in Phase 5)
  → Pickle compiled (tested in Phase 5 via public API)
  → pytest collects scenario items
  → pytest_runtest_setup:
      Run.from_stash(config.stash)
      Run.create_scenario_run(request, gherkin_document, feature_source, pickle)
        → apply_transition(HookPhase.before_scenario)
  → pytest_runtest_call:
      _invoke_bdd_hook(before_scenario)  [already transitioned above]
      _invoke_bdd_hook(run_scenario):
        → step_dispatcher loop:
            _invoke_bdd_hook(run_step) → match → before_step → before_step_call → execute → after_step
            or: step_error / step_func_lookup_error on failure
      _invoke_bdd_hook(after_scenario)
        → apply_transition(HookPhase.after_scenario) → _finalize_after_scenario
  → pytest_runtest_teardown:
      Run.pop_scenario_run(request)
```

### Step Matching Resolution Chain

```
Matcher.__call__(request, feature, pickle, step, previous_step, step_registry)
  → find_step_definition_matches(registry, [strict, unspecified, liberal])
    → For each matcher type:
      → For each step_definition in registry:
        → If matcher(definition): yield definition
      → If found: break (first matcher type wins)
    → If exhausted, recurse to registry.parent
  → If no match: raise MatchNotFoundError
```

**Priority order (tested by this phase):**
1. `strict_matcher` — `type_ == step_type_context AND parser.is_matching()`
2. `unspecified_matcher` — either side has `PickleStepType.unknown AND parser.is_matching()`
3. `liberal_matcher` — `liberal=True AND types differ AND NOT unspecified AND parser.is_matching()`

### RunStage Transition Map

| HookPhase | RunStage | Tested By |
|-----------|----------|-----------|
| `before_scenario` | `scenario_setup` | 06-02 |
| `run_scenario` | `scenario_running` | 06-02 |
| `before_step` | `step_running` | 06-02 |
| `before_step_call` | `step_running` | 06-02 |
| `run_step` | `step_running` | 06-02 |
| `after_step` | `scenario_running` | 06-02 |
| `step_error` | `scenario_running` | 06-02, 06-03 |
| `step_lookup_error` | `scenario_running` | 06-02, 06-03 |
| `after_scenario` | `scenario_teardown` | 06-02 |

## Key Risks and Gaps

### Risk 1: Step matching is non-deterministic across implementations
Python `set` iteration order is non-deterministic but CPython 3.7+ preserves insertion order.
The `find_step_definition_matches` function yields from the first matcher that produces results,
then breaks. **Within a single matcher, all matching definitions are yielded** — but the caller
(`Matcher.__call__`) takes the first via `next()` on the generator. This means:
- First-registered wins within a matcher tier (verified via insertion-ordered set)
- Cross-tier priority is deterministic (strict > unspecified > liberal)
- **Integration test must verify both ordering dimensions**

### Risk 2: xdist worker isolation
Each xdist worker has its own `pytest.config.stash`, so `Run.from_stash()` returns
worker-local instances. However, if any module-level state exists (e.g., cached imports,
class variables), cross-contamination is possible. **Test must verify isolation.**

### Risk 3: Error path coverage
The `step_error` and `step_func_lookup_error` hooks are critical user-facing extensibility
points. Phase 4 confirmed these hooks fire correctly at the unit level, but no integration
test verifies the full pipeline from step exception → hook invocation → scenario continuation.

### Risk 4: Gherkin edge cases
Unusual but valid Gherkin constructs (unicode, multiline docstrings, data tables with special
characters, comments between steps) may not be exercised by existing tests.

## Test Strategy

| Area | Approach | Test Location | Count |
|------|----------|---------------|-------|
| Matching priority | testdir with overlapping definitions | `tests/feature/test_step_matching_priority.py` | 8 |
| Ambiguity handling | testdir with duplicate definitions | `tests/feature/test_step_matching_ambiguous.py` | 6 |
| Lifecycle transitions | testdir with hook recording | `tests/feature/test_run_lifecycle_integration.py` | 8 |
| Edge cases | testdir with crafted features | `tests/feature/test_scenario_execution_edge_cases.py` | 10 |
| Error paths | testdir with error-triggering features | `tests/feature/test_run_access_and_errors.py` | 8 |
| xdist parallel | testdir with `-n 2` ini | `tests/feature/test_xdist_parallel_integration.py` | 5 |

## Source Code Verified

| File | Key Elements Verified | Method |
|------|----------------------|--------|
| `src/pytest_bdd/steps.py` | `Matcher.__call__`, `strict_matcher`, `unspecified_matcher`, `liberal_matcher`, `find_step_definition_matches` | Full read (lines 286-443) |
| `src/pytest_bdd/plugin/pickle_runner/run_transitions.py` | `apply_transition`, `PHASE_TO_STAGE`, `_resolve_transition_refs`, `_finalize_after_scenario` | Full read (312 lines) |
| `src/pytest_bdd/plugin/pickle_runner/plugin.py` | `PickleRunner` lifecycle, `_invoke_bdd_hook`, `_match_to_step` | Read lines 124-312 |
| `src/pytest_bdd/plugin/pickle_runner/run_access.py` | `require_*` functions, `build_reporting_context_snapshot` | Read lines 1-368 |
| `src/pytest_bdd/model/run.py` | `Run`, `RunStage`, `HookPhase`, `LifecycleObjectRef`, `ActiveObjectSet` | Read (783 lines) |
| `src/pytest_bdd/model/scenario_run.py` | `ScenarioRun`, `RunNode`, `StepRun`, `advance_transition` | Read (332 lines) |
| `src/pytest_bdd/model/feature_binding.py` | `FeatureRuntimeBinding`, `index_runtime_objects` | Read (374 lines) |

## Existing Test Patterns (Verified)

| Pattern | Example File | Technique |
|---------|-------------|-----------|
| testdir integration | `tests/feature/test_steps.py` | `testdir.makeconftest()`, `testdir.makefile()`, `testdir.runpytest()` |
| Hook interception | `tests/feature/test_run_hooks.py` | Custom hook implementations in conftest |
| xdist test | `tests/contract/test_xdist_worker_controller_boundary_contract.py` | `testdir.runpytest("-n 2")` |
| Feature with conftest | `tests/feature/test_outline.py` | Separate .feature + conftest + test runner |

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest >=7.0.0 |
| Config file | `pyproject.toml` `[tool.pytest.ini_options]` |
| Quick run command | `uv run python -m pytest tests/feature/test_step_matching_priority.py -q` |
| Full phase run | `uv run python -m pytest tests/feature/test_step_matching_priority.py tests/feature/test_step_matching_ambiguous.py tests/feature/test_run_lifecycle_integration.py tests/feature/test_scenario_execution_edge_cases.py tests/feature/test_run_access_and_errors.py tests/feature/test_xdist_parallel_integration.py -q` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test File | Automated Command | Status |
|--------|----------|-----------|-------------------|--------|
| TEST-03 (priority) | Strict > unspecified > liberal matching | `test_step_matching_priority.py` | `pytest tests/feature/test_step_matching_priority.py -q` | ❌ |
| TEST-03 (priority) | Import-order independence | `test_step_matching_priority.py` | `pytest tests/feature/test_step_matching_priority.py -q` | ❌ |
| TEST-03 (lifecycle) | All RunStage transitions | `test_run_lifecycle_integration.py` | `pytest tests/feature/test_run_lifecycle_integration.py -q` | ❌ |
| TEST-03 (lifecycle) | Edge cases (empty, unicode, tables) | `test_scenario_execution_edge_cases.py` | `pytest tests/feature/test_scenario_execution_edge_cases.py -q` | ❌ |
| TEST-03 (errors) | Error hook pipelines | `test_run_access_and_errors.py` | `pytest tests/feature/test_run_access_and_errors.py -q` | ❌ |
| TEST-03 (xdist) | Parallel execution | `test_xdist_parallel_integration.py` | `pytest tests/feature/test_xdist_parallel_integration.py -q` | ❌ |

### Success Criteria

- All integration tests pass via `testdir` (no `testdir` failures)
- Step matching priority verified end-to-end (not just unit)
- xdist `-n 2` passes for all integration test files
- No regressions in existing `tests/feature/` suite

---

**Research date:** 2026-05-14
**Valid until:** 2026-06-14

## Open Questions

1. **Should xdist tests be in a separate directory?** Decision: Keep in `tests/feature/` alongside other integration tests for simpler collection, but mark with a custom marker for selective running.

2. **Data table and docstring parsing — need to verify through StepRun or just via step argument values?** Decision: Test via step argument values (what the step function receives) rather than StepRun internals — this is the user-facing behavior.

3. **Should we test the `liberal_steps` ini option?** Decision: Yes — create a minimal feature + conftest and test with `addopts = -a liberal_steps` to verify the ini option path.
