# Async Feature File Collection — Design

**Date:** 2026-05-11
**Status:** Draft
**Scope:** Feature file read + Gherkin parse executed concurrently (asyncio reads + multiprocessing parse)

## Problem

`FeatureFileCollector` discovers and parses `.feature` files one at a time, synchronously,
during pytest's collection phase. For suites with many feature files, this serial I/O and
CPU-bound parsing adds noticeable collection latency.

## Non-Goals

- Globbing/discovery stays synchronous (preserves deterministic feature order).
- No change to `UrlScenarioLocator` HTTP fetch path (already async).
- No change to `@scenario()` decorator-based collection path.
- No pre-scan enumeration before `pytest_collect_file`.

## Solution: Lazy-Batched Collector (Approach C)

A session-scoped `FeatureBatchParser` singleton (stored in `pytest.config.stash`) accumulates
file paths as discovered, and on first access flushes all pending files through a single
async pipeline: concurrent `aiofiles` reads → `multiprocessing.Pool` parallel Gherkin parsing
→ in-memory cache.

### Architecture

```text
pytest directory walk (sync)            Batch pipeline (async, on flush)
────────────────────────                ────────────────────────────────
pytest_collect_file(f1) → register(f1)
pytest_collect_file(f2) → register(f2)
pytest_collect_file(f3) → register(f3)
                                        |
first FeatureFileCollector.collect()    ↓
                                        asyncio.run(
                                          asyncio.gather(
                                            aiofiles.read(f1),
                                            aiofiles.read(f2),      ← concurrent I/O
                                            aiofiles.read(f3),
                                          )
                                        )
                                        ↓
                                        multiprocessing.Pool.starmap(
                                          parse_feature_content,      ← parallel CPU
                                          [(f1, c1), (f2, c2), (f3, c3)]
                                        )
                                        ↓
                                        cache = {f1: parsed, f2: parsed, f3: parsed}

collect(f1) → cache[f1]
collect(f2) → cache[f2]
collect(f3) → cache[f3]
```

### Components

#### 1. `FeatureBatchParser` (new: `src/pytest_bdd/collector_batch.py`)

Session-scoped singleton. Stash key: `_pytest_bdd_batch_parser`.

```python
@attrs.define
class FeatureBatchParser:
    _pending: list[Path] = attrs.field(factory=list)
    _cache: dict[Path, GherkinDocument] = attrs.field(factory=dict)
    _flushed: bool = False

    stash_key: ClassVar[str] = "_pytest_bdd_batch_parser"

    def register(self, path: Path) -> None: ...

    def flush(self) -> None:
        # 1. asyncio.run(_read_all_pending()) — concurrent aiofiles reads
        # 2. multiprocessing.Pool().starmap(_parse_one, paths_and_contents)
        #    — where _parse_one is a module-level function (picklable)
        # 3. populate _cache, clear _pending, set _flushed = True

    def get(self, path: Path) -> GherkinDocument | None: ...
```

**Design decisions:**

- `_parse_one(path, content)` is a free function (not a method) so it can be pickled
  by `multiprocessing.Pool` without reference to class state.
- `flush()` is idempotent; if `_flushed` is `True`, it is a no-op.
- `get()` returns `None` if path not registered, raises `KeyError` if never flushed.
- Initialized in `pytest_configure` via `FeatureBatchParser.initialize_for_config()`.

#### 2. Modified `FeatureFileCollector` (`collector.py`)

In `FeatureFileCollector.collect()`:
1. Call `batch_parser.flush()` if batch parser has pending files.
2. Call `batch_parser.get(self.path)` to get parsed document.
3. Fall through to existing logic unchanged.

`_getobj()` and `_build_test_module()` remain unchanged — they consume the parsed result.

#### 3. Registration Hook (`scenario_test_collector/plugin.py`)

In `_pytest_collect_file()` or `FeatureFileCollector.build()`:

```python
batch_parser = FeatureBatchParser.from_stash(parent.config.stash)
batch_parser.register(Path(file_path))
```

### Error Handling

| Scenario | Behavior |
|----------|----------|
| File read fails (permissions, missing) | `return_exceptions=True`; failed files excluded from parse batch. Error logged at WARNING. |
| Parse fails (malformed Gherkin) | Load balancing over `Pool` fails; `starmap` catch exception per file. Error stored per-path, get() returns None or raises. |
| Multiprocessing serialization error | Pool timeout kills workers; fall back to sync single-file parse. |
| `get()` called before `flush()` | Raise `RuntimeError("Feature batch not yet flushed")`. |
| Empty pending list at flush | No-op (skip read + parse). |

### Dependencies

| Dependency | Rationale |
|------------|-----------|
| `aiofiles` | Async file I/O compatible with `asyncio.gather`. New dependency. |
| `multiprocessing` | stdlib, CPU-parallel parse without GIL contention. |
| `asyncio` | stdlib, orchestrates concurrent file reads. |
| `gherkin-official` | Existing Gherkin parser. |

### Testing Strategy

1. **Unit — `FeatureBatchParser`**
   - Empty pending → flush no-op.
   - Single file → read + parse + cache hit.
   - Multiple files → all parsed, cache populated, order-independent.
   - Registration after flush → raises `RuntimeError` (session-scoped, single-use per collection).
   - Malformed Gherkin → error captured per-file, not batch failure.
   - Permission-denied file → error captured, others proceed.

2. **Integration — `FeatureFileCollector`**
   - Real `.feature` files in `testdir`-style tests.
   - Verify `collect()` returns correct items after batch flush.
   - Verify no regression in `@scenario()` decorator path.

3. **Edge cases**
   - Single feature file (batch of N=1) — no concurrency overhead penalty.
   - Existing URL-based collection unaffected.
   - `disable_feature_autoload` still skips registration.

### Migration / Backward Compatibility

- Fully backward compatible: same `pytest_collect_file` interface, same markers, same runtime.
- No new CLI flags or ini options required.
- If `aiofiles` not installed → skip batch optimization, fall back to sync path.
  (Optional: `try: import aiofiles` guard.)
