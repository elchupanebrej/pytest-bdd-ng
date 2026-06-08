# ADR-005: Go cgo Parser as Optional Performance Backend

**Status:** Accepted
**Date:** 2026-06-08
**Deciders:** pytest-bdd-ng core team

## Context

Gherkin feature file parsing is CPU-intensive. pytest-bdd-ng parses dozens to thousands of `.feature` files during test collection. The existing Python parser (`gherkin-official>=33`) handles the general case correctly but can be a bottleneck in large test suites.

A Go-based parser backend already exists in the codebase, built as a cgo shared library and accessed via `ctypes`. The Go parser delivers ≥2× parsing speedup compared to the Python fallback in benchmarks. However, the current integration requires a Go toolchain at build time for ALL users — even those who never use the Go backend. This violates the principle that `pip install pytest-bdd` should succeed without external toolchain dependencies.

## Decision

Extract the Go parser to an **optional extra** with a Python fallback path:

1. **`pip install pytest-bdd`** — no Go toolchain required. Python `gherkin.parser.Parser` handles all parsing.
2. **`pip install pytest-bdd[go-parser]`** — includes the Go bridge and triggers shared library compilation during install.
3. **Runtime backend selection** via `PYTEST_BDD_GHERKIN_BACKEND` env var:
   - `auto` (default): Go parser if the shared library is available, Python fallback otherwise
   - `go`: Go parser required; raises `ImportError` with an install hint if unavailable
   - `python`: Always use Python parser

The Go parser bridge (`src/pytest_bdd/_gherkin_go/`) ships with the main package (Python files only), but the shared library (`.so`/`.dll`/`.dylib`) is only built when the `go-parser` extra is installed. The `_get_parser()` factory in `__init__.py` handles import resolution via `importlib` — attempting the Go import lazily and falling back to Python when the bridge or shared library is unavailable.

The `BuildGoCommand` setuptools command in `_build.py` guards against missing Go toolchain: it warns (not errors) when Go or a C compiler is absent, allowing the main package to install successfully without Go.

## Consequences

### Positive

- **Frictionless install:** Users installing `pytest-bdd` for basic usage do not need Go or a C compiler.
- **Faster CI:** Teams that install `[go-parser]` in CI get ≥2× parsing speedup during collection.
- **Transparent fallback:** The Python parser always handles parsing when Go is unavailable; no user-visible breakage.
- **Backward compatible:** Existing `PYTEST_BDD_GHERKIN_BACKEND` env var semantics are preserved.

### Negative

- **Go toolchain requirement for builders:** Building the shared library requires Go 1.21+ and a C compiler (gcc/clang). This is documented but not enforced by pip.
- **cgo cross-platform complexity:** The Go shared library must be compiled for each target platform (Linux `.so`, macOS `.dylib`, Windows `.dll`). Pre-built wheels may be needed for broad distribution.
- **Maintenance burden:** The cgo bridge (`_bridge.py`, `gherkin_go/bridge/`) must be kept compatible with gherkin version bumps. The bridge is minimal (3 C exports) but requires periodic testing.

### Neutral

- **Env-var gating preserved:** `PYTEST_BDD_GHERKIN_BACKEND` gives users explicit control over parser selection.
- **`_gherkin_go/` stays in main package:** The Python bridge files ship with every install; only the native shared library is optional. This avoids complex package restructuring.
