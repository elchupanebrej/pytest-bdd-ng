# Contract: FeatureBatchParser Public API

**Feature**: 022-async-feature-collection
**Version**: 1.0

## Interface Summary

`FeatureBatchParser` provides a lazy-batched file read + parse pipeline. Paths are accumulated during pytest directory walk and processed concurrently on first access.

## Methods

### `register(path: Path) -> None`

Register a feature file path for deferred processing.

- **Preconditions**: Flush has not been called yet.
- **Postconditions**: `path` is appended to internal pending list.
- **Errors**: `RuntimeError` if flush has already been called.
- **Thread safety**: Not required (collection is single-threaded).

### `flush() -> None`

Execute the concurrent read + parallel parse pipeline for all pending paths.

- **Preconditions**: None (idempotent).
- **Postconditions**: All pending paths are read and parsed. Results cached. Pending list cleared. `_flushed` set to `True`.
- **Behavior when no pending paths**: No-op.
- **Behavior when aiofiles unavailable**: Synchronous fallback reads using `Path.read_bytes()`.
- **Error handling**: Individual file read failures captured via `asyncio.gather(return_exceptions=True)` and logged at WARNING. Individual parse failures captured per-worker via exception handling in `Pool.starmap` and logged at ERROR. Failed files excluded from cache; `get()` returns nothing for them.

### `get(path: Path) -> GherkinDocument`

Retrieve a parsed Gherkin document from cache.

- **Preconditions**: `flush()` must have been called.
- **Postconditions**: Returns parsed `GherkinDocument` for the path.
- **Errors**: `RuntimeError` if flush has not been called. Returns `None` if path was not registered or failed during flush.
- **Thread safety**: Not required (collection is single-threaded).

### `has_pending() -> bool`

Check if there are unprocessed paths.

- **Returns**: `True` if pending list is non-empty and flush has not been called.

## Lifecycle

```python
# pytest_configure
parser = FeatureBatchParser()
parser.initialize_in_stash(config.stash)

# pytest_collect_file (per file)
parser = FeatureBatchParser.from_stash(config.stash)
parser.register(Path(file_path))

# FeatureFileModule.collect (first call triggers flush)
parser = FeatureBatchParser.find_in_stash(config.stash)
if parser and parser.has_pending():
    parser.flush()
doc = parser.get(self.path)

# All subsequent collect() calls
doc = parser.get(self.path)  # cache hit
```
