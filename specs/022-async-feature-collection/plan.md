# Implementation Plan: Async Feature File Collection

**Branch**: `022-async-feature-collection` | **Date**: 2026-05-11 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/022-async-feature-collection/spec.md`

## Summary

Reduce pytest collection latency for projects with many `.feature` files by replacing serial file read + Gherkin parse with a lazy-batched pipeline: file paths are accumulated during synchronous directory walk, then flushed concurrently via `asyncio` (file I/O) + `multiprocessing` (CPU-bound parsing) into an in-memory cache on first access. Existing deterministic globbing, marker application, and test item generation are unchanged.

## Technical Context

**Language/Version**: Python 3.10–3.14
**Primary Dependencies**: `aiofiles` (new optional), `gherkin-official` (existing), `pytest >= 7` (existing), `attrs` (existing), `multiprocessing` (stdlib), `asyncio` (stdlib)
**Storage**: In-memory dict `{Path: GherkinDocument}` in `pytest.config.stash`; no persistent storage
**Testing**: pytest + pytester (existing `testdir` patterns from `tests/feature/test_autoload.py`); `uv run python -m pytest tests/...`
**Target Platform**: All platforms supported by pytest (Linux, macOS, Windows)
**Project Type**: Library (pytest plugin)
**Performance Goals**: Measurable wall-clock reduction for N >= 10 feature files; zero overhead for N = 1
**Constraints**: Backward compatible (no CLI/ini changes); synchronous fallback when `aiofiles` not installed; deterministic feature order preserved
**Scale/Scope**: Suites with 10–1000+ feature files

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Rationale |
|-----------|--------|-----------|
| I. Pure BDD Integration | PASS | Feature file semantics, markers, and test item generation unchanged. Same Gherkin documents produced. |
| II. Realistic Runtime Evidence | PASS | Cache is internal state in `config.stash`. No synthetic probe payloads or test-only substitutions. Reporter pipeline unaffected. |
| III. Explicit Returns & Determinism | PASS | `flush()` and `get()` use explicit returns. Glob order preserved. Cache keyed by `Path` with deterministic lookup. |
| IV. Broad Compatibility | PASS | `multiprocessing` and `asyncio` from stdlib; `aiofiles` guarded by optional import. Python 3.10+ supported. |
| V. Quality & Formatting Discipline | PASS | New module follows `ruff` / `pre-commit` / `mypy` rules. All docs in English. |

**Gate result**: All pass. No violations.

### Post-Design Re-check (Phase 1 complete)

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Pure BDD Integration | PASS | `FileScenarioLocator` cache integration uses same Gherkin document format. No feature semantics changed. |
| II. Realistic Runtime Evidence | PASS | Batch parser cache is internal stash state. No synthetic messages emitted. |
| III. Explicit Returns & Determinism | PASS | `flush()` returns `int` (files processed). `get()` returns `GherkinDocument`. `register()` returns `int` (pending count). `_parse_feature_file()` returns `tuple[Path, GherkinDocument]`. No bare `None` returns. |
| IV. Broad Compatibility | PASS | `multiprocessing` and `asyncio` stdlib ensure 3.10+ compat. `aiofiles` guarded by `try/except ImportError`. |
| V. Quality & Formatting Discipline | PASS | All new code in `collector_batch.py`, formatted by `ruff`. Contracts and docs in English. |

**Post-design gate result**: All pass. No violations.

## Agentic Implementation Strategy

**Superpowers**:
- `test-driven-development`: Write tests first per acceptance scenario, then implement
- `systematic-debugging`: For any test failures during implementation
- `verification-before-completion`: Run lint + tests before claiming done

**Subagent Dispatch**:
- Independent tasks (unit tests for `FeatureBatchParser`, integration tests for `FeatureFileCollector`, type stubs) can be dispatched in parallel
- Each subagent gets precise TDD context: spec section + acceptance scenario to implement
- Final integration verification runs sequentially after all subagent work

## Project Structure

### Documentation (this feature)

```text
specs/022-async-feature-collection/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (/speckit.tasks)
```

### Source Code (repository root)

```text
src/pytest_bdd/
├── collector_batch.py       # NEW: FeatureBatchParser + parse worker function
├── collector.py             # MODIFY: FeatureFileCollector.collect() — integrate batch parser
└── plugin/
    └── scenario_test_collector/
        └── plugin.py        # MODIFY: _pytest_collect_file() — register paths

tests/
├── unit/
│   └── test_collector_batch.py    # NEW: Unit tests for FeatureBatchParser
├── feature/
│   └── test_batch_collection.py   # NEW: Integration tests with real .feature files
└── hook/
    └── test_batch_collection_regression.py  # NEW: Regression — identical output vs sync path
```

**Structure Decision**: Single-project layout. New module `collector_batch.py` encapsulates batch logic. Existing `collector.py` and plugin entry point receive minimal integration changes.

## Complexity Tracking

> No constitution violations. Table omitted.
