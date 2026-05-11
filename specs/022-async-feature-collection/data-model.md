# Data Model: Async Feature File Collection

**Feature**: 022-async-feature-collection
**Date**: 2026-05-11

## Entities

### FeatureBatchParser

Session-scoped singleton. Accumulates file paths during collection and flushes them through a concurrent read + parallel parse pipeline.

| Field | Type | Description |
|-------|------|-------------|
| `_pending` | `list[Path]` | File paths accumulated since last flush |
| `_cache` | `dict[Path, GherkinDocument]` | Parsed Gherkin documents, keyed by file path |
| `_flushed` | `bool` | Whether `flush()` has been called (prevents re-entrant flush and post-flush registration) |

**Stash key**: `_pytest_bdd_batch_parser`
**Lifecycle**: Created in `pytest_configure`, populated during directory walk, flushed on first `collect()`, consumed via `get()` for remainder of session.

### State Transitions

```
[Created] → register(path)* → [Pending]
                                  |
                              flush()
                                  |
                                  v
                             [Flushed + Cached]
                                  |
                              get(path)* → cached doc
```

- `register()`: valid only in `[Created]` or `[Pending]` state
- `flush()`: idempotent; if already `[Flushed + Cached]`, no-op
- `get()`: valid only after flush; raises if called before
- Post-flush `register()`: raises `RuntimeError`

### Parse Worker Contract

```python
def _parse_feature_file(path: Path, content: bytes) -> tuple[Path, GherkinDocument]:
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `path` | `Path` | File path (for error attribution) |
| `content` | `bytes` | Raw file content (pickled from main process) |
| **Returns** | `tuple[Path, GherkinDocument]` | Path and parsed Gherkin document |

**Design constraints**:
- Must be a module-level function (picklable by `multiprocessing`)
- Must not capture any class or instance state
- Parse errors propagate as exceptions (caught by `Pool.starmap`)

### Cache Entry

| Field | Type | Description |
|-------|------|-------------|
| key | `Path` | Absolute path to `.feature` file |
| value | `GherkinDocument` | Parsed `cucumber_messages.GherkinDocument` |

### Integration with Existing Model

```
FeatureFileModule.collect()
  → FeatureBatchParser.flush()          [NEW]
  → FeatureBatchParser.get(path)        [NEW — injects cached doc]
  → _getobj()
    → _build_test_module()
      → scenarios(...)
        → FileScenarioLocator(cache={path: doc})  [MODIFIED — accepts cache]
          → resolve_features()
            → [skips file read + parse if in cache]
            → yield (GherkinDocument, Pickle, Source)
```

**FileScenarioLocator change**: Accepts optional `cache: dict[Path, GherkinDocument] | None` parameter. When present and path is in cache, uses cached document instead of reading + parsing the file.
