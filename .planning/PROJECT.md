# pytest-bdd-ng

## What This Is

A pytest plugin that brings BDD (Behavior-Driven Development) to Python testing. Users write Gherkin `.feature` files, define step implementations with `@given`/`@when`/`@then` decorators, and get full Cucumber-compatible reporting. The library handles Gherkin parsing (plain and Markdown), scenario collection, step matching, execution lifecycle, and multiple output formatters — all integrated natively into pytest's hook system.

## Core Value

**Reliable, frictionless BDD testing in pytest.** Scenario execution must be deterministic, step matching must be intuitive, and reporting must be interoperable. Everything else can fail; this cannot.

## Requirements

### Validated

- ✓ Gherkin `.feature` file parsing (plain + Markdown) — existing
- ✓ Optional Go-ctypes parser backend for performance — existing
- ✓ Step definition registration via `@given`/`@when`/`@then` decorators — existing
- ✓ Step matching with 7 parser types (re, parse, cfparse, cucumber_expression, etc.) — existing
- ✓ Scenario collection via `scenario()` and `scenarios()` API — existing
- ✓ pytest hook integration (17 plugins registered via `pytest11`) — existing
- ✓ Scenario execution lifecycle with before/after/around hooks — existing
- ✓ Cucumber Messages protocol compliance — existing
- ✓ Cucumber JSON/JUnit/pretty formatters — existing
- ✓ Struct BDD (YAML/JSON/TOML/HOCON feature definitions) — existing
- ✓ Test group ordering for CI — existing
- ✓ Live reporting bridge (gherkin_message_reporter) — existing
- ✓ Python 3.10-3.14 + PyPy support — existing
- ✓ Cross-platform (Linux, macOS, Windows) — existing
- ✓ pytest-xdist distributed execution support — existing

### Active

- [ ] **STAB-01**: Remove or re-implement dead Allure logger plugin
- [x] **STAB-02**: Eliminate 96 `return None` antipattern instances in non-hook code
- [x] **STAB-03**: Replace 22 bare `except Exception:` catch-alls with specific types or logged warnings
- [ ] **STAB-04**: Add deprecation warning to legacy `--cucumberjson` CLI flag
- [ ] **REF-01**: Split `scenario_run.py` (1422 lines) into separate modules (Run, ScenarioRun, FeatureRuntimeBinding)
- [ ] **REF-02**: Refactor code generator plugin into class-based pattern matching other plugins
- [ ] **REF-03**: Reduce other large files (>400 lines) where practical
- [x] **SIM-01**: Streamline compatibility layer — remove dead shims, consolidate (09-01: deps+modules removed; 09-02: matrix.py split)
- [ ] **SIM-02**: Unify programming approaches across plugins (consistent patterns)
- [ ] **SIM-03**: Audit and prune underused plugin/utility modules
- [ ] **TEST-01**: Improve unit test coverage for core modules (scenario_run, steps, parsers)
- [ ] **TEST-02**: Expand BDD feature tests in `features/` for undocumented behaviors
- [ ] **TEST-03**: Add integration tests for edge cases in step matching and scenario execution
- [ ] **DOC-01**: Ensure all public API functions have docstrings
- [ ] **DOC-02**: Update DEVELOPMENT.rst with current practices
- [ ] **DOC-03**: Add migration guide for users coming from pytest-bdd (original)

### Out of Scope

- New feature development (parsers, formatters, protocols) — stabilization phase only
- Performance optimization beyond what cleanup naturally achieves — not a perf milestone
- Python version support changes — keep 3.10-3.14 matrix
- Docker/Compose infrastructure changes — not relevant to stabilization
- Real-time chat or collaboration features — not applicable

## Context

- **Origin:** Fork/evolution of `pytest-bdd` with expanded Cucumber Messages support and modern tooling.
- **Codebase state:** Production-grade library with 17 pytest plugins, Go parser backend, and full Cucumber protocol compliance. Architecture is plugin-oriented with model/collector/parser/step-definition layers. Accumulated tech debt from rapid feature development.
- **Test infrastructure:** `tests/` organized as unit/feature/hook/e2e/model/messages/messages_coverage. BDD acceptance tests live in `features/` directory as `.feature.md` files. Coverage tooling includes `coverage.py`, Codecov, and Coveralls.
- **Development workflow:** ATDD/BDD — acceptance tests in `features/` before implementation. Specs in `specs/` for planning. Pre-commit hooks enforce ruff linting and formatting. Tox matrix runs Python 3.10-3.14 × pytest 7.0-latest.

## Constraints

- **Compatibility:** Must support Python 3.10-3.14 and pytest >=7.0.0. Breaking changes require major version bump.
- **Performance:** No regression in Gherkin parse times or test collection speed.
- **Security:** No pickle-based patterns in production code paths. Test infrastructure exceptions must be documented.
- **Style:** Must follow ruff rules. Must not introduce comments unless asked. Must use `attrs` over `dataclass`. Must follow `StashBound` pattern for config stash access.

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Split `scenario_run.py` into 3+ modules | 1422-line file is unmaintainable | — Pending |
| Remove dead Allure plugin vs reimplement | Dead code deceives users who install `[allure]` extra | — Pending |
| Use specific exceptions instead of bare `except Exception:` | Silent failures mask real bugs | — Pending |
| `return None` → explicit handling | AGENTS.md rule, 96 violations | — Pending |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd-transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd-complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
Last updated: 2026-05-12 after initialization
