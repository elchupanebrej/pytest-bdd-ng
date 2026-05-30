# Tasks: Async Feature File Collection

**Feature**: 022-async-feature-collection
**Branch**: `022-async-feature-collection`
**Date**: 2026-05-11
**Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md)

## Implementation Strategy

**Approach**: TDD — write tests first per acceptance scenario, then implement. Each phase produces a working, testable increment. US1+US2 are merged as they share the core pipeline (US1 = build it, US2 = verify correctness).

**MVP Scope**: Phases 1-3 (Setup + Foundational + US1/US2). Delivers concurrency + correctness. Error handling (US3) and order verification (US4) can follow.

## Dependencies

```
Phase 1 (Setup)
  └→ Phase 2 (Foundational)
       └→ Phase 3 (US1+US2: Core Pipeline + Correctness) [P1]
            ├→ Phase 4 (US3: Error Handling) [P2]
            └→ Phase 5 (US4: Deterministic Order) [P2]
                 └→ Phase 6 (Polish)
```

US3 and US4 are independent of each other — can be implemented in parallel.

## Parallel Execution Examples

- **Phase 2**: T003 (batch parser class) and T004 (parse worker) — different functions, same file
- **Phase 3**: T007 (state machine tests) and T008 (worker tests) — different test areas, same file
- **Phase 4 + 5**: Entire US3 and US4 phases can run in parallel (different concerns, shared base from Phase 3)

---

## Phase 1: Setup

**Goal**: Project scaffolding and dependency declaration.

- [x] T001 Add `aiofiles` as optional dependency in `pyproject.toml` under `[project.optional-dependencies]` with key `async` and package `aiofiles`
- [x] T002 Create `src/pytest_bdd/collector_batch.py` with module docstring, imports (`attrs`, `Path`, `asyncio`, `multiprocessing`, `logging`), and optional aiofiles import guard

---

## Phase 2: Foundational

**Goal**: Build the `FeatureBatchParser` class and parse worker function. These are prerequisites for all user stories.

- [x] T003 Implement `FeatureBatchParser` class in `src/pytest_bdd/collector_batch.py` — `attrs`-decorated, extends `StashBound` with `STASH_KEY = "_pytest_bdd_batch_parser"`. Fields: `_pending` (`list[Path]`), `_cache` (`dict[Path, GherkinDocument]`), `_flushed` (`bool`). Methods: `register(path) -> int` (append to pending, return new count, raise `RuntimeError` if flushed), `has_pending() -> bool`, `flush() -> int` (skeleton — returns 0, sets `_flushed=True`), `get(path) -> GherkinDocument | None` (return cache entry or None, raise `RuntimeError` if not flushed).
- [x] T004 Implement `_parse_feature_file(path: Path, content: bytes) -> tuple[Path, GherkinDocument]` in `src/pytest_bdd/collector_batch.py` — module-level free function. Decode content as UTF-8, parse with `gherkin` `Parser`, return `(path, document)`. Raise on parse failure.
- [x] T005 [P] Wire `FeatureBatchParser` initialization into `src/pytest_bdd/plugin/scenario_test_collector/entrypoint.py` — add `pytest_configure` hookimpl (or extend existing one) to call `FeatureBatchParser().initialize_in_stash(config.stash)`.
- [x] T006 [P] Wire path registration into `src/pytest_bdd/plugin/scenario_test_collector/plugin.py` — in `_pytest_collect_file()`, after confirming file is collectible but before returning the collector, call `FeatureBatchParser.from_stash(config.stash).register(Path(file_path))`.

---

## Phase 3: US1+US2 — Core Batching Pipeline & Correctness (P1)

**User Story 1**: Faster test collection via concurrent reads + parallel parse.
**User Story 2**: Identical test items between batched and synchronous paths.
**Independent Test (US1)**: `pytest --collect-only` timing on 10+ feature files shows wall-clock improvement.
**Independent Test (US2)**: `pytest --collect-only` output diff between batched and sync paths is empty.

### Tests (US1)

- [x] T007 [P] [US1] Write unit tests for `FeatureBatchParser` state machine in `tests/unit/test_collector_batch.py` — test `register()` appends and returns count, `register()` after flush raises `RuntimeError`, `has_pending()` before/after flush, `get()` before flush raises, `get()` after flush returns cached doc, empty pending → flush returns 0, single file → flush returns 1, multiple files → flush returns N.
- [x] T008 [P] [US1] Write unit test for `_parse_feature_file` in `tests/unit/test_collector_batch.py` — test valid Gherkin content returns `(path, GherkinDocument)`, malformed Gherkin raises exception, UTF-8 decode error raises.

### Implementation (US1)

- [x] T009 [US1] Implement async file reads in `FeatureBatchParser.flush()` in `src/pytest_bdd/collector_batch.py` — use `asyncio.run()` with `asyncio.gather(*[aiofiles.open(p, "rb") for p in pending])` (read all files concurrently). Fallback: if `aiofiles` not available, read synchronously with `Path.read_bytes()`. Return list of `(path, content_bytes)` tuples. Failed reads → log WARNING, exclude from parse batch.
- [x] T010 [US1] Implement multiprocessing parse in `FeatureBatchParser.flush()` in `src/pytest_bdd/collector_batch.py` — use `multiprocessing.Pool().starmap(_parse_feature_file, paths_and_contents)` to parse all files in parallel. Catch individual worker exceptions per-result. Populate `_cache` with successful results. Log ERROR for failed parses. Set `_flushed = True`. Return count of successfully parsed files.
- [x] T011 [US1] Override `collect()` in `FeatureFileModule` in `src/pytest_bdd/collector.py` — add `collect()` method that calls `FeatureBatchParser.find_in_stash(self.config.stash).flush()` if has pending, then delegates to `super().collect()`. Use `find_in_stash` (optional lookup) to avoid crash when batch parser not initialized.
- [x] T012 [US1] Implement cache injection in `FeatureFileModule._build_test_module()` in `src/pytest_bdd/collector.py` — fetch batch parser from stash, get cached doc for `self.get_path()`. If doc is `None` (parse failed or not registered), do not pass cache to `scenarios()` (fall back to normal file read). If doc exists, pass as `cache={self.get_path(): doc}` dict to `scenarios()` call.

### Tests (US2)

- [ ] T013 [US2] Write regression test in `tests/hook/test_batch_collection_regression.py` — create a `testdir` project with .feature files containing scenarios, outlines, and tags, run `pytest --collect-only` with batching enabled, compare output (item count, names, markers) against synchronous path using pytester's `testdir.runpytest()` and `testdir.runpytest("-p", "no:pytest_bdd_batch_parser")` (or equivalent disable mechanism).

### Cache Integration

- [x] T014 [US2] Add optional `cache` parameter to `FileScenarioLocator.__init__()` via stash lookup in `src/pytest_bdd/scenario_locator.py` — parameter `cache: dict[Path, GherkinDocument] | None = None`. Store as `self._cache`.
- [x] T015 [US2] Implement cache path in `FileScenarioLocator.resolve_features()` via stash lookup — in the loop over resolved paths, check `self._cache` first: if path is in cache, use cached `GherkinDocument`; otherwise read + parse as before. All downstream pipeline (hook observers, pickle generation) unchanged.

### Integration

- [ ] T016 [US1] Write integration test in `tests/feature/test_batch_collection.py` — create a `testdir` project with 3+ real `.feature` files and step definitions, run `pytest` with batching, verify all tests pass and collect correctly. Use pytester patterns from `tests/feature/test_autoload.py`.

---

## Phase 4: US3 — Graceful Error Handling (P2)

**User Story 3**: Single broken file does not block batch; errors are surfaced per-file.
**Independent Test**: 3 valid + 1 malformed .feature file → valid files collected, malformed errors surfaced.

### Tests

- [ ] T017 [US3] Write error handling tests in `tests/unit/test_collector_batch.py` — test that `flush()` with one unreadable file (mock file system or use temp file with permission issue) logs warning and excludes that file, test that malformed Gherkin content captured per-worker with ERROR log. Test that `flush()` with all files failing still completes (returns 0).

### Implementation

- [ ] T018 [US3] Implement per-file error isolation in `FeatureBatchParser.flush()` in `src/pytest_bdd/collector_batch.py` — ensure `asyncio.gather(return_exceptions=True)` catches `OSError` per file. Ensure `Pool.starmap` exceptions are caught with try/except per result item. Failed files excluded from `_cache`.
- [ ] T019 [US3] Implement multiprocessing fallback in `FeatureBatchParser.flush()` in `src/pytest_bdd/collector_batch.py` — wrap `Pool.starmap` in try/except for `pickle.PickleError` and other serialization errors. On failure, fall back to synchronous single-file parse in main process (call `_parse_feature_file` directly for each path).

### Integration

- [ ] T020 [US3] Write error handling integration test in `tests/feature/test_batch_collection.py` — `testdir` project with 3 valid + 1 malformed `.feature` file, run `pytest`, assert that tests from 3 valid files are collected and malformed file produces a parse error message, not a crash.

---

## Phase 5: US4 — Deterministic Feature Order (P2)

**User Story 4**: Feature file registration order is deterministic and unchanged from synchronous path.
**Independent Test**: Two consecutive `pytest --collect-only` runs produce identical item order.

### Tests

- [ ] T021 [US4] Write determinism test in `tests/hook/test_batch_collection_regression.py` — run `pytest --collect-only` twice on the same `testdir` project with batching, assert that the order of collected feature items is byte-identical between runs. Also verify that registration order in `_pytest_collect_file` matches the synchronous glob order (by mocking or inspecting `_pending` list order).

### Validation (no new implementation)

- [ ] T022 [US4] Verify globbing is unchanged — confirm in `src/pytest_bdd/scenario_locator.py` that `FileScenarioLocator._resolved_feature_paths` (glob) runs synchronously and is not modified by the batch parser. The batch parser only takes over after glob complete, during `collect()`.

---

## Phase 6: Polish

**Goal**: Finalize dependency declarations, lint, and full test suite verification.

- [ ] T023 Run `ruff check` and `ruff format` on all modified/new files (`collector_batch.py`, `collector.py`, `plugin.py`, `scenario_locator.py`, `entrypoint.py`). Fix any violations.
- [ ] T024 Run `mypy` on new module `src/pytest_bdd/collector_batch.py`. Fix any type errors.
- [ ] T025 Run full test suite: `uvx --with tox-uv tox -l` or `uv run python -m pytest tests/ -q`. Verify no regressions in existing tests.
- [ ] T026 Run pre-commit on all files: `uvx pre-commit run --all-files`. Fix any failures.

---

## Summary

| Phase | Story | Tasks | Test Files | Source Files |
|-------|-------|-------|------------|--------------|
| 1: Setup | — | T001-T002 | — | `collector_batch.py`, `pyproject.toml` |
| 2: Foundational | — | T003-T006 | — | `collector_batch.py`, `entrypoint.py`, `plugin.py` |
| 3: Core + Correctness | US1+US2 (P1) | T007-T016 | `test_collector_batch.py`, `test_batch_collection.py`, `test_batch_collection_regression.py` | `collector_batch.py`, `collector.py`, `scenario_locator.py` |
| 4: Error Handling | US3 (P2) | T017-T020 | `test_collector_batch.py`, `test_batch_collection.py` | `collector_batch.py` |
| 5: Deterministic Order | US4 (P2) | T021-T022 | `test_batch_collection_regression.py` | (validation only) |
| 6: Polish | — | T023-T026 | — | all |

**Total**: 26 tasks. **MVP**: Phases 1-3 (16 tasks). **Parallel opportunities**: Phase 2 (T003+T004), Phase 3 tests (T007+T008), Phase 4+5 (entire phases).
