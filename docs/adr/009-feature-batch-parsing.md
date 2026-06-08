# ADR-009: Feature Batch Parsing with Async/Multiprocessing

**Status:** Accepted
**Date:** 2026-06-08
**Deciders:** pytest-bdd-ng core team

## Context

Feature file parsing is I/O-bound. In test suites with hundreds of `.feature` files, sequential single-threaded parsing dominates collection time. pytest-bdd-ng's `FeatureFileModule` collector parses each feature file synchronously during `pytest_collect_file`, which serializes all I/O operations behind a single thread.

The existing `collector_batch.py` already uses an async/multiprocessing pattern for batched feature file loading, but the parse worker operates per-file sequentially within each batch. For large suites (>500 feature files), even batched sequential parsing becomes a bottleneck — the initial flush on first `get()` call processes all files before any test begins execution.

## Decision

Adopt **lazy-batched async parsing** via `FeatureBatchParser` using `asyncio` + `multiprocessing`, with the following design:

1. **Lazy parsing, eager collection:** `FeatureFileModule` collects file paths eagerly (unchanged). Parsing is deferred until the first `get()` call on the batch result, at which point all queued files are parsed concurrently using an `asyncio` event loop with `multiprocessing` workers.

2. **Optional `aiofiles` for async I/O:** When `aiofiles` is installed (`pip install pytest-bdd[aio]`), file I/O uses async operations. When unavailable, the worker falls back to synchronous `Path.read_text()` inside the thread pool — no error, just slower.

3. **Single parse worker per process:** Each multiprocessing worker processes one file at a time, using the existing Python parser or Go parser backend (honoring `PYTEST_BDD_GHERKIN_BACKEND`). The concurrent speedup comes from multiple workers, not from per-worker async I/O.

4. **Result aggregation:** `FeatureBatchParser` exposes an async iterator that yields `(path, GherkinDocument)` tuples as files complete, enabling streaming collection (pytest can begin test item creation before all files are parsed).

5. **`FeatureBatchParser` lives in `collector_batch.py`** (existing module), replacing the current `parse_worker` function. The public API remains unchanged: `FeatureFileModule` calls the batch parser, receives results, and creates test items.

## Consequences

### Positive

- **Faster collection:** Concurrent parsing of feature files reduces wall-clock collection time by 2-5× on multi-core machines, proportional to core count and I/O parallelism.
- **Lower memory:** Lazy parsing defers file I/O until needed; results are yielded as they complete rather than buffered in full.
- **Backward compatible:** No change to user-visible API; `scenarios()` and `scenario()` continue to work identically. The async/multiprocessing machinery is internal.
- **Graceful degradation:** When `multiprocessing` is unavailable (e.g., restricted environments), the parser falls back to sequential single-process mode automatically.

### Negative

- **Complexity:** Async + multiprocessing coordination introduces new failure modes (worker crashes, pipe breakage, timeout handling). The existing `_aiofiles_available` flag and `asyncio` scaffolding help contain this.
- **Debugging difficulty:** Tracebacks from multiprocessing workers are less readable than single-process tracebacks. The parse worker must serialize and propagate exceptions cleanly.
- **Startup overhead:** Spawning worker processes adds ~200-500ms of startup latency. For small suites (<50 files), sequential parsing may be faster. The batch parser should have a threshold below which it skips parallelism.

### Neutral

- **Optional dependency:** `aiofiles` remains optional; the parser works without it. Users get the full benefit only with `aiofiles` installed.
- **Go parser compatibility:** Concurrent Go parser usage requires the shared library to be thread-safe. The current cgo bridge uses per-call `ctypes` — verified safe for concurrent access in the Go runtime.
- **`collector_batch.py` preserved:** The existing module is the natural home for this change; no new top-level modules needed.

## References

- `src/pytest_bdd/collector_batch.py` — existing batch parsing infrastructure
- `src/pytest_bdd/collector.py` — `FeatureFileModule` collection integration point
- ADR-005 — Go parser extraction and `_get_parser()` factory pattern
