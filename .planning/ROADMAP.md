# Roadmap: pytest-bdd-ng Stabilization

## Overview

A two-iteration hardening initiative for a mature BDD testing library. **Iteration 1** applies vertical slices — each phase targets a specific subsystem (cleanup, quality, refactor, test, document) before moving to the next. **Iteration 2** performs a horizontal cross-cutting pass over the entire codebase (compat layer, pattern unification, pruning). All structural refactoring is gated behind code quality prerequisites: zero `return None` in non-hook code and specific exception handling throughout.

**Critical constraints:** parsers (`parsers.py`) are frozen during stabilization — tests only, no modifications. `scenario_run.py` split (REF-01) requires characterization tests before any module boundaries change.

## Phases

- [x] **Phase 1: Foundation Cleanup** — Remove dead Allure plugin; remove legacy --cucumberjson CLI flag
- [ ] **Phase 2: Code Quality Gates** — Eliminate 96 return None instances; replace 22 bare except Exception
- [ ] **Phase 3: Core Runtime Refactor** — Split 1422-line scenario_run.py into 3 focused model modules
- [ ] **Phase 4: Plugin Refactoring** — Code generator to class-based pattern; reduce other large files
- [ ] **Phase 5: Unit Test Fortification** — Comprehensive unit test coverage for core modules
- [ ] **Phase 6: Integration Testing** — Edge case coverage for step matching and execution lifecycle
- [ ] **Phase 7: Documentation** — Public API docstrings, developer guide, migration guide
- [ ] **Phase 8: BDD Acceptance Testing** — Expand feature tests for undocumented behaviors
- [ ] **Phase 9: Compatibility Streamlining** — Remove dead shims; consolidate legacy compat layer
- [ ] **Phase 10: Pattern Unification** — Consistent plugin patterns; eliminate cross-plugin imports
- [ ] **Phase 11: Audit & Prune** — Dead code removal; stale module evaluation; final CI validation

## Phase Details

### Phase 1: Foundation Cleanup
**Goal**: Remove user-facing confusion points — dead Allure plugin and legacy `--cucumberjson` CLI flag
**Depends on**: Nothing (first phase)
**Requirements**: STAB-01, STAB-04
**Success Criteria** (what must be TRUE):
  1. Allure logger plugin entry point removed from pyproject.toml — no dead plugin registered at runtime
  2. Users installing `[allure]` extra receive pip error (extra no longer defined — not silent no-op)
  3. Running pytest with `--cucumberjson` produces standard "unrecognized arguments" error (direct removal per user decision D-10)
  4. `--cucumber-json` flag continues to work via cucumber_json_formatter.py
**Plans**: 2 plans
  - [x] 01-01-PLAN.md — Remove dead Allure plugin (entrypoint, source, deps, tests, config)
  - [x] 01-02-PLAN.md — Remove legacy --cucumberjson CLI flag from cucumber_json entrypoint

### Phase 2: Code Quality Gates
**Goal**: Zero `return None` antipatterns in non-hook code; all exception handlers are specific or explicitly logged — gates refactoring for all subsequent phases
**Depends on**: Phase 1
**Requirements**: STAB-02, STAB-03
**Success Criteria** (what must be TRUE):
  1. No `return None` in any non-hook function — explicit sentinels or exceptions used throughout
  2. All 22 bare `except Exception:` handlers replaced with specific exception types or `logger.warning(exc_info=True)`
  3. Scenarios with zero matched step definitions raise collection-time error (not silent green pass)
  4. CI lint gate added: new `return None` or bare `except` in non-hook code triggers CI failure
  5. Full test suite passes with zero regressions — behavior identical, no new failures
**Plans**: TBD

### Phase 3: Core Runtime Refactor
**Goal**: Split the 1422-line `scenario_run.py` god module into `model/run.py`, `model/scenario_run.py`, and `model/feature_binding.py` with zero behavior change
**Depends on**: Phase 2
**Requirements**: REF-01
**Success Criteria** (what must be TRUE):
  1. Three focused modules exist: `model/run.py`, `model/scenario_run.py`, `model/feature_binding.py`
  2. All `RunStage` state transitions produce identical results to pre-split behavior (verified by characterization tests)
  3. Full test suite passes including xdist parallel execution (`-n 2`)
  4. No circular imports between split modules; all imports resolve cleanly
  5. Characterization tests capturing all state transitions pass identically before and after split
**Plans**: TBD

### Phase 4: Plugin Refactoring
**Goal**: All 17 plugins follow canonical class-based pattern; large formatter files reduced to maintainable size
**Depends on**: Phase 3
**Requirements**: REF-02, REF-03
**Success Criteria** (what must be TRUE):
  1. Code generator plugin uses `CodeGeneratorPlugin` class matching canonical plugin standard
  2. `live_formatter_runtime.py` and `message_validation.py` each reduced below 400 lines
  3. All plugins register via consistent `class + entrypoint + hook.py` structure
  4. No plugin directly imports another plugin's internals — all cross-plugin communication via hooks
  5. Full test suite passes; all formatter output identical to pre-refactor
**Plans**: TBD

### Phase 5: Unit Test Fortification
**Goal**: Comprehensive unit test coverage for core runtime, step definition, and parser modules
**Depends on**: Phase 4
**Requirements**: TEST-01
**Success Criteria** (what must be TRUE):
  1. Split model modules (`model/run.py`, `model/scenario_run.py`, `model/feature_binding.py`) have >85% line coverage
  2. `steps.py` has >80% line coverage with step matching edge cases covered
  3. Parser edge cases tested (parsers not modified — tests only, behavior freeze respected)
  4. All `# pragma: no cover` instances in production code are either justified or removed
  5. No test uses pickle-based patterns in production code paths
**Plans**: TBD

### Phase 6: Integration Testing
**Goal**: Contract-level integration tests for step matching priority and scenario execution lifecycle edge cases
**Depends on**: Phase 5
**Requirements**: TEST-03
**Success Criteria** (what must be TRUE):
  1. Step matching priority contract tests pass: specific beats generic, explicit order maintained, no import-order dependency
  2. Scenario execution lifecycle tests cover all `RunStage` transitions end-to-end
  3. Edge cases covered: empty scenarios, malformed Gherkin, unicode, data tables, docstrings
  4. Gherkin keyword edge case tests pass: escaped pipes, table escaping, comments in tables
  5. xdist parallel execution tests pass for all integration scenarios (`-n 2` minimum)
**Plans**: TBD

### Phase 7: Documentation
**Goal**: Complete public API reference, developer guide, and user migration path
**Depends on**: Phase 6
**Requirements**: DOC-01, DOC-02, DOC-03
**Success Criteria** (what must be TRUE):
  1. All public API functions in `src/pytest_bdd/__init__.py` have docstrings with parameter and return descriptions
  2. `DEVELOPMENT.rst` reflects current conventions: `StashBound` pattern, `attrs` usage, testing patterns, plugin class standard
  3. Migration guide documents all breaking differences from pytest-bdd (original): fixture injection, hooks, configuration, CLI flags
  4. `DEPRECATIONS.md` lists all deprecated features with replacement paths and timeline
  5. No undocumented public function remains in `__all__` export list
**Plans**: TBD

### Phase 8: BDD Acceptance Testing
**Goal**: Executable BDD feature tests cover previously undocumented behaviors and edge cases
**Depends on**: Phase 7
**Requirements**: TEST-02
**Success Criteria** (what must be TRUE):
  1. New `.feature.md` files in `features/` directory cover previously undocumented behaviors
  2. All existing BDD feature tests in `features/` pass with zero failures
  3. Step definitions in `tests/e2e/conftest.py` cover all new feature scenarios
  4. BDD test suite runs via `python -m pytest tests/e2e/` with zero failures
  5. Generated documentation from `.feature.md` files (`docs/features/`) is up to date
**Plans**: TBD

### Phase 9: Compatibility Streamlining
**Goal**: Remove dead Python 2 shims and legacy dependencies; consolidate remaining compatibility layer
**Depends on**: Phase 8
**Requirements**: SIM-01
**Success Criteria** (what must be TRUE):
  1. `pathlib2` dependency removed from `pyproject.toml` and all import references
  2. `docopt-ng` dependency removed (replaced with stdlib `argparse` or removed if unused)
  3. All legacy Python 2 compatibility shims and conditional imports removed
  4. Full test suite passes across Python 3.10-3.14 matrix after dependency removal
**Plans**: TBD

### Phase 10: Pattern Unification
**Goal**: Consistent programming patterns across all plugins and core modules — no cross-plugin imports, uniform StashBound usage
**Depends on**: Phase 9
**Requirements**: SIM-02
**Success Criteria** (what must be TRUE):
  1. All plugins follow identical `class + entrypoint + hook.py` structure
  2. No plugin-internal direct imports between plugin modules — all inter-plugin state via hooks
  3. `StashBound` pattern used uniformly for all `pytest.config.stash` access
  4. `attrs` library used consistently across all data classes (no stdlib `dataclass` in new or modified code)
  5. Lint gate passes: ruff rules detect no pattern violations across plugin boundaries
**Plans**: TBD

### Phase 11: Audit & Prune
**Goal**: Zero dead code, unused imports, or stale modules; full CI matrix validation
**Depends on**: Phase 10
**Requirements**: SIM-03
**Success Criteria** (what must be TRUE):
  1. All dead imports removed — ruff F401/F811 pass clean
  2. Underused plugin/utility modules evaluated: kept (with documented justification) or removed
  3. No commented-out code blocks remain (except deprecation-path documentation)
  4. Full CI matrix passes: Python 3.10-3.14 × pytest 8.x-9.x, all platforms
  5. Project size metrics measurably reduced: total lines, import count, module count
**Plans**: TBD

## Progress

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Foundation Cleanup | 2/2 | Planned | - |
| 2. Code Quality Gates | 0/TBD | Not started | - |
| 3. Core Runtime Refactor | 0/TBD | Not started | - |
| 4. Plugin Refactoring | 0/TBD | Not started | - |
| 5. Unit Test Fortification | 0/TBD | Not started | - |
| 6. Integration Testing | 0/TBD | Not started | - |
| 7. Documentation | 0/TBD | Not started | - |
| 8. BDD Acceptance Testing | 0/TBD | Not started | - |
| 9. Compatibility Streamlining | 0/TBD | Not started | - |
| 10. Pattern Unification | 0/TBD | Not started | - |
| 11. Audit & Prune | 0/TBD | Not started | - |
