# Phase 06: Integration Testing — Summary

**Planned:** 2026-05-14
**Status:** Planning complete — awaiting execution

## Plans Created

| Plan ID | Wave | Title | Type | Focus |
|---------|------|-------|------|-------|
| 06-01 | 0 | Step Matching Priority Contract Tests | execute | Strict > unspecified > liberal ordering, import-order independence, parent/child registry |
| 06-02 | 0 | Scenario Execution Lifecycle & Edge Cases | execute | RunStage transitions, hook sequence, empty scenarios, unicode, data tables, docstrings |
| 06-03 | 0 | Run Access, Error Reporting & Failure Paths | execute | require_* failures, step_error/step_func_lookup_error hooks, reporting degradation |
| 06-04 | 1 | Parallel Execution (xdist) Integration | execute | Worker isolation, correct outcomes under `-n 2`, report aggregation |

## Test Files to Create

| File | Tests | Req ID |
|------|-------|--------|
| `tests/feature/test_step_matching_priority.py` | 8 | TEST-03 |
| `tests/feature/test_step_matching_ambiguous.py` | 6 | TEST-03 |
| `tests/feature/test_run_lifecycle_integration.py` | 8 | TEST-03 |
| `tests/feature/test_scenario_execution_edge_cases.py` | 10 | TEST-03 |
| `tests/feature/test_run_access_and_errors.py` | 8 | TEST-03 |
| `tests/feature/test_xdist_parallel_integration.py` | 5 | TEST-03 |

## Total: ~45 new integration tests across 6 files

## Key Dependencies

- Phase 5 (Unit Test Fortification) — complete, `@pytest.mark.unit` marker registered
- Phase 3 (Core Runtime Refactor) — complete, model modules split
- Phase 4 (Plugin Refactoring) — complete, xdist bootstrap blocker fixed

## Constraints

- Parsers frozen — no modifications, tests via public API only
- `scenario_run.py` split characterization tests must remain passing
- No modifications to existing `tests/feature/test_steps.py` (1474 lines, 41 tests)

## Success Gate

All 6 plan files executed, all tests pass:
```bash
uv run python -m pytest tests/feature/test_step_matching_*.py tests/feature/test_run_lifecycle_integration.py tests/feature/test_scenario_execution_edge_cases.py tests/feature/test_run_access_and_errors.py tests/feature/test_xdist_parallel_integration.py -q
```

---

*Auto-generated from plan-phase workflow. Update after each plan completes.*
