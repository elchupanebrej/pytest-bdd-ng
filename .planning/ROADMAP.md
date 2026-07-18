# Roadmap: pytest-bdd-ng Stabilization

## Overview

A two-iteration hardening initiative for a mature BDD testing library. **Iteration 1** applies vertical slices — each phase targets a specific subsystem (cleanup, quality, refactor, test, document) before moving to the next. **Iteration 2** performs a horizontal cross-cutting pass over the entire codebase (compat layer, pattern unification, pruning). All structural refactoring is gated behind code quality prerequisites: zero `return None` in non-hook code and specific exception handling throughout.

**Critical constraints:** parsers (`parsers.py`) are frozen during stabilization — tests only, no modifications. `scenario_run.py` split (REF-01) requires characterization tests before any module boundaries change.

## Phases

- [x] **Phase 1: Foundation Cleanup** — Remove dead Allure plugin; remove legacy --cucumberjson CLI flag
- [x] **Phase 2: Code Quality Gates** — Eliminate 96 return None instances; replace 22 bare except Exception
- [x] **Phase 3: Core Runtime Refactor** — Split 1422-line scenario_run.py into 3 focused model modules (completed 2026-07-07)
- [x] **Phase 4: Plugin Refactoring** — Code generator to class-based pattern; reduce other large files
- [ ] **Phase 5: Unit Test Fortification** — Comprehensive unit test coverage for core modules
- [ ] **Phase 6: Integration Testing** — Edge case coverage for step matching and execution lifecycle
- [x] **Phase 7: Documentation** — Public API docstrings, developer guide, migration guide
- [ ] **Phase 8: BDD Acceptance Testing** — Expand feature tests for undocumented behaviors
- [ ] **Phase 9: Compatibility Streamlining** — Remove dead shims; consolidate legacy compat layer
- [x] **Phase 10: Pattern Unification** — Consistent plugin patterns; eliminate cross-plugin imports (completed 2026-05-16)
- [x] **Phase 11: Audit & Prune** — Dead code removal; stale module evaluation; final CI validation
- [x] **Phase 12: Restructure test suite into semantic groups** — Semantic test tree migration, Makefile API, testing/ package
- [x] **Phase 13: Unify cucumber-json plugins INI/CLI options** — Consolidate INI and CLI cucumber-json reporters
- [x] **Phase 14: Gap Closure** — Achieve 70% unit test coverage; resolve BDD feature test failures
- [x] **Phase 15: Cross-platform test suite entrypoint (Makefile + MinGW sh)** — Cross-platform test suite entrypoint via Makefile and MinGW shell (reopened for gap closure 2026-05-23) (completed 2026-05-23)
- [x] **Phase 16: Move vulture dead-code gate from pytest to native pre-commit hook** — Native vulture pre-commit hook with native whitelist (completed 2026-05-25)

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

**Plans**: 4 plans
Plans:

- [x] 02-01-PLAN.md — Foundation: returns library + StrEnum types + CI lint rule
- [x] 02-02-PLAN.md — Core model migration: scenario_run.py, stash_access.py, feature_locator.py, etc.
- [x] 02-03-PLAN.md — Plugin + utility migration: collectors, plugins, scripts, remaining model files
- [x] 02-04-PLAN.md — Exception fixes + parsers Result conversion + zero-matches UX

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

**Plans**: 3 plans
Plans:

- [x] 03-01-PLAN.md — Characterization safety net and import/source contracts
- [x] 03-02-PLAN.md — Extract runtime modules and migrate direct imports
- [x] 03-03-PLAN.md — Final verification, xdist smoke, and execution summary

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

**Plans**: 6 plans
Plans:

- [x] 04-01-PLAN.md — Verification environment unblocker
- [x] 04-02-PLAN.md — Source contracts and formatter golden baselines
- [x] 04-03-PLAN.md — Code generator class-based plugin refactor
- [x] 04-04-PLAN.md — Plugin package normalization and boundary contracts
- [x] 04-05-PLAN.md — Live formatter runtime responsibility split
- [x] 04-06-PLAN.md — Message validation split and final verification

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

**Plans**: 4 plans

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

**Plans**: 6 plans

  - [x] 06-01-PLAN.md — Step matching priority contract tests
  - [x] 06-02-PLAN.md — Scenario execution lifecycle & edge cases
  - [x] 06-03-PLAN.md — Run access, error reporting & failure paths
  - [x] 06-04-PLAN.md — Parallel execution (xdist) integration

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

**Plans**: 4 plans
Plans:

- [x] 07-01-PLAN.md — Sphinx setup + docstring verification test scaffolds
- [x] 07-02-PLAN.md — Comprehensive Google-style docstrings for all 8 public API exports
- [x] 07-03-PLAN.md — Comprehensive DEVELOPMENT.rst rewrite with architecture, patterns, testing
- [x] 07-04-PLAN.md — Migration guide + DEPRECATIONS.md + docs toctree wiring

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

**Plans**: 8 plans
Plans:

- [x] 08-01-PLAN.md — Audit 47 existing feature files + propose gap list (D-02, D-11)
- [x] 08-02-PLAN.md — Create step definition stubs for 8a core topics (Go parser, tags, heading, mimetype, struct_bdd)
- [x] 08-03-PLAN.md — Create .feature.md files for 8a core topics
- [x] 08-04-PLAN.md — Create step definition stubs for 8b formatters (junit, progress, snippets, summary, usage)
- [x] 08-05-PLAN.md — Create .feature.md files for 8b formatters
- [x] 08-06-PLAN.md — Create step definition stubs for 8c plugins (code_generator, scenario_reporter, compatibility, batch)
- [x] 08-07-PLAN.md — Create .feature.md files for 8c plugins
- [x] 08-08-PLAN.md — Full test suite run, ensure zero failures (D-15)

### Phase 9: Compatibility Streamlining

**Goal**: Remove dead Python 2 shims and legacy dependencies; consolidate remaining compatibility layer
**Depends on**: Phase 8
**Requirements**: SIM-01
**Success Criteria** (what must be TRUE):

  1. `pathlib2` dependency removed from `pyproject.toml` and all import references
  2. `docopt-ng` dependency removed (replaced with stdlib `argparse` or removed if unused)
  3. All legacy Python 2 compatibility shims and conditional imports removed
  4. Full test suite passes across Python 3.10-3.14 matrix after dependency removal

**Plans**: 2 plans
Plans:

- [x] 09-01-PLAN.md — Remove pathlib2/docopt-ng deps, delete git.py/jsonschema.py, update consumers
- [x] 09-02-PLAN.md — Split matrix.py into runtime_compat.py + util/matrix.py, update all imports

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

**Plans**: 5 plans
Plans:

- [x] 11-01-PLAN.md — Remove confirmed dead code (feature_locator.py, util/temp_root.py, validate_requested_pair)
- [x] 11-02-PLAN.md — Split steps.py (971L) into steps/ package: Registry, Matcher, Definition, decorators
- [x] 11-03-PLAN.md — Split message_capability_governance.py (853L) into schema/capabilities/decisions/cli
- [x] 11-04-PLAN.md — Split run.py (783L) into model/run/ package: stages, lifecycle, refs
- [x] 11-05-PLAN.md — Plugin audit docs (17 plugins), decopatch health, CI matrix validation

## Progress

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Foundation Cleanup | 2/2 | Complete    | 2026-05-12 |
| 2. Code Quality Gates | 4/4 | Complete    | 2026-05-12 |
| 3. Core Runtime Refactor | 3/3 | Complete    | 2026-05-13 |
| 4. Plugin Refactoring | 6/6 | Complete | 2026-05-14 |
| 5. Unit Test Fortification | 4/4 | Complete | 2026-05-14 |
| 6. Integration Testing | 4/4 | Complete | 2026-05-14 |
| 7. Documentation | 4/4 | Complete | 2026-05-15 |
| 8. BDD Acceptance Testing | 8/8 | Complete | 2026-05-15 |
| 9. Compatibility Streamlining | 2/2 | Complete | 2026-05-16 |
| 10. Pattern Unification | 1/1 | Complete | 2026-05-16 |
| 11. Audit & Prune | 5/5 | Complete | 2026-05-17 |
| 12. Restructure test suite | 6/6 | Complete | 2026-05-20 |
| 13. Unify cucumber-json plugins | 3/3 | Complete | 2026-05-20 |
| 14. Gap Closure | 4/4 | Complete | 2026-05-21 |
| 15. Cross-platform test suite entrypoint | 3/3 | Complete   | 2026-05-23 |
| 16. Vulture pre-commit hook | 1/1 | Complete | 2026-05-25 |
| 17. Adapt GitHub CI to use make and validate with act | 2/2 | Complete    | 2026-05-28 |
| 20. docs/architecture/allure.md | 7/7 | Complete | 2026-06-11 |
| 29. CCK Closure | 1/1 | Complete | 2026-07-02 |
| 30. Add a new phase from todo | 2/2 | Complete | 2026-07-02 |
| 31. Add __tracebackhide__ = True module-level to all src/pytest_bdd/ modules | 3/3 | Complete    | 2026-07-09 |

### Phase 12: Restructure test suite into semantic groups

**Goal:** Restructure the test suite so `tests/cases/` communicates semantic purpose, `tests/assets/` holds passive data only, shared active harness code lives under internal `src/pytest_bdd/testing/`, and Makefile targets are the documented human API for local, full, semantic, slow, and environment-specific runs.
**Requirements**: P12-01, P12-02, P12-03, P12-04, P12-05, P12-06, P12-07, P12-08, P12-09, P12-10
**Depends on:** Phase 11
**Plans:** 3/3 plans complete

Plans:
**Wave 1**

- [x] 12-01-PLAN.md — Wave 0 guard tests for semantic classification, Makefile API, and E2E loader shape
- [x] 12-02-PLAN.md — Move active shared helpers to `src/pytest_bdd/testing/` and passive fixtures to `tests/assets/`

**Wave 2** *(blocked on Wave 1 completion)*

- [x] 12-03-PLAN.md — Big-bang semantic test tree migration and per-file E2E loader split

**Wave 3** *(blocked on Wave 2 completion)*

- [x] 12-04-PLAN.md — Rewrite pytest config, Makefile API, tox paths, and path-coupled scripts

**Wave 4** *(blocked on Wave 3 completion)*

- [x] 12-05-PLAN.md — Update development docs and handle generated feature-doc drift

**Wave 5** *(blocked on Wave 4 completion)*

  - [x] 12-06-PLAN.md — Run final guard, semantic slice, tox, full feasible suite, and stale path validation

### Phase 13: Unify cucumber-json plugins INI/CLI options

**Goal:** Unify the two existing cucumber-json reporter plugins (INI-configured and CLI-configured) into a single consolidated plugin with both configuration paths
**Depends on:** Phase 12
**Plans:** 3/3 plans complete

**Success Criteria** (what must be TRUE):

  1. A third entry point (`cucumber_json_dispatcher`) bridges INI and CLI cucumber-json configuration paths
  2. No duplicate registration or conflicting output between the two paths
  3. Backward compatible: existing INI configs and CLI invocations produce identical output
  4. Full test suite passes with zero regressions

Plans:

- [x] 13-01-PLAN.md — TBD

### Phase 14: Gap Closure

**Goal:** Close v1.0 milestone audit gaps: achieve 70% unit test coverage (from 56%) and resolve 27 remaining BDD feature test failures (TEST-02)
**Requirements**: TEST-01, TEST-02
**Depends on:** Phase 13
**Plans:** 4/4 plans complete

**Success Criteria** (what must be TRUE):

  1. Unit test coverage reaches >=70% line+branch coverage on non-exempt modules (from current 56%)
  2. All 27 BDD feature test failures in `features/` are resolved (excluding infrastructure-dependent tests)
  3. BDD test suite passes via `python -m pytest tests/cases/e2e/e2e/` with zero failures
  4. E2E test modules are split per feature file (D-10), no whole-directory loaders
  5. No regressions introduced to existing passing tests
  6. All `# pragma: no cover` instances are justified or removed

Plans:
**Wave 1**

- [x] 14-01-PLAN.md — Analysis sweep: coverage gap scan + BDD failure triage

**Wave 2** *(blocked on Wave 1)*

- [x] 14-02-PLAN.md — Unit test coverage augmentation + markers + pragma audit
- [x] 14-03-PLAN.md — BDD failure resolution + E2E per-file module split + new feature docs

**Wave 3** *(blocked on Wave 2)*

- [x] 14-04-PLAN.md — Final verification: full suite + coverage threshold + phase summary

### Phase 15: Cross-platform test suite entrypoint (Makefile + MinGW sh)

**Goal:** Add a Makefile-based test entrypoint that works across platforms including MinGW shell
**Depends on:** Phase 14
**Requirements:** TBD
**Plans:** 3/3 plans complete

**Success Criteria** (what must be TRUE):

  1. OS detection at top of Makefile uses `uname -s` to detect Windows, macOS, Linux
  2. Unsupported shell guard exits early with actionable error when invoked from cmd.exe/PowerShell
  3. Windows SHELL set to Git Bash `sh.exe` (short DOS path) and Docker bin added to PATH
  4. `test-docker` split into `test-docker-linux` and `test-docker-windows` with per-platform routing in `test-all`
  5. `test-all` routes native, Docker, and platform-specific targets per OS (D-10 satisfied)
  6. Shell syntax in `test-windows` and `test-posix` fixed for cross-platform compatibility
  7. DEVELOPMENT.rst has "Cross-Platform Setup" section with prerequisite table
  8. All existing Makefile targets continue to work; no regressions in test suite

Plans:
**Wave 1**

- [x] 15-01-PLAN.md — Makefile cross-platform guards, OS detection, Docker split, platform routing

**Wave 2** *(blocked on Wave 1 completion)*

- [x] 15-02-PLAN.md — DEVELOPMENT.rst cross-platform documentation + final verification

**Wave 3** *(gap closure; blocked on Wave 2 completion)*

- [x] 15-03-PLAN.md — Tox-backed cross-platform pipeline gap closure

### Phase 16: Move vulture dead-code gate from pytest to native pre-commit hook

**Goal:** Move vulture dead-code checking out of pytest and into the native pre-commit workflow.
**Requirements**: SIM-03
**Depends on:** Phase 15
**Plans:** 1/1 plans complete

**Success Criteria** (what must be TRUE):

  1. Vulture runs as a native pre-commit hook.
  2. False positives live in native `vulture_whitelist.py`.
  3. The pytest wrapper vulture test is removed.
  4. Direct project test/tox dependencies on vulture are removed.
  5. Targeted pre-commit hooks and unit suite pass.

Plans:

- [x] 16-01-PLAN.md — Move vulture gate to native pre-commit config and whitelist

### Phase 17: Adapt GitHub CI to use make and validate with act

**Goal**: Adapt the main GitHub Actions workflow to reuse Makefile targets for project-specific commands, while keeping GitHub Actions responsible for runner/toolchain setup.
**Requirements**: TBD
**Depends on**: Phase 16
**Plans**: 2 plans

Plans:

- [x] 17-01-PLAN.md — Create Makefile CI command API
- [x] 17-02-PLAN.md — Migrate GitHub CI project-command steps to Makefile targets

### Phase 18: Split xdist-remote tests into separate parallel GHA executor job

**Goal:** [To be planned]
**Requirements**: TBD
**Depends on:** Phase 17
**Plans:** 1/1 plans complete

Plans:

- [x] TBD (run /gsd-plan-phase 18 to break down) (completed 2026-06-02)

### Phase 19: HTML doc generation simplification

**Goal:** [To be planned]
**Requirements**: TBD
**Depends on:** Phase 18
**Plans:** 4/4 plans complete

Plans:

- [x] TBD (run /gsd-plan-phase 19 to break down) (completed 2026-06-04)

**Cross-cutting constraints:**

- D-02: Do not keep the old generated RST pipeline as a fallback.

### Phase 20: multiple refactorings

**Goal:** Elevate pytest-bdd-ng from 4-star to 5-star quality across three dimensions: type safety (mypy `--strict` compliance with zero errors), architecture (no file exceeds 400 LOC, plugins core/extra split, Go parser optional, explicit layered architecture), and documentation (object map with scores, responsibility contracts for every Python entity, API reference, 10 ADRs, 5 how-to guides).
**Requirements**: T0, T1, T2, T3, A1, A2, A3, A4, A5, D0, D1, D2, D3, D4, INIT-01, R1, R2, R3, R4, R5, R6, R7, R8, R9, R10
**Depends on:** Phase 19
**Plans:** 32/32 plans complete

**Success Criteria** (what must be TRUE):

 1. `mypy --strict src/` exits 0 with all 13 strict flags enabled and zero errors
2. 17 local stub packages ship in wheel at `stubs/`; zero `ignore_missing_imports` in pyproject.toml
3. Custom ruff rule (BLQ11xx) enforces type:ignore discipline with error codes + explanations
4. No file in `src/` exceeds 400 LOC; 5 named files split into packages with facade.py backward compat
5. 18 plugins audited, categorized into 3 core + 15 extra in 4 thematic groups; zero core-to-plugin compile-time deps
6. Go parser available via `pip install pytest-bdd[go-parser]`; `pip install pytest-bdd` is Go-free
7. 8-layer architectural model defined in `docs/architecture/layers.toml` with enforcement rule (BLQ13xx)
8. `docs/architecture/OBJECT_MAP.md` with architectural scores (wave 1 average ≥ 4.0)
9. Auto-generated API reference via Sphinx autodoc at `docs/api/`; `make docs` builds without warnings
10. 10 ADR files at `docs/adr/`; 5 how-to guides at `docs/guides/`
11. Full test suite passes at every intermediate step; CI matrix green at phase completion
 12. All requirement IDs addressed; all custom ruff rules (including init_rules.py BLQ14xx) run in pre-commit
 13. All 48 __init__.py files have classification comments; init_rules.py exits 0; ruff rules are logically organized in pyproject.toml
14. Every Python entity under `src/pytest_bdd/` has a filled responsibility contract in its docstring; injector, object map, gap analyzer, Pylint gate, and Sphinx build pass

Plans:

### Architecture (Waves 1-5)

- [x] 20-01-PLAN.md — A4: Layer definition (layers.toml, LAYERS.md, layer_rules.py) + D2 ADRs 001-003 (Wave 1)
- [x] 20-02-PLAN.md — A3: Go parser extraction to optional extra + D2 ADR 005 (Wave 2)
- [x] 20-03-PLAN.md — A2: Plugin audit + core/extra split + D2 ADRs 004, 007 (Wave 3)
- [x] 20-04-PLAN.md — A1: File splits (parsers, scenario_locator, message_stream_validation) + file_size_rules.py + D2 ADRs 006, 008 (Wave 4)
- [x] 20-05-PLAN.md — A1: File splits (cucumber_formatters, tests_group_ordering, 4 remaining) + D2 ADRs 009, 010 (Wave 5)

### Typing (Waves 6-9)

- [x] 20-06-PLAN.md — T0: Type checker comparison report (pyright, ty, pytype vs mypy) (Wave 6)
- [x] 20-07-PLAN.md — T1: Stub creation (17 local stubs at stubs/) + eliminate ignore_missing_imports (Wave 7)
- [x] 20-08-PLAN.md — T2: Enable all mypy --strict flags incrementally; fix ~250-300 errors (Wave 8)
- [x] 20-09-PLAN.md — T3: Custom ruff rule (typing_rules.py) for type:ignore enforcement (Wave 9)

### Documentation (Wave 10)

- [x] 20-10-PLAN.md — D0: Object map wave 1 (public API scores ≥ 4.0) + collect_arch_scores.py (Wave 10)
- [x] 20-11-PLAN.md — D1: Auto-generated API reference via Sphinx autodoc (Wave 10)
- [x] 20-12-PLAN.md — D3: 5 how-to guides at docs/guides/ (Wave 10)

### Gap Closure (Waves 11-13)

- [~] 20-13-PLAN.md — T2: Fix mypy errors — Tasks 1-2 done (800→484 errors), Task 3 remaining (Wave 11)
- [~] 20-14-PLAN.md — A1: Split oversized files — Task 1 done (1 of 7 split), 6 remaining (Wave 12)

### Package Hygiene (Wave 13)

- [~] 20-15-PLAN.md — INIT-01: Tasks 1+5 done (init_rules.py + layout_rules.py created), Tasks 2-4 remaining (Wave 13)

### Gap Closure Phase 2 (Waves 14-15)

- [x] 20-16-PLAN.md — T2: Fix unused-ignore (64) + untyped-decorator (58) mypy errors (Wave 14)
- [x] 20-17-PLAN.md — T2: Fix attr-defined (203) via stub enhancements for pluggy, cucumber_messages, gherkin (Wave 14)
- [x] 20-18-PLAN.md — T2: Fix remaining mypy errors (call-arg, type-arg, arg-type, etc.) + final verify + remove xfail (Wave 15, depends on 20-16, 20-17)
- [x] 20-19-PLAN.md — A1: Split step_catalog_runtime.py, cli.py, struct_bdd/model.py — quick/medium files (Wave 14)
- [x] 20-20-PLAN.md — A1: Split lifecycle.py, lifecycle_runtime.py, pickle_runner/plugin.py — hard files (Wave 14)
- [x] 20-21-PLAN.md — INIT-01: Audit __init__.py files, reorg ruff rules, merge .ruff/, fix layout_rules.py (Wave 14)
- [x] 20-22-PLAN.md — A1: Remove xfail from test_file_size_compliance.py — A1 requirement closure (Wave 15, depends on 20-19, 20-20)

### Gap Closure Phase 3 — Test Package & __init__.py Cleanup (Waves 16-17)

**Requirements**: R1, R2, R3, R4, R5, R6, R7, R8, R9, R10
**Goal:** Extract tests to independent `pytest_bdd_toolchain` package, fix Docker compose paths, eliminate `__all__` and empty `__init__.py`, update init_rules.py enforcement

**Success Criteria** (what must be TRUE):

  1. Tests live at `src/pytest_bdd_toolchain/` — a completely separate package at `./src` level
  2. `testing = ["pytest_bdd_toolchain"]` in `[project.optional-dependencies]`
  3. `tests/` directory at repo root fully removed
  4. All Docker paths resolve from repo root; docker-compose context = 5 levels (correct)
  5. Zero empty `__init__.py` files — all deleted per PEP 420
  6. Zero `__all__` in `__init__.py` — replaced with clean imports and mypy overrides (no `as Y` aliases)
  7. No backward-compat re-exports or transitional facade.py patterns
  8. init_rules.py BLQ1401/1402/1403/1404 and test_import_rules.py BLQ1601 enforce new conventions
  9. Full test suite passes from new layout; mypy strict passes; all custom lint rules pass

**Plans:** 4 plans

Plans:
**Wave 1** *(R1-R4: test package extraction + Docker rework)*

- [x] 20-26-PLAN.md — R1+R2: Move testing/ → pytest_bdd_toolchain/, rewrite imports, update pyproject.toml + Makefile (Wave 1)
- [x] 20-27-PLAN.md — R3+R4: Delete tests/, fix Docker compose+Dockerfiles+entrypoints+Makefile (Wave 2, depends on 20-26)

**Wave 2** *(R5-R9: __init__.py elimination + namespace + rules)*

- [x] 20-28-PLAN.md — R5+R6+R7+R8: Replace __all__ with as-imports, delete empty __init__.py files, remove backward-compat shims, add INP001 suppressions (Wave 3, depends on 20-27)
- [x] 20-29-PLAN.md — R9: Update init_rules.py BLQ1401/1402/1403, create unit tests, final verification (Wave 3, depends on 20-27)
- [x] 20-30-PLAN.md — A5: Port custom static rules into unified Pylint checker plugin (Wave 3, depends on 20-29)
- [x] 20-31-PLAN.md — A5: Enable Pylint cyclic-import and duplicate-code checks and fix violations (Wave 4, depends on 20-30)
- [x] 20-32-PLAN.md — D4: Full responsibility documentation for every `src/pytest_bdd/` Python entity (Wave 18, depends on 20-30 and 20-31)

### Phase 26: Test CLI scripts in a separate Cucumber Development flow

**Goal:** Add executable BDD coverage for repository development scripts, command-line tools, and pre-commit quality gates in a focused `features/18 Development/` flow.
**Requirements**: P26-DEV-01, P26-DEV-02, P26-DEV-03, P26-DEV-04, P26-DEV-05, P26-DEV-06, P26-DEV-07, P26-DEV-08, P26-DEV-09, P26-DEV-10, P26-DEV-11
**Depends on:** Phase 25
**Plans:** 2/2 plans complete

**Success Criteria** (what must be TRUE):

  1. `features/18 Development/` contains BDD feature coverage for Allure conversion, heading validation, architecture tooling, compatibility matrix, messages schema sync, Cucumber formatter rendering, and messages coverage audit orchestration.
  2. Shared development steps support isolated mock file creation, command execution in the test directory, exit-code assertions, and stdout/stderr assertions.
  3. E2E registration imports the development steps and exposes `src/pytest_bdd_toolchain/case/e2e/feature/test_18_development.py` as the loader for the Development feature space.
  4. The known Messages Coverage Audit probe issue is documented as a blocker/risk until resolved or explicitly scoped.
  5. Focused verification target `pytest src/pytest_bdd_toolchain/case/e2e/feature/test_18_development.py` is the primary phase test.

Plans:
**Wave 1**

- [x] 26-01-PLAN.md - Development script ATDD/BDD coverage

**Wave 2** *(blocked on Wave 1 completion)*

- [x] 26-02-PLAN.md - Close Development CLI literal coverage gaps

### Phase 27: Replace Make&sh with Act

**Goal:** Replace Make and shell development entrypoints with local GitHub Actions workflow targets and Python command
surfaces while preserving GitHub-hosted CI/release workflows.
**Depends on:** Phase 26
**Plans:** 2/2 plans complete

**Success Criteria** (what must be TRUE):

  1. Local development targets are runnable through explicit workflow jobs and produce durable artifacts under neutral
     local artifact paths.

  2. GitHub-hosted CI workflows remain present and clearly documented as CI-owned, not local target replacements.
  3. Every workflow file explains whether it is CI-owned or local/manual artifact-producing infrastructure.
  4. Every file under `scripts/` is accounted for by BDD/ATDD coverage, facade coverage, or explicit private-helper
     classification behind a covered facade.

  5. Feature files in `features/18 Development` describe the capability, reason to exist, and framework pain covered;
     they do not present the local runner as the feature target.

  6. Touched contract tests follow project test style: PyHamcrest assertions and module-level test functions.

Plans:

**Wave 1**

- [x] 27-01-PLAN.md - Replace Make and shell scripts with local workflow/Python command surface

**Wave 2** *(blocked on Wave 1 findings review)*

- [x] 27-02-PLAN.md - Close workflow boundary, artifact naming, direct JSON, scripts coverage, and test-style findings

### Phase 28: Extract pytest_bdd_toolchain

**Goal:** Extract `pytest_bdd_toolchain` into `pytest_bdd_toolchain` — a standalone package with all 11 development
scripts as `pbt-*` entrypoints, updated documentation, and zero regressions.
**Depends on:** Phase 27
**Plans:** 1/1 plans complete

**Success Criteria** (what must be TRUE):

1. `python -c "import pytest_bdd_toolchain"` succeeds
2. `python -c "import pytest_bdd_toolchain"` fails with ImportError
3. All 11 `pbt-*` commands execute without import errors
4. Scoped `rg` checks over active code/config/docs and current planning surfaces return zero old-name matches
5. Full test suite passes with zero regressions
6. Python 3.10-3.14 compatibility is preserved

Plans:

- [x] 28-01-PLAN.md — Rename `pytest_bdd_toolchain` to `pytest_bdd_toolchain`, move development scripts into
      `src/pytest_bdd_toolchain/tool/`, register `pbt-*` entrypoints, update references, and validate the rename.

### Phase 29: CCK Closure

**Goal:** Close CCK-01 through CCK-07 documentation gaps from v1.0 milestone audit — reconcile requirements, specs, and verification artifacts with actual implementation state.
**Depends on:** Phase 28
**Plans:** 1/1 plans complete

**Success Criteria** (what must be TRUE):

1. All CCK-01..07 requirements marked [x] in REQUIREMENTS.md
2. Spec 045 success criteria all marked [x]
3. Phase 29 VERIFICATION.md exists
4. ROADMAP.md includes Phase 29

Plans:

- [x] 29-01-PLAN.md — Close gap: CCK-01..CCK-07 - Allure CCK compatibility evidence

### Phase 30: Add a new phase from todo

**Goal:** [To be planned]
**Requirements**: TBD
**Depends on:** Phase 29
**Plans:** 2/2 plans complete

Plans:

- [x] 30-PLAN.md

- [x] TBD (run /gsd-plan-phase 30 to break down) (completed 2026-07-02)
- [x] 30-02-PLAN.md — Migrate codebase to BLQ import-form rules and re-enable BLQ1506/1508/1509/1510/1511/1512

### Phase 31: Add __tracebackhide__ = True module-level to all src/pytest_bdd/ modules

**Goal:** Add `__tracebackhide__ = True` at the module level in all non-empty Python files under `src/pytest_bdd/` to hide library-internal implementation details from pytest tracebacks when user tests fail.
**Requirements**: None
**Depends on:** Phase 30
**Plans:** 3/3 plans complete

Plans:
**Wave 1**

- [x] 31-01-PLAN.md — Scaffold integration test to verify traceback hiding behavior

**Wave 2** *(blocked on Wave 1 completion)*

- [x] 31-02-PLAN.md — Automate module-level tracebackhide insertion and remove redundant declarations

**Wave 3** *(blocked on Wave 2 completion)*

- [x] 31-03-PLAN.md — Verify full test suite and confirm traceback hiding integration tests pass

### Phase 32: Implement Unbound Feature Detection

**Goal:** Detect `.feature` and `.feature.md` files (plus shortcut formats: `.url`, `.desktop`, `.webloc`) in `features_base_dir` that exist on disk but are NOT bound to any pytest test collection. Report them as `pytest.skipped` items with configurable severity (skip/warn/error).
**Requirements**: TBD
**Depends on:** Phase 31
**Plans:** 2 plans

**Success Criteria** (what must be TRUE):

  1. Unbound feature files appear as SKIPPED in pytest output with a clear reason ("Feature not bound to any test module")
  2. Bound feature files are NOT reported as skipped — no false positives
  3. Feature files with `@unbound` tag are excluded from detection per BDD conventions
  4. Severity is configurable: INI `bdd_unbound_features` and CLI `--unbound-features` with values skip (default), warn, error
  5. Shortcut files (`.url`, `.desktop`, `.webloc`) resolve to their target files before checking collection status
  6. Symlinks are followed during recursive scan; symlink loops are safely handled
  7. xdist worker nodes do not run duplicate detection — only the controller node injects skip items
  8. Unit tests cover detection logic; integration tests verify end-to-end behavior through pytester

Plans:
**Wave 1**

- [x] 32-01-PLAN.md — Config model + CLI/INI registration + unbound.py detection module + hook integration

**Wave 2** *(blocked on Wave 1 completion)*

- [x] 32-02-PLAN.md — Unit tests (16) and integration tests (10) for unbound feature detection

### Phase 33: Gather failed CI logs into workflow artifact

**Goal:** After any `main.yml` run with failed matrix cells, produce a single downloadable workflow artifact containing raw step output with metadata headers for each failed cell, without modifying existing `test` or `test-xdist-remote` jobs.
**Requirements**: TBD
**Depends on:** Phase 32
**Plans:** 1/1 plans complete

Plans:

- [x] 33-01-PLAN.md — Add collect-failed-logs job to main.yml with github-script and upload-artifact

### Phase 34: Move remaining CCK testing utilities out of pytest_bdd/testing

**Goal:** Move CCK testing utilities from library to toolchain and fix UnboundFeatureItem crash
**Requirements**: CCK-MIGRATION, UNBOUND-FIX
**Depends on:** Phase 33
**Plans:** 1/1 plans complete

Plans:

- [x] 34-01-PLAN.md — Move cck.py to toolchain, update consumer imports, delete pytest_bdd/testing/ and fix UnboundFeatureItem crash

### Phase 35: Improve library typing using best practices from awesome-python-typing

**Goal:** Establish strict static typing across production and non-test toolchain code, configure Pyright verifytypes package validation, and implement isolated wheel typing contract tests.

**Scope amendment (2026-07-13):** `src/pytest_bdd_toolchain/case/**` is test-suite code and is excluded from the strict-mypy implementation gate. All remaining `pytest_bdd` and non-test `pytest_bdd_toolchain` modules remain in scope without suppressions.
**Requirements**: TBD
**Depends on:** Phase 34
**Plans:** 68/140 plans executed

Plans:

- [x] 35-04-PLAN.md
- [x] 35-05-PLAN.md
- [x] 35-06-PLAN.md
- [x] 35-07-PLAN.md
- [x] 35-08-PLAN.md
- [x] 35-09-PLAN.md
- [x] 35-10-PLAN.md
- [x] 35-100-PLAN.md
- [x] 35-101-PLAN.md
- [x] 35-102-PLAN.md
- [x] 35-103-PLAN.md
- [x] 35-104-PLAN.md
- [x] 35-105-PLAN.md
- [x] 35-106-PLAN.md
- [x] 35-107-PLAN.md
- [x] 35-108-PLAN.md
- [x] 35-109-PLAN.md
- [x] 35-11-PLAN.md
- [x] 35-110-PLAN.md
- [x] 35-111-PLAN.md
- [x] 35-112-PLAN.md
- [x] 35-113-PLAN.md
- [x] 35-114-PLAN.md
- [x] 35-115-PLAN.md
- [x] 35-116-PLAN.md
- [x] 35-117-PLAN.md
- [x] 35-118-PLAN.md
- [x] 35-119-PLAN.md
- [x] 35-12-PLAN.md
- [x] 35-120-PLAN.md
- [x] 35-121-PLAN.md
- [x] 35-122-PLAN.md
- [x] 35-123-PLAN.md
- [x] 35-124-PLAN.md
- [x] 35-125-PLAN.md
- [x] 35-126-PLAN.md
- [x] 35-127-PLAN.md
- [x] 35-128-PLAN.md
- [x] 35-129-PLAN.md
- [x] 35-13-PLAN.md
- [x] 35-130-PLAN.md
- [x] 35-131-PLAN.md
- [x] 35-132-PLAN.md
- [x] 35-133-PLAN.md
- [x] 35-134-PLAN.md
- [x] 35-135-PLAN.md
- [x] 35-136-PLAN.md
- [x] 35-137-PLAN.md
- [x] 35-14-PLAN.md
- [x] 35-15-PLAN.md
- [x] 35-16-PLAN.md
- [x] 35-17-PLAN.md
- [x] 35-18-PLAN.md
- [x] 35-19-PLAN.md
- [x] 35-20-PLAN.md
- [x] 35-21-PLAN.md
- [x] 35-22-PLAN.md
- [x] 35-23-PLAN.md
- [x] 35-24-PLAN.md
- [x] 35-25-PLAN.md
- [x] 35-26-PLAN.md
- [x] 35-27-PLAN.md
- [x] 35-28-PLAN.md
- [x] 35-29-PLAN.md
- [x] 35-30-PLAN.md
- [ ] 35-31-PLAN.md
- [ ] 35-32-PLAN.md
- [ ] 35-33-PLAN.md
- [ ] 35-34-PLAN.md
- [ ] 35-35-PLAN.md
- [ ] 35-36-PLAN.md
- [ ] 35-37-PLAN.md
- [ ] 35-38-PLAN.md
- [ ] 35-39-PLAN.md
- [ ] 35-40-PLAN.md
- [ ] 35-41-PLAN.md
- [ ] 35-42-PLAN.md
- [ ] 35-43-PLAN.md
- [ ] 35-44-PLAN.md
- [ ] 35-45-PLAN.md
- [ ] 35-46-PLAN.md
- [ ] 35-47-PLAN.md
- [ ] 35-48-PLAN.md
- [ ] 35-49-PLAN.md
- [ ] 35-50-PLAN.md
- [ ] 35-51-PLAN.md
- [ ] 35-52-PLAN.md
- [ ] 35-53-PLAN.md
- [ ] 35-54-PLAN.md
- [ ] 35-55-PLAN.md
- [ ] 35-56-PLAN.md
- [ ] 35-57-PLAN.md
- [ ] 35-58-PLAN.md
- [ ] 35-59-PLAN.md
- [ ] 35-60-PLAN.md
- [ ] 35-61-PLAN.md
- [ ] 35-62-PLAN.md
- [ ] 35-63-PLAN.md
- [ ] 35-64-PLAN.md
- [ ] 35-65-PLAN.md
- [ ] 35-66-PLAN.md
- [ ] 35-67-PLAN.md
- [ ] 35-68-PLAN.md
- [ ] 35-69-PLAN.md
- [ ] 35-70-PLAN.md
- [ ] 35-71-PLAN.md
- [ ] 35-72-PLAN.md
- [ ] 35-73-PLAN.md
- [ ] 35-74-PLAN.md
- [ ] 35-75-PLAN.md
- [ ] 35-76-PLAN.md
- [ ] 35-77-PLAN.md
- [ ] 35-78-PLAN.md
- [ ] 35-79-PLAN.md
- [ ] 35-80-PLAN.md
- [ ] 35-81-PLAN.md
- [ ] 35-82-PLAN.md
- [ ] 35-83-PLAN.md
- [ ] 35-84-PLAN.md
- [ ] 35-85-PLAN.md
- [ ] 35-86-PLAN.md
- [ ] 35-87-PLAN.md
- [ ] 35-88-PLAN.md
- [ ] 35-89-PLAN.md
- [ ] 35-90-PLAN.md
- [ ] 35-91-PLAN.md
- [ ] 35-92-PLAN.md
- [ ] 35-93-PLAN.md
- [ ] 35-94-PLAN.md
- [ ] 35-95-PLAN.md
- [ ] 35-96-PLAN.md
- [ ] 35-97-PLAN.md
- [ ] 35-98-PLAN.md
- [ ] 35-99-PLAN.md

- [x] 35-01-PLAN.md — Establish no-bypass mypy, Pyright strict Python-3.10/All discovery config, Allure stubs, and baseline ledger.
- [x] 35-02-PLAN.md — Make the enum, importlib metadata/resources, parser, and path compatibility source slice strict-mypy clean and record isolated evidence.
- [x] 35-03-PLAN.md — Make the pathlib, pytest, runtime compatibility, struct-BDD, and sys compatibility source slice strict-mypy clean and record isolated evidence.
- [x] 35-04..35-137-PLAN.md — One hundred thirty-four independently executable source slices; each owns at most five modules and only its own evidence record.
- [x] 35-138-PLAN.md — Build the fresh-wheel, venv-local mypy/Pyright public contract and load its Development BDD acceptance coverage through the real toolchain E2E paths.
- [x] 35-139-PLAN.md — Run and classify full-scope upstream-Pyright strict and ty discovery; promote neither without evidence.
- [x] 35-140-PLAN.md — Aggregate isolated evidence into the canonical inventory and run independently asserted final source and installed-wheel gates.

### Phase 36: Integrate BDD/ATDD tests into development workflow and UAT phase

**Goal:** [To be planned]
**Requirements**: TBD
**Depends on:** Phase 35
**Plans:** 0 plans

Plans:

- [ ] TBD (run /gsd-plan-phase 36 to break down)
