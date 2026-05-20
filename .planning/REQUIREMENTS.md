# Requirements: pytest-bdd-ng

**Defined:** 2026-05-12
**Core Value:** Reliable, frictionless BDD testing in pytest

## v1 Requirements

### Stabilization

- [x] **STAB-01**: Remove or re-implement dead Allure logger plugin (entrypoint.py registers plugin but all implementation is commented out)
- [x] **STAB-02**: Eliminate 96 `return None` antipattern instances in non-hook code, replacing with sentinels or explicit exceptions
- [x] **STAB-03**: Replace 22 bare `except Exception:` catch-alls with specific exception types or logged warnings with `exc_info=True`
- [x] **STAB-04**: Add deprecation warning to legacy `--cucumberjson` CLI flag (TODO at cucumber_json/entrypoint.py:31)

### Refactoring

- [x] **REF-01**: Split `scenario_run.py` (1422 lines) into `model/run.py`, `model/scenario_run.py`, `model/feature_binding.py` with characterization tests first
- [x] **REF-02**: Refactor `code_generator` plugin into class-based pattern matching other plugins (entrypoint.py + plugin.py class)
- [x] **REF-03**: Reduce other large files (>400 lines) where practical (target: live_formatter_runtime.py 823L, message_validation.py 672L, steps.py 627L)

### Simplification

- [x] **SIM-01**: Streamline compatibility layer — remove `pathlib2` (Python 2 backport), `docopt-ng` (legacy CLI parser)
- [x] **SIM-02**: Unify programming approaches across plugins — consistent class + entrypoint + hook.py pattern, fix plugin-internal direct imports
- [x] **SIM-03**: Audit and prune underused plugin/utility modules (dead code, unused imports, stale modules)

### Documentation

- [x] **DOC-01**: Ensure all public API functions in `src/pytest_bdd/__init__.py` have docstrings
- [x] **DOC-02**: Update DEVELOPMENT.rst with current conventions (StashBound, attrs, testing patterns)
- [x] **DOC-03**: Create migration guide documenting differences from pytest-bdd (original) — fixture injection, hooks, configuration

### Testing

- [x] **TEST-01**: Improve unit test coverage for core modules (`scenario_run.py`, `steps.py`, `parsers.py`)
- [x] **TEST-02**: Expand BDD feature tests in `features/` for undocumented behaviors and edge cases
- [x] **TEST-03**: Add integration tests for edge cases in step matching priority and scenario execution lifecycle

## v2 Requirements

- Async step definitions (`async def` step functions) — highest user demand
- Better error messages for step matching failures (reduce support burden)
- Duplicate scenario detection across feature files (safety)
- Working example directory (`examples/`) for onboarding

## Out of Scope

| Feature | Reason |
|---------|--------|
| Built-in web dashboard | Scope creep — use existing Messages bridge with external tools |
| Custom Gherkin dialect extensions | Breaks Cucumber interoperability |
| Scenario-to-scenario dependencies | Violates BDD isolation principles |
| Global mutable context object | Undermines pytest fixture isolation |
| Automatic retry of all failures | Masks flaky tests, anti-pattern |
| New step parser types | Feature set already exceeds all Python BDD competitors |
| Performance optimization | Not a perf milestone — cleanup naturally improves performance |
| Python version support changes | Keep 3.10-3.14 matrix |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| STAB-01 | Phase 1 — Foundation Cleanup | Complete |
| STAB-02 | Phase 2 — Code Quality Gates | Complete |
| STAB-03 | Phase 2 — Code Quality Gates | Complete |
| STAB-04 | Phase 1 — Foundation Cleanup | Complete |
| REF-01 | Phase 3 — Core Runtime Refactor | Complete |
| REF-02 | Phase 4 — Plugin Refactoring | Complete |
| REF-03 | Phase 4 — Plugin Refactoring | Complete |
| SIM-01 | Phase 9 — Compatibility Streamlining | Complete |
| SIM-02 | Phase 10 — Pattern Unification | Complete |
| SIM-03 | Phase 11 — Audit & Prune | Complete |
| DOC-01 | Phase 7 — Documentation | Complete |
| DOC-02 | Phase 7 — Documentation | Complete |
| DOC-03 | Phase 7 — Documentation | Complete |
| TEST-01 | Phase 5 — Unit Test Fortification | Deferred (coverage 56% vs 70% target) |
| TEST-02 | Phase 8 — BDD Acceptance Testing | Deferred (27 BDD failures remain) |
| TEST-03 | Phase 6 — Integration Testing | Complete |

**Coverage:**
- v1 requirements: 16 total
- Mapped to phases: 16
- Unmapped: 0

---
*Requirements defined: 2026-05-12*
*Last updated: 2026-05-19 — checkboxes synced with completed phases; TEST-01/TEST-02 deferred to next milestone*
