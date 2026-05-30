# Research: Go Gherkin Parser Integration

**Feature**: Go Gherkin Parser (023-go-gherkin-parser)
**Date**: 2026-05-11

## Research Topics

### 1. Go c-shared Library Compilation with setuptools

**Decision**: `go build -buildmode=c-shared -o <output> ./gherkin_go/bridge`

**Rationale**: `-buildmode=c-shared` produces a C-compatible shared library with an auto-generated C header. ctypes can load this directly. The output extension varies by platform:
- Linux: `libgherkin_go.so`
- Windows: `gherkin_go.dll`
- macOS: `libgherkin_go.dylib`

The `sys.platform` check in `_load_library()` maps the correct extension.

**Alternatives considered**:
- `-buildmode=c-archive`: extra compile step to link into CPython extension; more complex, no benefit.
- Manual `gcc` linking: unnecessarily complex; Go toolchain handles it.

### 2. ctypes Memory Management for Go C Strings

**Decision**: Go allocates strings via `C.CString()` and Python must call a Go-exported `FreeCString` after each parse call.

**Rationale**: Go's garbage collector does not manage memory allocated for C export. Strings passed from Go to C must be explicitly freed. The pattern:
1. Go `ParseGherkinDocument(text *C.char) *C.char` — allocates return string with `C.CString(jsonResult)`.
2. Python reads the pointer, copies to Python string via `ctypes.c_char_p.value.decode("utf-8")`.
3. Python calls `FreeCString(ptr)` to release Go-side allocation.

A Python context manager or `__del__` wrapper ensures cleanup even on exceptions.

**Alternatives considered**:
- Caller-allocated buffer: complex API, hard to size correctly.
- Static buffer: not safe for concurrent use.
- Go `String()` with pre-allocated memory: not supported by cgo.

### 3. Multiprocessing Safety with cgo Shared Library

**Decision**: Each worker process loads its own copy of the shared library at import time. No special synchronization needed.

**Rationale**: `multiprocessing.Pool.starmap` spawns worker processes via `fork()` or `spawn()`. Each process imports `_gherkin_go._bridge` independently, calling `ctypes.CDLL()` which loads a fresh library instance. cgo's threading model is per-process, so there is no cross-process state sharing.

**Alternatives considered**:
- Shared memory via `multiprocessing.shared_memory`: unnecessary complexity for per-process parse calls.
- `threading` instead of `multiprocessing`: ctypes releases GIL during C calls, but Python-side GIL contention could limit throughput for CPU-bound parsing.

### 4. Cross-Platform Shared Library Naming and Loading

**Decision**: `_load_library()` searches one location (`pytest_bdd/_gherkin_go/`) with platform-appropriate name.

```python
_suffix_map = {
    "linux": "libgherkin_go.so",
    "win32": "gherkin_go.dll",
    "darwin": "libgherkin_go.dylib",
}
```

**Rationale**: ctypes' `CDLL()` requires the exact filename. Python's `sys.platform` provides reliable platform detection. The library is a single file in the package data directory — no search path complexity.

**Alternatives considered**:
- `ctypes.util.find_library("gherkin_go")`: unreliable across platforms for custom libraries.
- Environment variable override (`GHERKIN_GO_LIBRARY_PATH`): could be added as an escape hatch if needed.

### 5. Go Gherkin Library API (cucumber/gherkin/go/v28)

**Decision**: Use `gherkin.ParseGherkinDocument(io.Reader, newId func() string)` for plain Gherkin, and a custom markdown path via `GherkinInMarkdownTokenMatcher` for markdown.

**Rationale**: The Go library provides:
- `gherkin.ParseGherkinDocument(reader io.Reader, newId func() string) (*messages.GherkinDocument, error)` — parses plain `.feature`.
- `gherkin.ParseGherkinDocumentForMarkdown(reader io.Reader, newId func() string) (*messages.GherkinDocument, error)` — in newer versions, or construct manually with `TokenMatcher`.

The returned `*messages.GherkinDocument` is a protobuf-generated struct. Serialize to JSON via `json.Marshal()` before returning to Python. The JSON output must match the structure produced by the Python `gherkin.parser.Parser().parse()` dict.

**Alternatives considered**:
- Protobuf binary serialization: adds protobuf dependency on Python side; JSON is simpler and already the existing format.
- Direct struct passing via ctypes: complex, fragile, version-sensitive.

### 6. Build Caching Strategy

**Decision**: Hash-based cache in `_build.py` — compare SHA256 of all `.go` files in `gherkin_go/` against a stored hash file.

**Rationale**: Go compilation is slow (~10-30s). For iterative development, recompilation should only happen when source files change. A `.gherkin_go_build_hash` file in the build output directory stores the last-known hash.

**Alternatives considered**:
- Timestamp-based: unreliable with git operations that touch files.
- Always rebuild: wastes developer time.
- Go build cache (`GOCACHE`): already used by Go toolchain, but doesn't prevent the `go build` process invocation.

### 7. Error Handling Strategy for Go Panics

**Decision**: Wrap ctypes calls in try/except that catches `OSError`, `ValueError`, and `ctypes.ArgumentError`. Use `faulthandler` module to detect segfaults.

**Rationale**: Go panics in CGo code may manifest as segfaults or abnormal termination. Python's `faulthandler` can register a handler that produces a traceback before process death. However, in a multiprocessing worker, process death is acceptable — the parent pool will detect the worker exit and restart it.

**Alternatives considered**:
- Signal handlers in Go: don't prevent crash, just log before exit.
- `setjmp`/`longjmp`: not available from Python side.

### 8. JSON Format Compatibility

**Decision**: Go serializes `*messages.GherkinDocument` via `json.Marshal()`. Python uses `message_converter.from_dict()` to convert the result to a `cucumber_messages.GherkinDocument` dataclass.

**Rationale**: The Python `gherkin.parser.Parser().parse()` returns a plain dict. `collector_batch.py:_parse_feature_file()` then calls `message_converter.from_dict(raw_dict, GherkinDocument)`. The Go JSON output must be structurally identical to this dict. Field naming (snake_case with leading lowercase) must match. Protobuf JSON serialization in Go uses `jsonpb` or direct `json.Marshal` with proper field name mappings.

**Risk**: Field name mismatches between Go protobuf JSON and Python cucumber_messages model. Mitigation: cross-backend comparison test against `gherkin/testdata/good/` fixtures catches any mismatch.
