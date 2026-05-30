# Contract: Parse Worker Function

**Feature**: 022-async-feature-collection
**Version**: 1.0

## Signature

```python
def _parse_feature_file(path: Path, content: bytes) -> tuple[Path, GherkinDocument]:
```

## Semantics

1. Receives a file path (for error attribution) and raw bytes content.
2. Decodes content as UTF-8.
3. Parses content using `gherkin-official` parser.
4. Returns `(path, GherkinDocument)` on success.
5. Raises exception on parse failure (propagated to `Pool.starmap`).

## Design Constraints

| Constraint | Rationale |
|------------|-----------|
| Must be a module-level free function | `multiprocessing.Pool` requires picklable callables |
| Must not capture class/instance state | Pickle serialization fails if closure references non-global state |
| Must not perform file I/O | Content is passed as argument; file I/O happens in main process via aiofiles |
| Must decode content as UTF-8 | Gherkin files are always UTF-8 encoded |
| Must use existing parser | `gherkin-official` `Parser.parse()` — no new parser implementation |

## Error Contract

- **Gherkin parse errors**: `gherkin.ParserError` or `CompositeParserException` — propagates to `Pool.starmap` as exception, caught per-worker.
- **UTF-8 decode errors**: `UnicodeDecodeError` — treated as parse failure.

## Multiprocessing Integration

```python
with Pool() as pool:
    results = pool.starmap(_parse_feature_file, [(path, content) for path, content in zip(paths, contents)])
```

- `starmap` blocks until all workers complete.
- Individual worker exceptions are captured in results.
- Pool lifetime: created and destroyed within `flush()`; no persistent pool.

## Fallback (no aiofiles)

When `aiofiles` is unavailable, files are read synchronously in the main process:

```python
contents = [path.read_bytes() for path in pending]  # sequential fallback
```

Parse still uses `multiprocessing.Pool` if available.
