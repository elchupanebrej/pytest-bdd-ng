# Go Gherkin Parser via cgo — Design

**Date:** 2026-05-11
**Status:** Draft
**Scope:** Replace pure-Python `gherkin.parser.Parser().parse()` with Go-compiled shared library via ctypes, while keeping the existing Python parser as fallback.

## Problem

`gherkin-official` (v39) is a pure-Python parser auto-generated from `.razor` templates. For projects with many feature files, the CPU-bound Gherkin parsing step dominates collection time. The Go implementation of the same parser (from `cucumber/gherkin/go`) compiles to native code and is expected to be significantly faster.

## Non-Goals

- Do NOT replace pickle compilation (`gherkin.pickles.compiler.Compiler`) — only `Parser().parse()`.
- Do NOT replace step-expression parsers (`parsers.py`).
- Do NOT add Go source code to this repository — Go sources are vendored from `cucumber/gherkin` via `go mod vendor`.
- Do NOT remove the existing `gherkin-official` dependency or Python parser path.

## Solution: Go cgo Shared Library + ctypes Bridge (Approach A)

A thin Go wrapper (`gherkin_go/bridge/bridge.go`) imports `cucumber/gherkin/go`, exposes C-compatible functions via `//export`. The wrapper is compiled to a shared library (`.so`/`.dll`/`.dylib`) using `go build -buildmode=c-shared`. Python loads the library via `ctypes` and calls parse functions that return JSON strings — identical in structure to the dict returned by the existing Python `Parser().parse()`.

Backend selection is driven by the `PYTEST_BDD_GHERKIN_BACKEND` environment variable (`auto`, `go`, `python`). In `auto` mode, the Go parser is tried first; on any failure (library not available, parse error, segfault), it falls back to the Python parser per-file.

### Architecture

```text
┌──────────────────────────────────────────────────┐
│ pytest-bdd runtime (collector_batch.py)          │
│   _parse_feature_file(path, content)             │
│     │                                             │
│     ├─ content.decode()                          │
│     ├─ [NEW] _gherkin_go.parse(text)  ───┐       │
│     │   или                               │       │
│     └─ [OLD] Parser(AstBuilder()).parse() │       │
│                                           ▼       │
│                              ┌──────────────────┐ │
│                              │ ctypes bridge    │ │
│                              │ _bridge.py       │ │
│                              └────────┬─────────┘ │
│                                       │           │
└───────────────────────────────────────┼───────────┘
                                        │
                          C ABI (.so / .dll / .dylib)
                                        │
┌───────────────────────────────────────┼───────────┐
│ gherkin_go/bridge/                    │           │
│   bridge.go (//export)               │           │
│     ParseGherkinDocument(*C.char) → *C.char (JSON)│
│     ParseGherkinMarkdown(*C.char) → *C.char (JSON)│
│     FreeCString(*C.char)                          │
│                                        │           │
│   vendor/ ← go mod vendor              │           │
│     cucumber/gherkin/go               │           │
│     cucumber/messages/go              │           │
└────────────────────────────────────────┴───────────┘
```

### Components

#### 1. Go Bridge (`gherkin_go/bridge/bridge.go`)

Exports three C functions:

```go
//export ParseGherkinDocument
func ParseGherkinDocument(text *C.char) *C.char

//export ParseGherkinMarkdown
func ParseGherkinMarkdown(text *C.char) *C.char

//export FreeCString
func FreeCString(s *C.char)

//export Version
func Version() *C.char
```

- `ParseGherkinDocument` — parses plain `.feature` text, returns JSON GherkinDocument or error array.
- `ParseGherkinMarkdown` — parses markdown `.feature.md` text, returns JSON GherkinDocument or error array.
- `FreeCString` — frees a C string allocated by Go. Python MUST call this after every parse call.
- `Version` — returns the Go gherkin library version string.

**Return format:**

Success: `{"type":"GherkinDocument","feature":{"type":"Feature","language":"en","keyword":"Feature","name":"...","children":[...],"tags":[...]}}`

Error: `[{"source":{"uri":"","location":{"line":3,"column":1}},"message":"..."}]`

Python detects success/error by checking the first character: `{` = GherkinDocument, `[` = error array.

#### 2. Python Bridge (`src/pytest_bdd/_gherkin_go/`)

```text
src/pytest_bdd/_gherkin_go/
  __init__.py     # parse(text, *, mimetype) -> dict  (public API)
  _bridge.py      # ctypes low-level: library load, C calls, memory management
  _types.py       # GherkinParseError, GherkinGoNotAvailable
```

**`_bridge.py`** — low-level ctypes layer:

- `_load_library()` — searches for `libgherkin_go.so` / `gherkin_go.dll` / `libgherkin_go.dylib` in `pytest_bdd/_gherkin_go/` (package data path).
- Wraps C calls: `text: str` → `.encode("utf-8")` → `ctypes.c_char_p` → call Go → read `*C.char` → `json.loads()` → call `FreeCString()` via `try/finally`.
- Caches the `ctypes.CDLL` handle in the module; loaded once on first import.
- Raises `GherkinGoNotAvailable` if the shared library cannot be loaded.

**`__init__.py`** — public API:

```python
def parse(text: str, *, mimetype: Mimetype) -> dict:
    """Parse Gherkin text, returning dict identical to Parser().parse()."""
    if mimetype == Mimetype.gherkin_markdown:
        json_str = _bridge.parse_gherkin_markdown(text)
    else:
        json_str = _bridge.parse_gherkin_document(text)
    result = json.loads(json_str)
    if isinstance(result, list):
        raise GherkinParseError(result)
    return result
```

**`_types.py`** — exception classes:
- `GherkinGoNotAvailable(RuntimeError)` — shared library missing or incompatible.
- `GherkinParseError` — wraps the error list from Go (structured like `CompositeParserException.errors`).

#### 3. Backend Selection (`PYTEST_BDD_GHERKIN_BACKEND`)

| Value | Behavior |
|-------|----------|
| `auto` (default) | Try Go first; fall back to Python per-file on any failure |
| `go` | Only Go; raise `GherkinGoNotAvailable` if unavailable, raise `GherkinParseError` on syntax errors (no Python fallback) |
| `python` | Only Python (current behavior) |

The selection logic lives in `collector_batch.py:_parse_feature_file()` alongside existing imports. When Go backend is selected, import `_gherkin_go.parse` is attempted lazily (late import) to avoid breaking environments without the shared library.

#### 4. Build Integration (`src/pytest_bdd/_gherkin_go/_build.py`)

A setuptools `Command` subclass (`BuildGoCommand`) registered in `pyproject.toml`:

```toml
[tool.setuptools.cmdclass]
build_go = "pytest_bdd._gherkin_go._build:BuildGoCommand"
```

**Build process:**
1. Check for Go toolchain (`go version` available on PATH).
2. If missing: print warning, skip.
3. If present: `go build -buildmode=c-shared -o <output_dir>/libgherkin_go.<ext> ./gherkin_go/bridge`.
4. Output directory: `src/pytest_bdd/_gherkin_go/`.
5. Cache: compare hash of `gherkin_go/` sources — skip rebuild if unchanged.

**Chain:** `build_go` → `build_py` → `build_package_data` → wheel. If Go build fails, wheel is still produced (without shared library).

**Package-data inclusion:**

```toml
[tool.setuptools.package-data]
"pytest_bdd._gherkin_go" = ["*.so", "*.dll", "*.dylib"]
```

#### 5. Error Handling & Degradation

| Layer | Situation | Behavior |
|-------|-----------|----------|
| Build | No Go toolchain | Warning; wheel without `.so`; runtime falls back to Python |
| Load | `.so` not found in package | `GherkinGoNotAvailable`; fallback to Python |
| Load | Platform mismatch (e.g., x86 .dll on x64) | `GherkinGoNotAvailable`; fallback; log details |
| Parse | Invalid Gherkin syntax | `GherkinParseError` containing structured error list |
| Parse | Go panic / segfault | `faulthandler` registers; per-file fallback to Python |
| Parse | Null bytes in text | Python filters before passing to Go (replace/remove) |
| Memory | `FreeCString` not called | `__del__` on wrapper object calls it at GC; C string leaks until process exit |

**Logging guidelines:**
- INFO on first successful Go parse: `"Using Go gherkin parser v{X.Y.Z}"`
- WARNING on fallback: `"Go gherkin parser unavailable ({reason}), falling back to Python"`
- DEBUG on individual parse calls with timing

#### 6. Multiprocessing Safety

Each worker process in `multiprocessing.Pool.starmap` imports `_gherkin_go` independently. The Go shared library uses CGo threads that interface with Python's GIL correctly via ctypes. No shared state between processes.

#### 7. Repository Layout

```text
gherkin_go/                     # Go module: our bridge + vendored deps
  go.mod
  go.sum
  bridge/
    bridge.go                   # C-exported parse functions
  vendor/                       # go mod vendor output
    cucumber/gherkin/go/...
    cucumber/messages/go/...

src/pytest_bdd/
  _gherkin_go/                  # Python integration package
    __init__.py                 # Public API: parse()
    _bridge.py                  # ctypes low-level
    _build.py                   # setuptools Command
    _types.py                   # Exceptions
```

## Testing Strategy

### Unit Tests (instant group)
- `tests/unit/test_gherkin_go_bridge.py` — test `_bridge.py` ctypes calls with a compiled `.so` (CI with Go installed) and without (CI without Go).
- `tests/unit/test_gherkin_go_parse.py` — test `parse()` with valid/invalid Gherkin, both plain and markdown.
- `tests/unit/test_gherkin_go_fallback.py` — test backend selection, `GherkinGoNotAvailable` fallback path.

### Integration Tests (medium group)
- `tests/feature/test_gherkin_go_collection.py` — full collection with Go backend active; verify parsed results match Python backend.
- Cross-comparison: run `_parse_feature_file` against all `gherkin/testdata/good/` fixtures with both backends, assert identical `GherkinDocument` dicts.

### Build Tests (slow group)
- `tests/build/test_gherkin_go_build.py` — test `BuildGoCommand` succeeds/fails gracefully.

### CI Matrix
- Linux (ubuntu-latest) with Go installed → compile + run all tests
- Windows (windows-latest) with Go installed → compile + run all tests
- macOS (macos-latest) with Go installed → compile + run all tests
- All platforms without Go → verify graceful fallback

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Go version incompatibility with vendored modules | Pin Go toolchain version in CI; `go.mod` specifies minimum Go version |
| cgo thread overhead vs multiprocessing | Benchmarked before merge; if Go per-call overhead > Python parse time, use different threshold |
| Platform-specific .so/.dll names | `_load_library()` handles three suffixes; `sys.platform` detection |
| Vendored Go code goes stale vs upstream cucumber/gherkin | `go get -u` + `go mod vendor` in CI on schedule; automated update PR |
| cgo + Python signal handling conflicts | `faulthandler` enabled; per-file fallback strategy limits blast radius |
