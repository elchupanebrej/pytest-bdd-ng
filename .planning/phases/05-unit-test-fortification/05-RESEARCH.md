# Phase 05: Unit Test Fortification - Research

**Researched:** 2026-05-14
**Domain:** Python unit test coverage — pytest BDD library core modules
**Confidence:** HIGH

## Summary

This phase adds comprehensive unit test coverage for five core modules totaling ~2,440 source lines. The modules span message-oriented runtime state (`model/run.py`, `model/scenario_run.py`, `model/feature_binding.py`), step definition management (`steps.py`), and step pattern parsing (`parsers.py`). Currently **zero direct unit tests exist** for any of these five modules. All existing coverage comes from integration tests (testdir-based) and characterization tests that were written during Phases 2-3 as behavioral safety nets.

The key challenge is the mixed testability profile: model modules are pure data classes — directly instantiable with `attrs` constructors, making them ideal for fast unit tests. `steps.py` requires a live pytest runtime context (step registration via `@given`/`@when`/`@then` decorators, fixture injection, `testdir` runner), making testdir integration the only viable approach. `parsers.py` is frozen — tests must exercise the public API (`StepParser.build()`, individual parser constructors, `is_matching()`, `parse_arguments()`) without touching internals.

**Primary recommendation:** Use direct-instantiation unit tests (`@pytest.mark.unit`) for all three model modules; testdir-based integration tests for `steps.py`; pure public-API tests (extending `tests/args/`) for parsers. Migrate all existing model/hook/steps test files into `tests/unit/` with marker tags and updated import paths. Add `pytest-cov` as dev dependency for coverage feedback loops.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Step definition registration/matching | API/Backend | — | `steps.py` manages pytest fixture injection, step registry; requires full pytest runtime |
| Session-level runtime state (Run) | API/Backend | — | `model/run.py` is a `StashBound` subclass managing `pytest.config.stash` — pure in-memory state |
| Per-scenario execution state (ScenarioRun) | API/Backend | — | `model/scenario_run.py` tracks step lifecycle, transitions — pure data, no I/O |
| Per-feature parsed data (FeatureRuntimeBinding) | API/Backend | — | `model/feature_binding.py` indexes Gherkin AST into registries — pure data, no I/O |
| Step pattern parsing (7 parser types) | API/Backend | — | `parsers.py` converts step strings to argument dicts — pure computation, no I/O |

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| TEST-01 | Improve unit test coverage for core modules (`scenario_run.py`, `steps.py`, `parsers.py`) | All findings below support coverage gap filling for expanded module set (run.py, scenario_run.py, feature_binding.py, steps.py, parsers.py) |

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| pytest | >=7.0.0 | Test runner, fixtures, assertions | Already project dependency; universal Python test framework |
| pytest-cov | latest (dev dep) | Coverage measurement, `--cov-report=term-missing` | Not installed [VERIFIED: `import pytest_cov` fails]. Must add to `[project.optional-dependencies].dev` |
| unittest.mock | stdlib | Mocking Go parser availability, plugin registrations | Already project standard [VERIFIED: TESTING.md]. No third-party mock library needed |
| attrs | >=24 | Data class construction for test fixtures | Already project standard [VERIFIED: CONVENTIONS.md]. Model modules use `@define(slots=True)` |
| returns | latest (dev dep) | `Maybe`, `Result`, `Success`, `Failure` in tests | Already used in contract tests [VERIFIED: tests/model/test_scenario_run_returns_contract.py] |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| PyHamcrest | latest (allure tests only) | `assert_that()`, `has_entry()` | Only for allure-specific tests [VERIFIED: TESTING.md]. All other tests use vanilla `assert` |
| cucumber_messages | latest (dev dep) | Construct `GherkinDocument`, `Pickle`, `Step` objects for test data | Model tests that need real message objects for `FeatureRuntimeBinding` construction |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| testdir integration for model modules | Direct instantiation `@pytest.mark.unit` | Testdir adds 10-50x overhead per test; model modules are pure data — direct instantiation is 100x faster |
| pytest-cov | coverage.py CLI | pytest-cov integrates with `--cov-report=term-missing` for per-module feedback loops; coverage.py CLI is batch-only |

**Installation:**
```bash
uv add --dev pytest-cov
```

## Architecture Patterns

### System Architecture Diagram
```text
┌─────────────────────────────────────────────────────────────────┐
│                        TEST INPUT                               │
│  (Gherkin strings, Pickle objects, FixtureRequest mocks)        │
└───────────────┬─────────────────────────────────────────────────┘
                │
    ┌───────────┴───────────┬──────────────────┬──────────────────┐
    ▼                       ▼                  ▼                  ▼
┌──────────┐    ┌───────────────────┐  ┌──────────────┐  ┌──────────────┐
│ parsers  │    │     steps.py      │  │ model/run.py │  │ model/       │
│  .py     │    │  (testdir only)   │  │              │  │ scenario_    │
│          │    │                   │  │ (direct)     │  │ run.py       │
│ (direct  │    │ @given → registry │  │              │  │              │
│  API)    │    │ testdir.runpytest │  │ Run() +      │  │ ScenarioRun()│
│          │    │    │              │  │ assert       │  │ + assert     │
│ parse()  │    │    ▼              │  │              │  │              │
│ build()  │    │ result.assert_    │  │ as_dict()    │  │ as_dict()    │
│ is_      │    │ outcomes()        │  │ state        │  │ state        │
│ matching │    │                   │  │ transitions  │  │ transitions  │
└────┬─────┘    └───────────────────┘  └──────┬───────┘  └──────┬───────┘
     │                                       │                  │
     ▼                                       ▼                  ▼
┌──────────┐                         ┌───────────────────────────────┐
│  args/   │                         │        ASSERT                 │
│  tests   │                         │  Coverage: >85% line (model)  │
│  (extend)│                         │  Coverage: >80% line (steps)  │
└──────────┘                         │  No pickle in production code │
                                     │  pragma:no cover justified    │
                                     └───────────────────────────────┘
```

### Recommended Project Structure
```text
tests/
├── unit/                              # NEW: all unit tests by source module
│   ├── model/
│   │   ├── test_run.py                # Run class tests (direct instantiation)
│   │   ├── test_scenario_run.py       # ScenarioRun class tests
│   │   ├── test_feature_binding.py    # FeatureRuntimeBinding tests
│   │   └── test_context_error_state.py # ContextErrorState, lifecycle enums
│   ├── test_steps.py                  # Step tests (testdir-based, tagged @unit)
│   └── test_parsers.py               # Parser public API tests (direct)
├── args/                              # EXISTING: extend for parser edge cases
│   ├── regex/test_args.py
│   ├── parse_/test_args.py
│   ├── cfparse/test_args.py
│   ├── cucumber_expression/test_args.py
│   └── heuristic/test_args.py
├── feature/                           # UNCHANGED: integration tests stay
├── hook/                              # MIGRATED: → tests/unit/ + markers
├── model/                             # MIGRATED: → tests/unit/model/
├── steps/                             # MIGRATED: → tests/unit/ + markers
├── e2e/                               # UNCHANGED
└── ...
```

### Pattern 1: Direct Instantiation Unit Test (Model Modules)

**What:** Import class, construct with `attrs` factories, call methods, assert on return values and state.

**When to use:** `model/run.py`, `model/scenario_run.py`, `model/feature_binding.py` — all use `@define(slots=True)` with no pytest runtime coupling.

**Example:**
```python
# tests/unit/model/test_scenario_run.py
from __future__ import annotations

import pytest

from pytest_bdd.model.run import Run, RunStage, RunStatus, HookPhase
from pytest_bdd.model.scenario_run import ScenarioRun


@pytest.mark.unit
def test_scenario_run_advance_transition() -> None:
    """Transition index increments on each advance_transition call."""
    run = Run(id="r1", run_ref=..., status=RunStatus.ok)
    sr = ScenarioRun(
        id="sr1",
        run_ref=...,
        active_hook=HookPhase.before_scenario,
        stage=RunStage.idle,
        status=RunStatus.ok,
        active_set=...,
        run=run,
    )
    assert sr.transition_index == 0
    sr.advance_transition()
    assert sr.transition_index == 1
```

### Pattern 2: Testdir-Based Integration Test (steps.py)

**What:** Use `testdir` fixture to create `.feature` files and conftest with step definitions, run pytest, assert outcomes.

**When to use:** `steps.py` — requires pytest runtime context for `@given`/`@when`/`@then` decorators, fixture injection, step registry lifecycle.

**Example:**
```python
# tests/unit/test_steps.py (testdir-based, tagged @pytest.mark.unit)
from __future__ import annotations

import pytest

pytestmark = [pytest.mark.unit]


def test_decorator_builder_creates_step_definition(testdir) -> None:
    """Step decorator stores definition on function's __pytest_bdd_step_definitions__."""
    testdir.makeconftest("""
        from pytest_bdd import given
        @given("I have a {thing}")
        def have_thing(thing):
            return thing
    """)
    testdir.makefile(".feature", steps="Feature: Test\n  Scenario: S\n    Given I have a widget")
    result = testdir.runpytest()
    result.assert_outcomes(passed=1)
```

### Pattern 3: Public API Parser Test (parsers.py)

**What:** Call `StepParser.build()`, construct parser instances directly, test `is_matching()` and `parse_arguments()`.

**When to use:** `parsers.py` — frozen, test via public API only. No internal function testing.

**Example:**
```python
# tests/args/regex/test_args.py (extend existing)
from __future__ import annotations

import pytest
from pytest_bdd.parsers import re, StepParser


@pytest.mark.unit
def test_re_parser_parse_arguments_with_named_groups() -> None:
    """Named groups in regex patterns are extracted as arguments."""
    parser = re(r"I have (?P<count>\d+) (?P<item>\w+)")
    args = parser.parse_arguments(None, "I have 5 apples")
    assert args == {"count": "5", "item": "apples"}
```

### Anti-Patterns to Avoid

- **Mocking `Run`/`ScenarioRun` internals:** Model modules should be tested with real instances, not mocks. Only mock external dependencies (Go parser, plugin registrations).
- **Testing private methods directly:** `parsers.py` frozen — no `_get_parameter_type_registry()` tests. Stick to public API: `StepParser.build()`, `is_matching()`, `parse_arguments()`.
- **Pickle-based test fixtures:** Per success criterion 5, no pickle serialization in production code paths. Use `attrs` constructors or factory functions.
- **Skipping `as_dict()` serialization:** Every model class has `as_dict()` — test these for stable serialization contracts (already done in characterization tests; extend for uncovered branches).
- **Using `pytest.raises` without `match=`:** Always include `match=` parameter to verify the right exception is raised, not just any exception of that type.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Coverage measurement | Custom coverage scripts | `pytest-cov` with `--cov-report=term-missing` | Already standard in Python ecosystem; integrates with `.coveragerc`; per-module feedback loops |
| Complex assertion logic | Custom assertion helpers | Vanilla `assert` with descriptive message | Pytest rewrites assertions for rich diffs; project already uses this pattern [VERIFIED: TESTING.md] |
| Test data construction | Inline `cucumber_messages` dicts | Factory functions (`_build_gherkin_document()`, `_build_run()`) | Already exists in characterization tests [VERIFIED: tests/hook/test_scenario_run_characterization.py]; reuse/extend, don't duplicate |
| Mocking pytest internals | Custom mock framework | `unittest.mock.patch()` + `MagicMock` | Already project standard [VERIFIED: TESTING.md]; well-documented patterns for Go parser patching |

**Key insight:** The model modules (`run.py`, `scenario_run.py`, `feature_binding.py`) are designed for testability — `@define(slots=True)`, no I/O, no pytest coupling. Direct instantiation with `attrs` constructors is the natural testing pattern. Do not introduce testdir overhead for these modules.

## Runtime State Inventory

> Phase 5 is greenfield test creation — no rename/refactor. Skip runtime state inventory.

## Common Pitfalls

### Pitfall 1: testdir Overhead for Model Tests

**What goes wrong:** Using `testdir.makefile()` + `testdir.runpytest()` to test `Run` class takes 2-5s per test vs <0.01s for direct instantiation. At 100+ tests, this adds minutes to test suite runtime.

**Why it happens:** `testdir` spawns a subprocess pytest run to exercise model code that doesn't need a pytest runtime at all.

**How to avoid:** Direct `from pytest_bdd.model.run import Run`; construct with `attrs`; call methods; assert. Only use `testdir` for `steps.py` which genuinely requires pytest runtime.

**Warning signs:** Test file imports `testdir` fixture when testing `Run`, `ScenarioRun`, or `FeatureRuntimeBinding`.

### Pitfall 2: Parser Behavior Drift Under Freeze

**What goes wrong:** Adding tests that inadvertently test internal parser behavior (e.g., `_get_parameter_type_registry()`, `rebuild_expression_in_test_context()`), coupling tests to implementation details that may change after the freeze lifts.

**Why it happens:** `parsers.py` has many internal methods with complex logic. Temptation to test them directly for coverage.

**How to avoid:** All parser tests go through public entry points: `StepParser.build(parserlike)`, `parser.is_matching(request, name)`, `parser.parse_arguments(request, name)`. If a branch can't be reached via public API, it remains uncovered until freeze lifts.

**Warning signs:** Test calls `parser._get_parameter_type_registry()`, `parser.rebuild_expression_in_test_context()`, or accesses `parser.parsers_are_built`.

### Pitfall 3: Marker Not Registered Causing CI Warnings

**What goes wrong:** Adding `@pytest.mark.unit` without registering it in `pyproject.toml` markers list causes pytest to emit `PytestUnknownMarkWarning` on every test run. With `filterwarnings = ["error"]` (current config), this becomes a hard failure.

**Why it happens:** `pyproject.toml` currently has no `"unit"` marker entry [VERIFIED: grep for `unit` in markers list returned no match].

**How to avoid:** Add `"unit: fast in-memory unit tests for core modules"` to `[tool.pytest.ini_options].markers` list and `"tests/unit/** = instant"` to `test_group_paths` (latter already exists). Do this before writing any tests.

**Warning signs:** `PytestUnknownMarkWarning` in test output. CI failure on clean commit.

### Pitfall 4: Overlapping Test Functions After Migration

**What goes wrong:** Migrating tests from `tests/hook/`, `tests/model/`, `tests/steps/` into `tests/unit/` creates duplicate test function names if multiple source directories had same-named tests.

**Why it happens:** `test_scenario_run_characterization.py` and `test_scenario_run_model.py` both may define similar test function names. Combining into `tests/unit/model/test_scenario_run.py` requires deduplication.

**How to avoid:** Audit all test function names across source directories before migration. Rename duplicates with contextual prefixes. Use `pytest --co` to detect name collisions during migration.

**Warning signs:** `pytest` discovers only one of two identically-named test functions.

### Pitfall 5: StashBound Initialization Without pytest Config

**What goes wrong:** `Run` extends `StashBound` which requires `pytest.config.stash` for `initialize_in_stash()` and `from_stash()`. Direct instantiation works fine for most tests, but `initialize_for_session()` and `initialize_for_config()` need real stash objects.

**Why it happens:** `StashBound.find_in_stash()` calls `config.stash` which requires a real pytest `Config` object or compatible mock.

**How to avoid:** For tests that exercise `initialize_for_session()` or `initialize_for_config()`, use a mock `SimpleNamespace` with `stash` attribute (pattern already used in `tests/model/gherkin_document/test_feature_context_lookup.py` [VERIFIED: TESTING.md]). For all other `Run` tests, use direct constructor: `Run(id="...", run_ref=..., status=...)`.

**Warning signs:** `AttributeError: 'NoneType' object has no attribute 'stash'` when calling stash-related methods.

## Code Examples

Verified patterns from existing codebase:

### Direct Model Instantiation Test
```python
# Source: tests/hook/test_scenario_run_characterization.py (lines 65-113)
# Pattern: factory functions for reuse, direct attrs construction
def _build_run() -> Run:
    return Run(
        id="run-1",
        run_ref=LifecycleObjectRef(kind="run", object_id="run-1", name="run", is_active=True),
        status=RunStatus.ok,
    )


def _build_scenario_run() -> ScenarioRun:
    run = _build_run()
    # ... construct with all required fields
    return scenario_run
```

### Serialization Contract Test
```python
# Source: tests/hook/test_scenario_run_characterization.py (lines 116-141)
# Pattern: assert against expected dict for stable serialization
def test_lifecycle_object_ref_serialization_is_stable() -> None:
    active_ref = LifecycleObjectRef(
        kind="scenario",
        object_id="scenario-1",
        name="Scenario",
        source="Pickle",
        is_active=True,
    )
    assert active_ref.as_dict() == _lifecycle_dict(
        kind="scenario",
        object_id="scenario-1",
        name="Scenario",
        source="Pickle",
    )
```

### Error State Assertion
```python
# Source: tests/model/test_scenario_run_returns_contract.py (Phase 2 contract tests)
# Pattern: assert on return types from Maybe/Result-returning methods
def test_require_active_scenario_run_raises_when_none() -> None:
    run = Run(id="r1", run_ref=..., status=RunStatus.ok)
    with pytest.raises(RuntimeError, match="unavailable"):
        run.require_active_scenario_run(hook_name="test_hook")
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `return None` for missing values | `returns` library (`Maybe`, `Result`) | Phase 2 | Model methods return `Maybe` or `Result` — tests must unwrap or assert on `Nothing`/`Failure` |
| `scenario_run.py` god module (1422L) | Split into `run.py` (783L) + `scenario_run.py` (332L) + `feature_binding.py` (374L) | Phase 3 | Tests must import from correct owning module; no compatibility re-exports |
| No `# pragma: no cover` policy | Justification comments required for new instances | Phase 5 (this phase) | D-11: `# pragma: no cover — reason: <justification>` format |
| `assert_that()` (Hamcrest) in some tests | Vanilla `assert` everywhere except allure tests | Phase 4 | New tests use plain `assert`; no Hamcrest imports needed |

**Deprecated/outdated:**
- `pathlib2` shims — still in codebase but unused by model modules; do not import in new tests
- Legacy `cucumberjson` CLI flag — removed in Phase 1; do not reference in tests

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Model module methods that return `Maybe`/`Result` have correct type annotations — tests can unwrap safely | Code Examples | Tests pass incorrectly if return type annotation is wrong — caught by mypy |
| A2 | `pytest-cov` works with `--cov-report=term-missing` on this project's pytest version (7.0+) | Standard Stack | Coverage feedback loop fails — must use coverage.py CLI directly |
| A3 | All existing test files in `tests/hook/`, `tests/model/`, `tests/steps/` are safe to move to `tests/unit/` with updated imports — no hidden dependencies on their current directory location | Architecture Patterns | Import errors after migration — requires fixup commit |
| A4 | `testdir` fixture from `pytester` is always available (enabled via `addopts = "-p pytester"` in pyproject.toml) | Common Pitfalls | steps.py tests fail if pytester unavailable |

## Open Questions

1. **Should `fail_under = 70` be added to `.coveragerc` before or after writing tests?**
   - What we know: D-09 specifies `fail_under = 70` as a global safety net. Current `.coveragerc` has no `fail_under` [VERIFIED: file content]. Coverage tool not installed [VERIFIED: `import pytest_cov` fails].
   - What's unclear: Whether current coverage is above or below 70%. Running coverage now would answer this but requires installing `pytest-cov` first.
   - Recommendation: Add `fail_under = 70` to `.coveragerc` as a config-only change (no test behavior change). Install `pytest-cov` as first Wave 0 task. Run baseline coverage to determine if 70 is safe.

2. **How many of 9 global `# pragma: no cover` instances are in target modules vs elsewhere?**
   - What we know: 38 total instances across the codebase. In target modules: only `parsers.py` has 13 (all protocol stubs + `NotImplementedError` guards — likely justified). Zero instances in `steps.py`, `model/run.py`, `model/scenario_run.py`, `model/feature_binding.py` [VERIFIED: grep results].
   - What's unclear: Whether the 25 non-target pragma instances need auditing or can be deferred.
   - Recommendation: Focus D-10 audit on the 13 parsers.py instances (verify each has or needs justification comment). The other 25 can be addressed in a follow-up wave if time permits, since they're outside phase scope.

3. **Should model module tests use factory functions from characterization tests or write new factories?**
   - What we know: `tests/hook/test_scenario_run_characterization.py` has `_build_run()` and `_build_scenario_run()` factory functions. These construct fully-populated objects with realistic defaults.
   - What's unclear: Whether these factories should be extracted to a shared `tests/unit/conftest.py` or duplicated per test file.
   - Recommendation: Extract to `tests/unit/conftest.py` as fixtures with `scope="function"`. This avoids duplication while keeping tests independent. Use `@pytest.fixture` for `run()`, `scenario_run()`, `feature_binding()` — each constructing a valid default instance.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| pytest | All tests | ✓ | — (project dep) | — |
| pytest-cov | Coverage feedback, `--cov-report=term-missing` | ✗ | — | `coverage.py` CLI: `coverage run -m pytest && coverage report -m` |
| unittest.mock | Go parser patching, plugin mocking | ✓ | stdlib | — |
| attrs | Test data construction | ✓ | — (project dep) | — |
| cucumber_messages | Test data (GherkinDocument, Pickle) | ✓ | — (project dep) | — |
| returns | Maybe/Result assertions | ✓ | — (project dep) | — |

**Missing dependencies with no fallback:**
- **pytest-cov**: Not installed. Must add to dev dependencies before coverage-driven development begins. Fallback (`coverage.py` CLI) works but lacks `--cov-report=term-missing` per-module view.

**Missing dependencies with fallback:**
- None — all other dependencies are already project dependencies or stdlib.

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest >=7.0.0 |
| Config file | `pyproject.toml` `[tool.pytest.ini_options]` |
| Quick run command | `uv run python -m pytest tests/unit/ -q` |
| Full suite command | `uv run python -m pytest tests/ -q` |
| Coverage command (after install) | `uv run python -m pytest tests/unit/ --cov=pytest_bdd --cov-report=term-missing` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| TEST-01 (run.py) | Run state transitions, stash initialization, scenario lifecycle | unit | `pytest tests/unit/model/test_run.py -x` | ❌ Wave 0 |
| TEST-01 (scenario_run.py) | ScenarioRun state, RunNode lifecycle, context errors | unit | `pytest tests/unit/model/test_scenario_run.py -x` | ❌ Wave 0 |
| TEST-01 (feature_binding.py) | FeatureRuntimeBinding build, AST indexing, pickle compilation | unit | `pytest tests/unit/model/test_feature_binding.py -x` | ❌ Wave 0 |
| TEST-01 (steps.py) | Step decorators, matcher priority, registry hierarchy, fixture injection | integration (testdir) | `pytest tests/unit/test_steps.py -x` | ❌ Wave 0 |
| TEST-01 (parsers.py) | StepParser.build(), parser matching, argument extraction, heuristic fallback | unit | `pytest tests/args/ -x` | ✅ extends existing |
| — | Test migration: existing tests → `tests/unit/` with `@pytest.mark.unit` | unit | `pytest tests/unit/ -m unit -x` | ❌ Wave 0 |
| — | `# pragma: no cover` audit (D-10, D-11) | manual audit | N/A — code review step | N/A |
| — | `fail_under = 70` in `.coveragerc` (D-09) | config | `pytest --cov --cov-report=term` | ❌ Wave 0 |
| — | `@pytest.mark.unit` marker registration (D-05) | config | `pytest --markers` | ❌ Wave 0 |

### Sampling Rate

- **Per task commit:** `uv run python -m pytest tests/unit/ -x -q`
- **Per wave merge:** `uv run python -m pytest tests/ -q` (full suite)
- **Phase gate:** Full suite green + coverage targets met (>85% model, >80% steps, >70% global)

### Wave 0 Gaps

- [ ] `tests/unit/model/test_run.py` — covers Run class (783L, >85% target)
- [ ] `tests/unit/model/test_scenario_run.py` — covers ScenarioRun + RunNode (332L, >85% target)
- [ ] `tests/unit/model/test_feature_binding.py` — covers FeatureRuntimeBinding (374L, >85% target)
- [ ] `tests/unit/test_steps.py` — covers steps.py StepDefinitionManager patterns (760L, >80% target)
- [ ] `tests/unit/conftest.py` — shared fixtures: `run`, `scenario_run`, `feature_binding`, `gherkin_document`
- [ ] `tests/args/regex/test_args.py` — extend for `re` parser edge cases
- [ ] `tests/args/parse_/test_args.py` — extend for `parse` parser edge cases
- [ ] `tests/args/cfparse/test_args.py` — extend for `cfparse` parser edge cases
- [ ] `tests/args/cucumber_expression/test_args.py` — extend for cucumber_expression edge cases
- [ ] `tests/args/heuristic/test_args.py` — extend for heuristic parser fallback chain
- [ ] Framework install: `uv add --dev pytest-cov` — coverage tooling not installed
- [ ] Config: `@pytest.mark.unit` marker in `pyproject.toml`
- [ ] Config: `fail_under = 70` in `.coveragerc`
- [ ] Migration: `tests/hook/test_scenario_run_characterization.py` → `tests/unit/model/` with markers
- [ ] Migration: `tests/hook/test_run_transitions.py` → `tests/unit/model/` with markers
- [ ] Migration: `tests/hook/test_scenario_run_model.py` → `tests/unit/model/` with markers
- [ ] Migration: `tests/model/test_scenario_run_returns_contract.py` → `tests/unit/model/` with markers
- [ ] Migration: `tests/model/gherkin_document/test_feature_context_lookup.py` → `tests/unit/model/` with markers
- [ ] Migration: `tests/steps/test_given.py` → `tests/unit/` with markers
- [ ] Migration: `tests/steps/test_unicode.py` → `tests/unit/` with markers

## Security Domain

> `security_enforcement` not explicitly set to false in config — treating as enabled.

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|------------------|
| V2 Authentication | no | N/A — test framework, no auth surface |
| V3 Session Management | no | N/A |
| V4 Access Control | no | N/A |
| V5 Input Validation | yes — parsers | Step parsers validate Gherkin patterns; `_EXPECTED_PARSER_BUILD_ERRORS` handles malformed input. Tests should cover: regex injection attempts, parse format string abuse, undefined parameter types |
| V6 Cryptography | no | N/A |

### Known Threat Patterns for Python/pytest

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Regex DoS via crafted step patterns | Denial of Service | `re.fullmatch()` prevents catastrophic backtracking by design (no partial matches). Test with long/complex patterns to verify no timeout. |
| `eval()`-like code injection via parse format strings | Elevation of Privilege | `parse` library does not eval — it's a safe pattern matcher. No risk. |
| Pickle deserialization in test data | Elevation of Privilege | Project constraint: no pickle in production code paths. Tests using pickled Gherkin data (`tests/gherkin_integration/test_pickles_load.py`) are outside phase scope. |

## Sources

### Primary (HIGH confidence)
- `.planning/codebase/TESTING.md` — Test framework, mock conventions, run commands, file organization [VERIFIED: file read]
- `.planning/codebase/CONVENTIONS.md` — Naming, style, import organization, StashBound pattern [VERIFIED: file read]
- `.planning/codebase/STRUCTURE.md` — Module layout, test directory structure, plugin inventory [VERIFIED: file read]
- `src/pytest_bdd/steps.py` (760 lines) — StepDefinitionManager, Matcher, Registry, Definition, decorator_builder [VERIFIED: file read, lines 1-760]
- `src/pytest_bdd/model/run.py` (783 lines) — Run(StashBound), LifecycleObjectRef, ActiveObjectSet, enums, ReportingContextSnapshot [VERIFIED: file read, lines 1-783]
- `src/pytest_bdd/model/scenario_run.py` (332 lines) — ScenarioRun, RunNode, StepRun [VERIFIED: file read, lines 1-332]
- `src/pytest_bdd/model/feature_binding.py` (374 lines) — FeatureRuntimeBinding, AST indexing, pickle compilation [VERIFIED: file read, lines 1-374]
- `src/pytest_bdd/parsers.py` (769 lines) — StepParser, re, parse, cfparse, string, cucumber_expression, cucumber_regular_expression, heuristic [VERIFIED: file read, lines 1-769]
- `.coveragerc` — Branch coverage enabled, includes `pytest_bdd/*` and `tests/*` [VERIFIED: file read]
- `pyproject.toml` `[tool.pytest.ini_options].markers` — No `unit` marker exists [VERIFIED: grep returned no match]
- `tests/hook/test_scenario_run_characterization.py` (379 lines) — Factory functions, serialization contract tests [VERIFIED: file read, lines 1-230]

### Secondary (MEDIUM confidence)
- `tests/feature/test_steps.py` (1474 lines) — 41 testdir-based step integration tests, existing patterns [VERIFIED: file read, lines 1-60]
- `tests/args/regex/test_args.py` (105 lines) — Parser test pattern using testdir [VERIFIED: file read, lines 1-40]
- `tests/model/test_scenario_run_returns_contract.py` — Maybe/Result contract test patterns [VERIFIED: file existence confirmed]

### Tertiary (LOW confidence)
- None — all claims verified against codebase

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — verified via file reads and `import` probe; only gap is `pytest-cov` not installed
- Architecture: HIGH — verified via full source reads of all 5 target modules plus existing test patterns
- Pitfalls: HIGH — based on Phase 2-4 experience with this codebase, validated against actual `pyproject.toml` config and `filterwarnings = ["error"]` setting

**Research date:** 2026-05-14
**Valid until:** 2026-06-14 (30 days — stable testing domain, no major framework changes expected)

**Module size summary (verified):**
| Module | Lines | Target | Existing Tests | Test Approach |
|--------|-------|--------|---------------|---------------|
| `steps.py` | 760 | >80% | 44 (testdir-based) | New testdir tests in `tests/unit/test_steps.py` |
| `model/run.py` | 783 | >85% | ~15 (characterization + contract) | Direct instantiation in `tests/unit/model/test_run.py` |
| `model/scenario_run.py` | 332 | >85% | ~15 (shared with run.py) | Direct instantiation in `tests/unit/model/test_scenario_run.py` |
| `model/feature_binding.py` | 374 | >85% | 3 (context lookup) | Direct instantiation in `tests/unit/model/test_feature_binding.py` |
| `parsers.py` | 769 | N/A (frozen) | ~25 (args/ subdirs) | Extend `tests/args/` with public API tests |

**Pragma: no cover audit scope (target modules only):**
| File | Instances | Assessment |
|------|-----------|------------|
| `parsers.py` | 13 | All are protocol stubs (`StepParserProtocol`) or `NotImplementedError` guards in `@singledispatchmethod` init methods. Likely all justified. Must add D-11 comments. |
| `steps.py` | 0 | No instances |
| `model/run.py` | 0 | No instances |
| `model/scenario_run.py` | 0 | No instances |
| `model/feature_binding.py` | 0 | No instances |
