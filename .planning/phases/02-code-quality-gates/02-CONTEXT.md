# Phase 02: Code Quality Gates - Context

**Gathered:** 2026-05-12
**Status:** Ready for planning

## Phase Boundary

Eliminate `return None` antipatterns (~95 instances) and bare `except Exception:` handlers (~9 instances) in non-hook code. Introduce `returns` library (`Maybe[T]` / `Result[T, E]`) as the canonical pattern. Add CI lint gate to prevent regression. Enforce collection-time error for scenarios with zero matched step definitions.

## Implementation Decisions

### Sentinel/Exception Strategy — `returns` Library
- **D-01:** Adopt `returns` library (dry-python/returns) — `Maybe[T]` replaces `T | None`, `Result[T, E]` replaces try/except error flows
- **D-02:** Full migration — convert ALL ~95 `return None` instances in non-hook code to `Maybe` or `Result`
- **D-03:** Pytest hooks exempt — hooks return `None` by framework contract (AGENTS.md: "Outside pytest hook implementations, returning None is an antipattern")
- **D-04:** Per-module `StrEnum` for `Result.failure()` error values — each module defines its own failure reasons (e.g., `StashFailure`, `ScenarioRunFailure`)
- **D-05:** Per-file imports — each file imports `Maybe, Some, Nothing` / `Result, Success, Failure` directly from `returns`
- **D-06:** Canonical patterns:
  - **Lookups** (`find_in_stash`, `from_stash`, `feature_locator`) → `Maybe[T]` — `Some(value)` on hit, `Nothing` on miss
  - **Operations that can fail** (`require`, `initialize`, `validate`) → `Result[T, FailureEnum]` — `Success(value)` on success, `Failure(reason)` on error
  - **Chains** (nested optional lookups, pipeline) → `Maybe` with `bind_optional` / `Result` with `bind`
  - **Extracting back to Optional** → `.value_or(None)` at public API boundaries where callers expect `Optional`

### Exception Specificity
- **D-07:** Silent swallowers → add `logger.warning(exc_info=True)`:
  - `collector.py:107` — parse failures during collection
  - `code_generator/plugin.py:116` — formatting failures
  - `hook_catalog_runtime.py:160` — catalog read failures
- **D-08:** `parsers.py:652-672` — convert 4 `except Exception` chain to `Result` (override roadmap parsers freeze)
- **D-09:** `transport_runtime.py:88` — already correctly logs with `logger.exception()` — no change needed
- **D-10:** Remaining bare excepts (`entrypoint.py:266`, `message_transport.py:338`, `__init__.py:42`, `url.py:24`) → add logging or convert to specific exception types per site audit

### CI Enforcement
- **D-11:** Custom ruff AST-based lint rule checking: (a) `return None` in non-hook functions, (b) bare `except Exception:` without `# noqa: BLE001` + logging
- **D-12:** Hard block — zero tolerance. CI fails on any remaining violation after Phase 2 completion. No baseline/transitional period.

### Zero-Matches UX
- **D-13:** Collection-time `pytest.UsageError` listing unmatched steps with `file:line` references
- **D-14:** Escape hatch: `--allow-empty-scenarios` CLI flag or `bdd_allow_empty_scenarios = true` ini option to skip instead of error
- **D-15:** Direct enforcement — no transitional deprecation period (consistent with D-10 precedent from Phase 1)

### Override Decisions
- **D-16:** `parsers.py` freeze (roadmap constraint) overridden — `Result` conversion in parsers.py is explicitly authorized for this phase

### the agent's Discretion
- Exact `StrEnum` member names per module
- Ruff rule implementation details (AST node types, hook detection heuristic)
- Error message formatting for zero-matches UsageError
- Migration ordering — which files/patterns to convert first

## Canonical References

### Requirements and Roadmap
- `.planning/ROADMAP.md` — Phase 2: Code Quality Gates (goal, success criteria, depends on Phase 1)
- `.planning/REQUIREMENTS.md` — STAB-02 (return None elimination), STAB-03 (bare except replacement)

### Library Dependency
- `https://pypi.org/project/returns/` — `returns` library by dry-python (`Maybe`, `Result` containers)

### Existing Code — High-Impact Files
- `src/pytest_bdd/model/scenario_run.py` — 11 return None instances (highest density)
- `src/pytest_bdd/feature_locator.py` — 5 return None instances
- `src/pytest_bdd/model/stash_access.py` — 1 return None (find_in_stash pattern)
- `src/pytest_bdd/model/message_validation.py` — 5 return None instances
- `src/pytest_bdd/steps.py` — 1 return None

### Existing Code — Bare Except Sites
- `src/pytest_bdd/parsers.py` §lines 648-672 — 4 intentional except Exception (parser chain)
- `src/pytest_bdd/collector.py` §line 107 — parse failure swallower
- `src/pytest_bdd/plugin/code_generator/plugin.py` §line 116 — formatting failure swallower
- `src/pytest_bdd/plugin/gherkin_message_reporter/hook_catalog_runtime.py` §line 160 — catalog read swallower
- `src/pytest_bdd/plugin/gherkin_message_reporter/entrypoint.py` §line 266 — bare except
- `src/pytest_bdd/plugin/gherkin_message_reporter/transport_runtime.py` §line 88 — correctly logged (no change)
- `src/pytest_bdd/util/message_transport.py` §line 338 — bare except

### Prior Decisions Carried Forward
- `.planning/phases/01-foundation-cleanup/01-CONTEXT.md` — D-10 (direct removal, no transitional period)

### Codebase Concerns
- `.planning/codebase/CONCERNS.md` §"return None Antipattern" — 96 instances across source
- `.planning/codebase/CONCERNS.md` §"Broad Exception Catchers" — 22 instances (some now resolved)

## Existing Code Insights

### Reusable Assets
- `_MISSING = object()` in `src/pytest_bdd/util/toolz_extra.py` — existing sentinel pattern (will be replaced by `Nothing`)
- `StashBound.stash_missing_message()` in `src/pytest_bdd/model/stash_access.py` — existing string-based error reporting pattern

### Established Patterns
- `StashBound` pattern — all config stash access goes through `from_stash()` / `find_in_stash()` / `initialize_in_stash()` class methods
- `attrs` over `dataclass` — all new/modified data classes must use `attrs`
- Plugin entrypoint convention — `class + entrypoint.py + hook.py` structure

### Integration Points
- `pyproject.toml` → adds `returns` dependency in `[project] dependencies`
- `pyproject.toml` → ruff custom lint rule in `[tool.ruff]` or standalone script
- Scenario collection pipeline (`collector.py` → `scenario_test_collector`) → zero-matches check must hook into collection phase
- All 17 pytest plugins may need `Maybe`/`Result` imports

## Deferred Ideas

None — discussion stayed within phase scope.

---

*Phase: 02-code-quality-gates*
*Context gathered: 2026-05-12*
