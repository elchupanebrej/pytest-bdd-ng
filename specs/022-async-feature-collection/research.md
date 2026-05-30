# Research: Async Feature File Collection

**Feature**: 022-async-feature-collection
**Date**: 2026-05-11

## Research Questions & Resolutions

### Q1: Where in the collection lifecycle does `FeatureBatchParser` initialize?

**Decision**: Initialize in `pytest_configure` hook, identical to how `Run` initializes.

**Rationale**: `pytest_configure` fires before any collection, and `config.stash` is available. The `StashBound` pattern (`initialize_in_stash`) provides the same double-init guard used by `Run`. This ensures `FeatureBatchParser` is available before the first `pytest_collect_file` call.

**Alternatives considered**:
- Lazy init on first `register()`: Rejected — would need per-call "is initialized?" checks, adds complexity.
- Init in `pytest_sessionstart`: Rejected — this fires after `pytest_collect_file` in some configurations.

**Implementation**: New entry point in `scenario_test_collector/entrypoint.py`:

```python
@pytest.hookimpl(trylast=True)
def pytest_configure(config: Config) -> None:
    FeatureBatchParser().initialize_in_stash(config.stash)
```

---

### Q2: How does `FeatureFileModule.collect()` integrate with batch parser?

**Decision**: Override `collect()` in `FeatureFileModule` to flush the batch before delegating to `Module.collect()`.

**Rationale**: The first time `collect()` is called on any `FeatureFileModule`, all pending feature files registered during directory walk are flushed at once. Subsequent `collect()` calls on other `FeatureFileModule` instances find the batch already flushed and pull from the cache. This is the lazy-batched approach (Approach C from the design doc).

The call chain is:
```
FeatureFileModule.collect()
  → batch_parser.flush()             # one-shot; idempotent
  → Module.collect()
    → self.obj (property) → _getobj() → _build_test_module() → scenarios(...) → uses scenarios() which internally calls scenario locator pipeline
```

**Alternatives considered**:
- Flush in `pytest_collection_modifyitems`: Rejected — too late; collection already started.
- Flush in `pytest_collect_file` after registering: Rejected — defeats batching (would flush before all files registered).

---

### Q3: Parse worker function design

**Decision**: Module-level free function `_parse_feature_file(path: Path, content: bytes) -> tuple[Path, Exception | GherkinDocument]`.

**Rationale**: Must be picklable by `multiprocessing.Pool`. Free functions (not methods, not lambdas) are always picklable. Returns a tuple so the caller can distinguish which file each result belongs to and handle individual failures.

**Signature**:
```python
def _parse_feature_file(path: Path, content: bytes) -> tuple[Path, GherkinDocument]:
```
- Input: file path (for error messages) and raw bytes content (read by aiofiles, picklable).
- Output: `(Path, GherkinDocument)` on success; raises on parse failure (caught by `Pool.starmap`).
- The `gherkin-official` parser's `Parser.parse()` accepts a string, so content is decoded in the worker.

**Alternatives considered**:
- Pass filename strings and read in worker: Rejected — each worker would re-read the file, negating the I/O concurrency benefit.
- Pass parsed token streams: Rejected — pickle overhead of token tree > pickle overhead of raw bytes.

---

### Q4: Optional `aiofiles` import guard

**Decision**: Lazy import with fallback pattern.

**Rationale**: `aiofiles` is an optional dependency. If not installed, the batch parser silently degrades to synchronous single-file reads. This avoids breaking existing installations.

**Pattern**:
```python
try:
    import aiofiles
    _aiofiles_available = True
except ImportError:
    _aiofiles_available = False
```

In `flush()`: if `_aiofiles_available` is `False`, read files synchronously via `Path.read_bytes()` (the existing fallback path).

**Alternatives considered**:
- Hard dependency: Rejected — user explicitly wants optional.
- Conditional dependency group in `pyproject.toml`: Considered for future UX improvement (e.g., `pip install pytest-bdd[async]`).

---

### Q5: How does batch parser interact with existing scenario locator pipeline?

**Decision**: The batch parser replaces the I/O + parse step in `FileScenarioLocator.resolve_features()`, NOT the entire locator pipeline.

**Rationale**: `FileScenarioLocator.resolve_features()` currently does: glob → read file → parse Gherkin → yield GherkinDocument + Pickle + Source. The batch parser takes over the "read file → parse Gherkin" step. The "glob", "yield GherkinDocument + Pickle + Source", and "observer hook firing" steps remain in the locator.

However, the `FeatureFileModule._build_test_module()` calls `scenarios(...)` which internally instantiates `FileScenarioLocator` and calls `resolve_features()`. The batch parser's cached `GherkinDocument` must be consumable by this pipeline without changing the locator's public interface.

**Resolution**: Two integration options:
1. **Inject cached parse into locator**: Add a `cache` parameter to `FileScenarioLocator` that, when populated, skips file read + parse and uses the cached document.
2. **Short-circuit in `MetaScenarioCollector`** (the mark-based collector): Not applicable — this path is for `@scenario()` decorators, not auto-discovery.

**Chosen**: Option 1 — pass cache to `FileScenarioLocator`. Minimal change to existing code.

---

### Q6: Thread safety of stash during concurrent access

**Decision**: Stash access is single-threaded during collection (pytest's collection phase is single-threaded). No locking needed.

**Rationale**: pytest's `pytest_collect_file` hook and all collector methods execute sequentially in a single thread. The `multiprocessing.Pool` runs workers in separate processes, not threads. The cache is populated synchronously in the main process after `Pool.starmap` returns. No concurrent stash access occurs.

---

### Q7: Test isolation for batch parser

**Decision**: Unit tests mock the I/O layer (file reads) and parse layer (Gherkin parser). Integration tests use real `.feature` files in `testdir`.

**Rationale**: `FeatureBatchParser` has three layers: file I/O, Gherkin parse, cache management. Unit tests mock I/O and parse to test cache logic. Integration tests use `testdir` with real `.feature` files (existing pattern from `tests/feature/test_autoload.py`).

**Pytest configuration**: Tests should not use the batch parser by default (to avoid interfering with other tests). The batch parser should be opt-in via a conftest fixture or a `testdir`-local `conftest.py`.
