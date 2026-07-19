# Phase 14: Gap Closure - Research

**Researched:** 2026-05-20
**Domain:** Python test coverage augmentation + BDD feature test triage/repair
**Confidence:** HIGH

## Summary

Phase 14 closes the v1.0 milestone by addressing two deferred testing requirements: raising unit test coverage from ~30% to 70% per-module (TEST-01, exempting entrypoints/scripts/_gherkin_go/testing), and resolving all BDD feature test failures (TEST-02) to zero. Additionally, it applies the Phase 12 D-18 E2E per-file module split, adds `@pytest.mark.unit` markers to 25 test files, completes model module tests and steps.py testdir tests, extends parser tests with a pragma audit, and expands feature documentation for undocumented behaviors.

**Current state baseline:** All test files now live under `tests/cases/` (Phase 12 migration complete). Running the current unit+integration test suite yields ~30% total line+branch coverage across `src/pytest_bdd/` and 20 vulture-related test failures (not phase targets). Coverage on core modules ranges from 12% (util/inspect_extra) to 92% (util/toolz_test). The E2E test suite skips 61 of 64 BDD scenarios due to tag-based filtering (@allure, @docker, @slow, @xdist); the 27 referenced failures are hidden behind these skips and must be surfaced, triaged, and resolved.

**Primary recommendation:** Run a quick coverage gap scan to identify the biggest uncovered functions per core module (D-05), then use a mix of direct-instantiation unit tests and testdir-based integration tests to drive per-module coverage to ≥70%. For BDD failures, remove tag-based exclusions temporarily, categorize failures by error type, fix by category (D-06/D-07), then apply the per-file E2E module split (D-10).

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| TEST-01 | Improve unit test coverage for core modules to 70% per-module line+branch | Coverage gap analysis (§Coverage Gap Analysis), per-module thresholds (§Coverage Strategy), standard testing patterns (§Architecture Patterns) |
| TEST-02 | Expand BDD feature tests in `features/` for undocumented behaviors and edge cases; resolve all 27 failing BDD tests | BDD failure triage strategy (§BDD Failure Landscape), E2E per-file split pattern (§E2E Module Split), feature gap identification (§Fold Pending: D-15) |
</phase_requirements>

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** Broad coverage augmentation — write tests across all modules evenly, not focused on a specific subset
- **D-02:** Mix of unit tests (tests/unit/, tests/model/) and integration tests (testdir-based in tests/feature/) to carry the coverage lift
- **D-03:** Per-module minimum threshold of 70% line+branch coverage on `src/pytest_bdd/`
- **D-04:** entrypoint.py files, script/ modules, and the _gherkin_go/ ctypes bridge are exempt from the per-module 70% threshold
- **D-05:** Quick coverage gap scan first — run coverage report to identify biggest uncovered functions/classes per module, start with easy wins (error paths, edge cases), then tackle complex gaps
- **D-06:** Automated triage first — run suite with verbose failure output, script-categorize failures by error type (StepNotFound, AssertionError, etc.), then review and fix by category
- **D-07:** Case-by-case judgment for step-def vs feature-file fixes: if the feature describes intended behavior, implement the missing step definition; if the feature describes outdated/wrong behavior, update the feature file
- **D-08:** Fix production code bugs discovered during BDD triage — do not defer them
- **D-09:** Single full-suite verification run at the end after all fixes are applied
- **D-10:** Split E2E test modules per feature file — each E2E module must bind only its owned feature file(s). Whole-directory scenario loaders are forbidden. Replaces the current `tests/e2e/test_e2e.py` with per-file modules
- **D-11:** Migrate 6 remaining test files to tests/unit/ with `@pytest.mark.unit` markers (from STATE.md pending)
- **D-12:** Write model module unit tests for run.py, scenario_run.py, feature_binding.py (from STATE.md pending)
- **D-13:** Write steps.py testdir-based integration tests (from STATE.md pending)
- **D-14:** Extend parser edge case tests for parsers.py (FROZEN — tests only, no modifications to parsers.py) + audit and justify or remove all `# pragma: no cover` instances
- **D-15:** Expand feature tests for undocumented behaviors — add new .feature.md files under features/ for gaps identified in Phase 8 audit

### the agent's Discretion
- Exact module-by-module test allocation within the broad augmentation strategy
- Specific test structure and naming, following established conventions (TESTING.md, CONVENTIONS.md)
- Order of triage categories after automated categorization of BDD failures
- File-by-file organization of the E2E module split
- Which specific undocumented behaviors to cover with new .feature.md files
- Per-file pragma audit decisions (keep justified, remove unjustified)

### Deferred Ideas (OUT OF SCOPE)
None — discussion stayed within phase scope. All STATE.md pending items were folded in.
</user_constraints>

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Unit test coverage augmentation | Python Test Suite (unit/) | — | Direct instantiation of source classes; no pytest runner needed |
| testdir-based integration tests | Python Test Suite (feature/) | — | pytester creates isolated pytest runs with in-memory file trees |
| BDD feature test triage | E2E Test Suite (e2e/) | Feature files (features/) | E2E tests load .feature.md files via `scenarios()` and execute step definitions |
| E2E module split (D-10) | E2E Test Suite (e2e/) | — | Per-feature-file test modules replace monolithic loader |
| Coverage configuration | Project Config (pyproject.toml, .coveragerc) | — | `.coveragerc` sets `fail_under = 70` and `branch = true` |
| Pragma audit (D-14) | Source Code (src/pytest_bdd/) | — | Review-only: inspect `# pragma: no cover` annotations for justification |
| Documented behavior expansion (D-15) | Feature files (features/) | E2E Test Suite (e2e/) | New .feature.md files require step definitions in conftest.py or per-module step files |

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| pytest | >=7.0.0 | Test runner + fixture framework | Project baseline; all tests use pytest |
| pytest-cov | >=7.1.0 | Coverage measurement (branch-aware) | Already in dev dependencies; `.coveragerc` configured |
| pytest (pytester) | built-in | testdir fixture for integration tests | Standard pytest plugin; `addopts = "-p pytester"` in pyproject.toml |
| unittest.mock | stdlib | Mocking external dependencies (Go parser, network) | Already used throughout test suite; no new dep needed |
| attrs | project dep | `@define(slots=True)` for data classes | Project convention per AGENTS.md; tests use real attrs objects |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| PyHamcrest | (project dep) | Expressive assertions for allure/e2e tests | Only in allure-specific test contexts |
| pytest-xdist | >=3.8.0 | Parallel/distributed test execution | E2E tests marked @xdist; not needed for coverage lift |
| pytest-order | (project dep) | Test ordering via markers | Already configured; group ordering via test_group_paths |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| pytest-cov | coverage.py directly | pytest-cov integrates with pytest plugin system and respects `--ignore` flags |
| Manual coverage gap analysis | diff-cover | diff-cover targets changed lines only; phase needs per-module absolute coverage (D-03) |

**Installation:**
```bash
# All core deps already in pyproject.toml; ensure test extras installed:
uv pip install pytest-order pytest-httpserver pytest-xdist pytest-cov execnet PyHamcrest deepdiff GitPython PyYAML
```

**Version verification:** All packages above already installed in the project's virtual environment — verified via `uv pip list` during research. No new external package installations required for this phase beyond what's already in pyproject.toml `[project.optional-dependencies] test`.

## Package Legitimacy Audit

> No new external packages are introduced in this phase. All required tools (pytest, pytest-cov, pytest-xdist, unittest.mock) are either stdlib or already listed as project dependencies in pyproject.toml. The phase is testing-only — it writes test code that exercises existing source, using existing test infrastructure.

**Packages removed due to slopcheck [SLOP] verdict:** none
**Packages flagged as suspicious [SUS]:** none
**Packages requiring verification:** none — no new packages introduced

## Architecture Patterns

### System Architecture Diagram

```
┌──────────────────────────────────────────────────────────────────────┐
│                        PHASE 14: GAP CLOSURE                         │
│                                                                      │
│  ┌─────────────┐     ┌──────────────────┐     ┌───────────────────┐  │
│  │ .coveragerc  │────▶│ Coverage Gap     │────▶│ Per-module test   │  │
│  │ (fail_under  │     │ Scan (D-05)      │     │ allocation        │  │
│  │  = 70)       │     │ pytest-cov       │     │ (unit + testdir)  │  │
│  └─────────────┘     │ --cov-report=json│     └────────┬──────────┘  │
│                       └──────────────────┘              │            │
│                                                         ▼            │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │              TEST-01: Coverage Augmentation                  │   │
│  │                                                              │   │
│  │  tests/cases/unit/unit/     tests/cases/integration/feature/ │   │
│  │  ├── test_steps.py          ├── test_steps.py                │   │
│  │  ├── test_parsers.py        ├── test_outline.py              │   │
│  │  ├── test_parsers_unit.py   ├── test_scenario_execution_*.py │   │
│  │  ├── model/test_run.py      └── ...                          │   │
│  │  ├── model/test_scenario_run.py                               │   │
│  │  └── model/test_feature_binding.py                            │   │
│  │         │                                                     │   │
│  │         ▼                                                     │   │
│  │  src/pytest_bdd/{steps,parsers,model,scenario,...}.py         │   │
│  │         │                                                     │   │
│  │         ▼                                                     │   │
│  │  Per-module ≥70% line+branch coverage                         │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │              TEST-02: BDD Failure Resolution                  │   │
│  │                                                              │   │
│  │  features/*.feature.md ──▶ tests/cases/e2e/e2e/              │   │
│  │         │                      │                              │   │
│  │         │              ┌───────▼────────┐                     │   │
│  │         │              │ Triage (D-06)  │                     │   │
│  │         │              │ Categorize by  │                     │   │
│  │         │              │ error type:    │                     │   │
│  │         │              │ StepNotFound,  │                     │   │
│  │         │              │ AssertionError,│                     │   │
│  │         │              │ ImportError    │                     │   │
│  │         │              └───────┬────────┘                     │   │
│  │         │                      │                              │   │
│  │         │         ┌────────────▼────────────┐                 │   │
│  │         │         │ Fix by category (D-07)  │                 │   │
│  │         │         │ ├─ Missing step def →   │                 │   │
│  │         │         │ │  add to conftest.py   │                 │   │
│  │         │         │ ├─ Outdated feature →   │                 │   │
│  │         │         │ │  update .feature.md   │                 │   │
│  │         │         │ └─ Production bug →     │                 │   │
│  │         │         │    fix source (D-08)    │                 │   │
│  │         │         └────────────┬────────────┘                 │   │
│  │         │                      │                              │   │
│  │         │         ┌────────────▼────────────┐                 │   │
│  │         │         │ E2E Module Split (D-10) │                 │   │
│  │         │         │ test_feature_001.py     │                 │   │
│  │         │         │ test_feature_002.py ... │                 │   │
│  │         │         └────────────┬────────────┘                 │   │
│  │         │                      │                              │   │
│  │         └──────────────────────▼──────────────────────────    │   │
│  │                   Full-suite verification (D-09)              │   │
│  │                   All BDD tests pass, zero failures           │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │              FOLDED PENDING ITEMS                             │   │
│  │                                                              │   │
│  │  D-11: 25 files → add @pytest.mark.unit markers              │   │
│  │  D-12: model/ test gap analysis → new unit tests             │   │
│  │  D-13: steps.py testdir test augmentation                    │   │
│  │  D-14: parser edge case tests + pragma audit (38 instances)  │   │
│  │  D-15: new .feature.md files for undocumented behaviors      │   │
│  └──────────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────────┘
```

### Recommended Project Structure (new test files)
```
tests/cases/
├── unit/unit/
│   ├── model/                          # D-12: Model module unit tests
│   │   ├── test_run.py                 # ✅ exists (64% on lifecycle.py)
│   │   ├── test_scenario_run.py        # ✅ exists (52% on scenario_run.py)
│   │   ├── test_feature_binding.py     # ✅ exists
│   │   └── test_run_access.py          # NEW: cover model/run_access.py (40%)
│   ├── test_steps.py                   # ✅ exists (augment: definition.py 52%)
│   ├── test_parsers.py                 # ✅ exists (49% → target 70%)
│   ├── test_parsers_unit.py            # ✅ exists (augment)
│   ├── test_scenario.py                # NEW: cover scenario.py (49%)
│   ├── test_scenario_locator.py        # NEW: cover scenario_locator.py (33%)
│   ├── test_parser.py                  # NEW: cover parser.py (50%)
│   ├── test_tag_expression.py          # NEW: cover tag_expression.py (14%)
│   └── test_collector.py               # NEW: cover collector.py
├── integration/feature/
│   ├── test_steps.py                   # ✅ exists (D-13 augment)
│   ├── test_step_matching_priority.py  # ✅ exists
│   └── test_step_matching_ambiguous.py # ✅ exists
└── e2e/e2e/
    ├── test_feature_001_launch.py      # D-10: split from test_e2e.py
    ├── test_feature_002_nonstrict.py
    ├── ... (one per feature file, ~47 modules)
    └── test_messages_fixed.py          # Existing non-scenario tests remain
```

### Pattern 1: Unit Test for Coverage Gap (Direct Instantiation)
**What:** Tests exercise a source class directly without pytest testdir. Use `Path("/fake/...")` for path-like args, `pytest.raises` for error paths.
**When to use:** Fast coverage lift for error handlers, edge cases, branch paths in any source module.
**Example:**
```python
# Source: tests/cases/unit/unit/test_collector_batch.py (existing pattern)
from pathlib import Path
import pytest
from pytest_bdd.collector_batch import FeatureBatchParser


def test_register_after_flush_raises() -> None:
    """Registering after flush raises RuntimeError."""
    parser = FeatureBatchParser()
    parser.register(Path("/fake/file.feature"))
    parser.flush()
    with pytest.raises(RuntimeError, match="flushed"):
        parser.register(Path("/fake/file2.feature"))
```

### Pattern 2: testdir Integration Test
**What:** Uses `testdir` fixture to create in-memory file trees, run pytest subprocess, assert outcomes.
**When to use:** Testing end-to-end step execution, fixture injection, error reporting, and plugin interactions.
**Example:**
```python
# Source: tests/cases/integration/feature/test_steps.py (existing pattern)
def test_steps(testdir):
    """Verify steps are executed one by one."""
    testdir.makefile(
        ".feature",
        steps="""\
        Feature: Steps are executed one by one
            Scenario: Executed step by step
                Given I have a foo fixture with value "foo"
    """,
    )
    testdir.makeconftest("""\
        from pytest_bdd import given
        @given('I have a foo fixture with value "foo"', target_fixture="foo")
        def foo():
            return "foo"
    """)
    result = testdir.runpytest()
    result.assert_outcomes(passed=1, failed=0)
```

### Pattern 3: E2E Per-File Module (D-10)
**What:** Each .feature.md file gets its own test module that calls `scenarios("path/to/feature.md", filter_=...)`. No whole-directory `scenarios(".", ...)`.
**When to use:** All E2E feature tests after split.
**Example:**
```python
# tests/cases/e2e/e2e/test_feature_001_launch.py
from pytest_bdd import scenarios

_EXCLUDED_TAGS = {"allure", "docker", "slow", "xdist"}


def _filter(config, feature, pickle):
    tag_names = {str(t.name).lstrip("@").lower() for t in getattr(pickle, "tags", ())}
    return tag_names.isdisjoint(_EXCLUDED_TAGS)


scenarios("../../../../features/01 Tutorial/01 Launch.feature.md", filter_=_filter)
```

### Anti-Patterns to Avoid
- **Whole-directory scenario loaders:** `scenarios(".", ...)` loads ALL feature files. D-10 explicitly forbids this. Use per-file `scenarios("path/to/feature.md", ...)` instead.
- **Testing through the UI for coverage:** Don't rely on slow E2E tests for per-module coverage. Use fast unit tests for branch coverage, reserve E2E for acceptance.
- **Skipping error paths:** Error handlers (`except:` blocks, `raise` paths) are the lowest-hanging fruit for coverage lift. Always test both success and error paths.
- **Mocking internals for unit tests:** Build real objects via factory functions rather than mocking internal pytest-bdd components. Use `unittest.mock` only for external boundaries (Go parser, network).

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Coverage measurement | Custom coverage tool | pytest-cov (already configured) | Branch coverage, HTML reports, fail_under threshold all built in |
| Test directory isolation | Custom temp dir management | pytest testdir fixture (pytester) | Creates isolated file trees, runs real pytest, auto-cleanup |
| BDD scenario loading | Custom feature file scanner | pytest_bdd.scenarios() | Already the project's own API; use per-file, not whole-directory |
| Failure categorization | Manual grep through output | pytest --tb=line + script parsing of failure types | D-06: script-categorize by error type (StepNotFound, AssertionError, etc.) |
| Tag-based test filtering | Custom tag parser | pytest_bdd tag filtering via `filter_` callback | Already implemented in test_e2e.py `_exclude_default_bdd_features` |

**Key insight:** The project already has mature test infrastructure (testdir, scenarios(), group ordering, coverage config). The gap is not in tooling but in test quantity — existing patterns should be replicated, not replaced.

## Runtime State Inventory

> This is NOT a rename/refactor phase. Runtime state inventory not applicable — no strings renamed, no data migrated, no service config changed. All work is additive (new tests, test fixes, test restructuring).

| Category | Items Found | Action Required |
|----------|-------------|------------------|
| Stored data | None — in-memory parsing only | — |
| Live service config | None | — |
| OS-registered state | None | — |
| Secrets/env vars | None | — |
| Build artifacts | None — no name changes | — |

## Common Pitfalls

### Pitfall 1: Coverage Percentage Inflation
**What goes wrong:** Running E2E tests with coverage enabled inflates per-module coverage numbers because E2E exercise code paths indirectly. The 70% threshold (D-03) is per-module line+branch — but .coveragerc `fail_under = 70` applies to the total aggregate.
**Why it happens:** `.coveragerc` sets a single global threshold. Per-module tracking requires post-processing.
**How to avoid:** After full-suite run, use `coverage json -o coverage.json` and parse per-file percentages. Flag any module below 70% for targeted unit test writing. The `fail_under` in .coveragerc gates the final verification.
**Warning signs:** Full-suite coverage passes 70% but individual modules (scenario_locator.py at 33%, tag_expression.py at 14%) are far below.

### Pitfall 2: BDD Skip Blindness
**What goes wrong:** The current E2E test_e2e.py skips 61 of 64 scenarios via `_exclude_default_bdd_features`. The "27 failures" are hidden behind these skips. Removing the exclusion filter reveals failures but also introduces environment-dependent failures (Docker, xdist, allure).
**Why it happens:** Tag-based filtering excludes tests that require specific infrastructure. Some excluded tests legitimately need Docker/allure/xdist; others are excluded only because they were never fixed.
**How to avoid:** Triage in layers:
1. First, remove ONLY the `_EXCLUDED_TAGS` filter and run. Categorize all failures by error type.
2. For each failure category: determine if the failure is a missing step definition (fixable), a production bug (fixable), or an infrastructure dependency (re-mark with appropriate exclusion tag).
3. Do NOT remove infrastructure exclusions blindly — @docker, @xdist, @allure tests may genuinely require those environments.

### Pitfall 3: Pragma no cover Over-Removal
**What goes wrong:** Removing `# pragma: no cover` from defensive code (platform-specific paths, ctypes fallback, abstract protocol methods) without adding tests for those paths creates coverage gaps that can't be filled on the current platform.
**Why it happens:** Some code paths are unreachable on Windows (POSIX-only) or require specific Python versions (<3.11 compatibility shims).
**How to avoid:** Audit each pragma instance against a justification checklist:
- Abstract protocol methods → keep (exercised via concrete implementations)
- `TYPE_CHECKING` blocks → keep (never executed at runtime)
- Platform-specific guards (POSIX/Windows) → keep if the testing platform can't reach both
- Defensive `except Exception:` → investigate if testable, keep if truly unreachable
- `if __name__ == "__main__":` in scripts → keep (script modules exempt per D-04)

### Pitfall 4: Model Module Test Duplication
**What goes wrong:** Writing new model tests that duplicate existing characterization tests in `tests/cases/unit/unit/model/test_scenario_run_characterization.py` or existing coverage in `test_run.py`, `test_scenario_run.py`, `test_feature_binding.py`.
**Why it happens:** D-12 says "Write model module unit tests" but model tests already exist. The gap is in uncovered paths, not missing test files.
**How to avoid:** Run coverage specifically on `src/pytest_bdd/model/run/lifecycle.py` (64%), `src/pytest_bdd/model/run/refs.py` (26%), `src/pytest_bdd/model/run_access.py` (40%), `src/pytest_bdd/model/scenario_run.py` (52%), `src/pytest_bdd/model/stash_access.py` (52%). Target the uncovered lines, not "writing a new test file from scratch."

## Coverage Gap Analysis

### Current State (unit + integration/feature tests only)

**Coverage command used:**
```bash
uv run python -m pytest tests/cases/unit/ tests/cases/integration/feature/ tests/cases/integration/hook/ \
  -p no:struct_bdd -q --cov=pytest_bdd --cov-report=term --cov-branch
```

### Core Modules Below 70% (excluding exempt categories)

| Module | Current Coverage | Gap to 70% | Primary Uncovered Areas |
|--------|-----------------|------------|------------------------|
| `tag_expression.py` | 14% | **56%** | Expression evaluation, error paths |
| `scenario_locator.py` | 33% | **37%** | Source loading, pickle iteration, URL locator |
| `model/run/refs.py` | 26% | **44%** | Object reference resolution |
| `model/run_access.py` | 40% | **30%** | Stash-bound accessors, error paths |
| `steps/manager.py` | 42% | **28%** | Step manager lifecycle |
| `scenario.py` | 49% | **21%** | Scenario decorator, filter logic, loader |
| `parsers.py` | 49% | **21%** | StepParser subclasses, pattern compilation |
| `parser.py` | 50% | **20%** | Gherkin parsing, structured BDD fallback |
| `model/scenario_run.py` | 52% | **18%** | RunStage transitions, error paths |
| `steps/definition.py` | 52% | **18%** | StepDefinition matching, fixture resolution |
| `steps/registry.py` | 52% | **18%** | Definition registry CRUD |
| `model/stash_access.py` | 52% | **18%** | Stash lookup, initialization |
| `model/scenario_report.py` | 46% | **24%** | Report collection, outcome aggregation |
| `plugin/.../plugin.py` (scenario_test_collector) | 57% | **13%** | Collection edge cases |
| `plugin/.../plugin.py` (pickle_runner) | 71% | ✅ above | Already past threshold |
| `plugin/.../run_transitions.py` | 81% | ✅ above | Already past threshold |
| `plugin/.../entrypoint.py` (scenario_test_collector) | 78% | ✅ above | Already past threshold |
| `util/pytest_extra.py` | 80% | ✅ above | Already past threshold |
| `util/toolz_extra.py` | 63% | **7%** | Functional composition edge cases |
| `util/tests_group_ordering.py` | 65% | **5%** | Marker application, path matching |
| `util/cucumber_formatters.py` | 73% | ✅ above | Already past threshold |
| `util/toolz_test.py` | 92% | ✅ above | Already past threshold |

**Exempt categories (not counted toward 70% threshold):**
- `src/pytest_bdd/script/*` — CLI entry points (D-04)
- `src/pytest_bdd/_gherkin_go/*` — ctypes bridge (D-04)
- `src/pytest_bdd/testing/*` — test support utilities (not production code)
- `src/pytest_bdd/plugin/*/entrypoint.py` — plugin entry points (D-04)
- `src/pytest_bdd/compatibility/*` — compatibility shims
- `src/pytest_bdd/types/*` — type definitions and exceptions
- Plugin formatters (`cucumber_*.py`) — covered by E2E formatter tests

### Quick Wins (error paths, edge cases)

1. **tag_expression.py (14%):** Expression evaluation with invalid inputs, edge cases (empty tags, unicode)
2. **model/run/refs.py (26%):** Object reference lookups with missing/None keys
3. **util/other.py (40%):** IdGenerator edge cases, identifier formatting with special characters
4. **steps/manager.py (42%):** Manager lifecycle after flush, duplicate registration
5. **scenario.py (49%):** Filter callback edge cases, empty scenario lists, loader error paths

## BDD Failure Landscape

### Current E2E Test Structure

The monolithic `tests/cases/e2e/e2e/test_e2e.py` loads 47 feature files via 61 individual `scenarios()` calls, each with `filter_=_exclude_default_bdd_features`. This filter excludes:

- Features tagged with: `@allure`, `@docker`, `@slow`, `@xdist`
- Specific excluded URIs: `07 report/08 xdist remote network reporting.feature.md`
- Specific excluded scenarios: HTML report gathering scenario in `07 report/02 Gathering.feature.md`

**Result:** 61 of 64 scenarios are SKIPPED. Only 3 pass (messages_fixed matrix validation tests).

### Failure Discovery Strategy (D-06)

```bash
# Step 1: Run without tag exclusions, capture all failures
uv run python -m pytest tests/cases/e2e/e2e/test_e2e.py -v --tb=short --no-header \
  2>&1 | tee bdd_failures.txt

# Step 2: Categorize failures by error type
# Categories: StepNotFound, AssertionError, ImportError, FixtureLookupError, etc.
```

### Expected Failure Categories

Based on the skip pattern and CONTEXT.md hints:

| Category | Likely Count | Root Cause | Fix Strategy |
|----------|-------------|------------|--------------|
| StepNotFound | ~10-15 | Missing step definitions for new/changed feature steps | Add step defs to `tests/cases/e2e/conftest.py` or per-module step files (D-07) |
| ImportError | ~5-8 | Missing optional dependencies (jq, allure, pandoc) or wrong import paths after Phase 12 migration | Install deps or conditionally skip |
| AssertionError | ~5-8 | Feature describes expected behavior but implementation changed; or step def assertion is stale | Update feature file (D-07) or fix step def |
| Infrastructure (Docker/xdist) | ~3-5 | Tests require Docker daemon or xdist workers not available on Windows | Keep excluded; tag appropriately |
| Production Bug | ~1-3 | Source code regression discovered via BDD scenario | Fix source code (D-08) |

### Feature Files Currently Untested (D-15 candidates)

Phase 8 audit (08-01-PLAN.md) identified gap areas. The following feature areas have .feature.md files but may lack comprehensive step definitions or are entirely excluded:

- **08 Go Parser:** `01 Go parser backend.feature.md` — requires Go shared library or fallback testing
- **09 Tag Expressions:** `01 Tag expression evaluation.feature.md` — tests exist but may need augmentation
- **10 Heading Validation:** `01 Heading validation.feature.md` — heading validation edge cases
- **11 Mimetype:** `01 Mimetype detection.feature.md` — mimetype detection
- **15 Compatibility:** `01 Python version compatibility.feature.md` — version matrix
- **16 Batch Collection:** `01 Batch collection edge cases.feature.md` — batch parsing edge cases

## Pragma Audit Summary

### Current State: 38 `# pragma: no cover` instances

Already justified (keep):
- `parsers.py` — 11 instances: abstract protocol methods (`...`) and `NotImplementedError` raises, exercised via concrete implementations
- `parser.py` — 2 instances: structured BDD guard (`STRUCT_BDD_INSTALLED`), defensive except
- `__init__.py` / compatibility modules — 3 instances: `TYPE_CHECKING` blocks
- `tag_expression.py` — 2 instances: abstract `NotImplementedError` in base class
- `types/failure_reasons.py` — 1 instance: Python < 3.11 compatibility import
- `scenario_locator.py` — 6 instances: callbacks exercised via integration tests
- `script/validate_feature_headings.py` — 2 instances: parser-level failures, `__main__` guard
- `util/toolz_test.py`, `util/data_table.py` — 2 instances: `TYPE_CHECKING` blocks

Needs investigation (verify if reachable with additional tests):
- `hook.py` line 207: `else` branch in hook resolution
- `plugin/gherkin_message_reporter/attachment_runtime.py` line 82: `else` branch
- `plugin/gherkin_message_reporter/transport_runtime.py` line 88: `except Exception` in transport
- `scenario_locator.py` lines 57, 66, 70, 74: callback protocol methods (already justified by pattern)
- `plugin/struct_bdd/model_builder.py` line 37: abstract `build` method
- `compatibility/parser.py` line 37: `ParserProtocol.parse_feature` abstract method

**Recommendation:** Audit each unjustified pragma by temporarily removing it, running the test suite, and checking if the line becomes covered. If still uncovered, the pragma is justified and should be documented with a comment. If newly covered, the pragma was masking a coverage gap.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest >=7.0.0 with pytester plugin |
| Config file | pyproject.toml `[tool.pytest.ini_options]` |
| Quick run command | `uv run python -m pytest tests/cases/unit/ tests/cases/integration/ -q --no-header` |
| Full suite command | `uv run python -m pytest tests/cases/ -q --no-header` |
| Coverage command | `uv run python -m pytest tests/cases/ --cov=pytest_bdd --cov-branch --cov-report=html` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| TEST-01-a | Per-module coverage ≥70% for `tag_expression.py` | unit | `pytest tests/cases/unit/unit/test_tag_expression.py -x --cov=pytest_bdd.tag_expression --cov-branch` | ❌ Wave 0 |
| TEST-01-b | Per-module coverage ≥70% for `scenario_locator.py` | unit | `pytest tests/cases/unit/unit/test_scenario_locator.py -x` | ❌ Wave 0 |
| TEST-01-c | Per-module coverage ≥70% for `scenario.py` | unit | `pytest tests/cases/unit/unit/test_scenario.py -x` | ❌ Wave 0 |
| TEST-01-d | Per-module coverage ≥70% for `parser.py` | unit | `pytest tests/cases/unit/unit/test_parser.py -x` | ❌ Wave 0 |
| TEST-01-e | Per-module coverage ≥70% for `steps/*` modules | unit | `pytest tests/cases/unit/unit/test_steps.py tests/cases/unit/unit/test_step_internals.py -x` | ✅ (augment) |
| TEST-01-f | Per-module coverage ≥70% for `parsers.py` | unit | `pytest tests/cases/unit/unit/test_parsers.py tests/cases/unit/unit/test_parsers_unit.py -x` | ✅ (augment) |
| TEST-02-a | All BDD scenarios pass without tag exclusions | e2e | `pytest tests/cases/e2e/e2e/ -v --tb=short` | ❌ split + fix |
| TEST-02-b | E2E modules split per feature file (D-10) | e2e | `pytest tests/cases/e2e/e2e/test_feature_*.py -v` | ❌ Wave 0 |
| D-11 | 25 test files have `@pytest.mark.unit` | marker check | `pytest --markers` or grep for `pytest.mark.unit` | ❌ Wave 0 |
| D-12 | Model module test coverage for run_access.py, refs.py, stash_access.py | unit | `pytest tests/cases/unit/unit/model/ -x --cov=pytest_bdd.model` | ✅ (augment new) |
| D-13 | Steps.py testdir test augmentation | integration | `pytest tests/cases/integration/feature/test_steps.py -x` | ✅ (augment) |
| D-14 | Parser edge case tests + pragma audit complete | unit | `pytest tests/cases/unit/unit/test_parsers.py tests/cases/unit/unit/test_parsers_unit.py -x` | ✅ (augment) |
| D-15 | New .feature.md files for undocumented behaviors | e2e | `pytest tests/cases/e2e/e2e/test_feature_*.py -v -k "new_feature"` | ❌ Wave 0 |

### Sampling Rate
- **Per task commit:** `uv run python -m pytest tests/cases/unit/ -q --no-header`
- **Per wave merge:** `uv run python -m pytest tests/cases/ -q --no-header --cov=pytest_bdd --cov-branch`
- **Phase gate:** Full suite green with per-module coverage ≥70% on non-exempt modules

### Wave 0 Gaps
- [ ] `tests/cases/unit/unit/test_tag_expression.py` — covers REQ TEST-01-a (tag_expression.py at 14%)
- [ ] `tests/cases/unit/unit/test_scenario_locator.py` — covers REQ TEST-01-b (scenario_locator.py at 33%)
- [ ] `tests/cases/unit/unit/test_scenario.py` — covers REQ TEST-01-c (scenario.py at 49%)
- [ ] `tests/cases/unit/unit/test_parser.py` — covers REQ TEST-01-d (parser.py at 50%)
- [ ] `tests/cases/unit/unit/model/test_run_access.py` — covers D-12 (run_access.py at 40%)
- [ ] `tests/cases/unit/unit/model/test_run_refs.py` — covers D-12 (refs.py at 26%)
- [ ] `tests/cases/e2e/e2e/test_feature_*.py` (47 modules) — covers D-10 split
- [ ] `tests/cases/unit/unit/test_collector.py` — covers collector.py
- [ ] `.coveragerc` per-module threshold enforcement mechanism
- [ ] 25 test files need `@pytest.mark.unit` markers (D-11)
- [ ] Pragma audit report document (D-14 justification list)
- [ ] New .feature.md files under `features/` (D-15)
- [ ] Framework install: all deps already installed (pytest, pytest-cov, pytest-order, pytest-xdist)

## Security Domain

> `security_enforcement` is enabled (absent from config = enabled by default).

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|------------------|
| V2 Authentication | no | — |
| V3 Session Management | no | — |
| V4 Access Control | no | — |
| V5 Input Validation | no | — (phase is testing-only, no production code changes except bug fixes) |
| V6 Cryptography | no | — |

**Note:** This is a testing-only phase. The only production code changes are bug fixes discovered during BDD triage (D-08). Standard security controls for the codebase are enforced by ruff's `S` (bandit) rules in pyproject.toml. No new security surface is introduced.

### Known Threat Patterns for pytest-bdd

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| `subprocess` calls in E2E test fixtures | Tampering | Already using `shlex` for argument quoting (e2e/conftest.py). No new subprocess patterns introduced. |
| File path injection in testdir | Tampering | testdir creates in-memory file trees; no real filesystem access |
| `eval()` or dynamic code execution | Elevation | Not used in test or source code |
| Hardcoded secrets in test files | Disclosure | No secrets in test fixtures; use environment variables via pytest fixtures |

## Sources

### Primary (HIGH confidence)
- `.coveragerc` — project coverage configuration (branch=true, fail_under=70, source=pytest_bdd)
- `pyproject.toml` — pytest markers, test_group_paths, ruff rules, dependency groups
- `tests/cases/e2e/e2e/test_e2e.py` — current E2E loader structure, filter logic, per-file scenario bindings
- `tests/cases/e2e/conftest.py` — 471 lines of step definitions, existing test patterns
- Source module coverage report (pytest-cov term-missing output) — per-module line counts and coverage percentages
- `src/pytest_bdd/` pragma audit (38 instances found via grep) — each instance catalogued
- `tests/cases/` directory listing — confirmed all test files under cases/, 25 files need @pytest.mark.unit

### Secondary (MEDIUM confidence)
- `.planning/codebase/TESTING.md` — project testing patterns and conventions
- `.planning/codebase/CONVENTIONS.md` — coding conventions (attrs, imports, naming)
- `.planning/codebase/STRUCTURE.md` — directory layout and plugin structure
- Phase 8 audit plan (08-01-PLAN.md) — gap list and feature file inventory reference
- Phase 12 CONTEXT.md — D-18 per-file E2E module binding rule
- `DEVELOPMENT.rst` — project development guidelines

### Tertiary (LOW confidence)
- pytest-cov documentation: usage pattern for per-module coverage thresholds — assumed from training data, not independently verified
- Cucumber Messages protocol: step definition patterns — assumed from project's own implementation

## Assumptions Log

> All claims tagged `[ASSUMED]` in this research.

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | 27 BDD failures are distributed across StepNotFound (~10-15), ImportError (~5-8), AssertionError (~5-8), and infrastructure (~3-5) categories | BDD Failure Landscape | Wrong distribution changes wave ordering and task allocation |
| A2 | Per-module coverage threshold of 70% applies to line+branch coverage as measured by pytest-cov with `--cov-branch` | Coverage Gap Analysis | If project intends line-only coverage, branch coverage targets are stricter than needed |
| A3 | The 25 files lacking `@pytest.mark.unit` in `tests/cases/unit/` include args/ subdirectory files that SHOULD have unit markers per D-11 | Coverage Gap Analysis | If args/ files are intentionally marker-free (test_group_paths covers them), D-11 scope is smaller |
| A4 | `scenario_locator.py` callback methods (lines 57, 66, 70, 74, 90) can remain under `# pragma: no cover` as they're exercised via integration/E2E tests | Pragma Audit Summary | If tests are expected to cover these directly, the pragmas are unjustified gaps |
| A5 | Model module tests are partially complete — D-12 scope is to augment existing test files with coverage for uncovered paths, not write new files from scratch | Coverage Gap Analysis | If D-12 expects new files, test allocation plan is under-scoped |

**If this table is empty:** All claims in this research were verified or cited — no user confirmation needed.

## Open Questions (RESOLVED)

1. **Scope of "27 BDD failures"** — RESOLVED
   - What we know: 61 E2E scenarios are excluded by tag-based filtering. The 27 count likely comes from a previous run with different exclusions.
   - What's unclear: Are the 27 failures all within the currently skipped scenarios, or are some in the passing set? Do the 27 include infrastructure-dependent tests (@docker, @xdist)?
   - **Resolution:** Plan 14-01 Task 2 runs the full E2E suite without tag exclusions to capture the actual failure count, categorized by error type. If count differs significantly from 27, task allocation adjusts dynamically based on the triage report. Infrastructure-dependent failures are identified and kept excluded.

2. **Per-module coverage threshold enforcement mechanism** — RESOLVED
   - What we know: `.coveragerc` has `fail_under = 70` which gates TOTAL aggregate coverage. No per-module enforcement exists.
   - What's unclear: Should per-module checking be a CI script, a pytest plugin, or manual review? What action on violation?
   - **Resolution:** Use `coverage json` post-processing in Plan 14-04 Task 1 (full suite verification). Parse `coverage.json` to extract per-file percentages, flag any non-exempt module below 70%. Hard enforcement: plan does not pass verification until all non-exempt modules reach ≥70%. The `.coveragerc` `fail_under = 70` handles the aggregate gate; per-module checking is scripted as part of 14-04 Task 1 action steps.

3. **25 files needing `@pytest.mark.unit` — intentional or oversight?** — RESOLVED
   - What we know: 25 test files under `tests/cases/unit/` lack `@pytest.mark.unit`. The `test_group_paths` config in pyproject.toml uses directory globs (`tests/cases/unit/** = unit`) which may provide automatic grouping independent of markers.
   - What's unclear: Are explicit markers required per Phase 12 D-04/D-06 conventions, or does test_group_paths suffice?
   - **Resolution:** `test_group_paths` provides automatic grouping via directory globs, so markers are not strictly required for group assignment. However, explicit `@pytest.mark.unit` markers are added per D-11 for convention compliance, human readability, and marker-based test selection (`pytest -m unit`). Plan 14-02 Task 3 adds markers to all unit test files.

4. **E2E module split — keep or remove test_e2e.py?** — RESOLVED
   - What we know: D-10 says "Replaces the current `tests/e2e/test_e2e.py` with per-file modules." The file also contains 3 non-scenario tests (messages_fixed matrix validation).
   - What's unclear: Should the 3 non-scenario tests move to their own file, or stay in a retained non-scenario module?
   - **Resolution:** Split into: (a) `test_messages_fixed.py` for the 3 non-scenario tests, (b) ~47 `test_feature_NNN.py` modules, one per feature file. Delete the original `test_e2e.py` after migration. This is implemented in Plan 14-03 Task 2. The 3 non-scenario tests are extracted first, then per-file modules are created, then original file is stripped of scenarios() calls (kept only as module stub, to be deleted after verification).

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python 3.14 | All test execution | ✓ | 3.14.0 | — |
| pytest | Test runner | ✓ | >=7.0.0 (installed) | — |
| pytest-cov | Coverage measurement | ✓ | >=7.1.0 (installed) | — |
| pytest-order | Test group ordering | ✓ | 1.4.0 (installed) | — |
| pytest-xdist | E2E distributed tests | ✓ | 3.8.0 (installed) | — |
| pytest-httpserver | E2E HTTP feature tests | ✓ | 1.1.5 (installed) | — |
| GitPython | Message/contract tests | ✓ | installed | — |
| PyYAML | StructBDD tests | ✓ | 6.0.3 (installed) | — |
| PyHamcrest | Allure tests | ✓ | 2.1.0 (installed) | — |
| deepdiff | Contract tests | ✓ | installed | — |
| pypandoc | Doc generation tests | ✓ | installed | — |
| Docker daemon | Docker-backed E2E tests | ✗ | — | Skip via @docker tag exclusion (D-06 triage) |
| jq | Message validation tests | ✗ (Windows) | — | Skip jq-dependent tests on Windows |
| Go compiler | Go parser build | — | — | Not needed; testing-only phase |

**Missing dependencies with no fallback:**
- jq — not available on Windows platform. Tests that depend on jq for JSON validation already skip on Windows. No new jq-dependent tests should be written.

**Missing dependencies with fallback:**
- Docker daemon — E2E tests tagged @docker are already excluded by `_EXCLUDED_TAGS` filter. BDD triage (D-06) should keep these excluded rather than trying to run them.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all tools already installed and configured; no new dependencies
- Architecture: HIGH — existing patterns (testdir, direct instantiation, per-file scenarios) are well-documented in codebase
- Pitfalls: HIGH — based on direct investigation of current test state and coverage reports
- BDD failure landscape: MEDIUM — failure categories extrapolated from skip patterns and CONTEXT.md hints; actual distribution requires Wave 0 triage run
- Pragma audit: HIGH — 38 instances catalogued from source grep; justification assessment is per-instance

**Research date:** 2026-05-20
**Valid until:** 2026-06-19 (30 days — stable testing domain)
