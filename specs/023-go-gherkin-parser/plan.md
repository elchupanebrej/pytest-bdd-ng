# Implementation Plan: Go Gherkin Parser

**Branch**: `023-go-gherkin-parser` | **Date**: 2026-05-11 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/023-go-gherkin-parser/spec.md`

## Summary

Replace the pure-Python `gherkin.parser.Parser().parse()` call with a Go-compiled shared library accessed via ctypes. The Go parser wraps `cucumber/gherkin/go` (vendored via `go mod vendor`), compiled to a platform-specific shared library (`libgherkin_go.so`/`.dll`/`.dylib`) using `go build -buildmode=c-shared`. A custom setuptools `BuildGoCommand` integrates compilation into the wheel build. Backend selection via `PYTEST_BDD_GHERKIN_BACKEND` env var (`auto`/`go`/`python`). Existing Python parser remains as fallback.

## Technical Context

**Language/Version**: Python 3.10-3.14 (runtime), Go 1.21+ (build-time only, for cgo shared library compilation)
**Primary Dependencies**: `gherkin-official>=33` (Python fallback, unchanged), `cucumber/gherkin/go/v28` (Go parser, vendored), `cucumber/messages/go/v28` (Go messages, vendored), `ctypes` (stdlib), `setuptools` (build)
**Storage**: N/A — in-memory parsing only, no persistent storage
**Testing**: pytest (instant/medium/slow groups), `gherkin/testdata/good/` fixtures for cross-backend comparison, ctypes mock tests
**Target Platform**: Linux (amd64, `.so`), Windows (x86_64, `.dll`), macOS (arm64 & amd64, `.dylib`) — all platforms with working cgo
**Project Type**: Python library with optional native compiled extension
**Performance Goals**: 2x+ wall-clock speedup vs pure-Python parser for suites with 100+ feature files
**Constraints**: Must not regress Python-only mode (no Go required at runtime), wheel must build without Go toolchain, lazy import for ctypes module
**Scale/Scope**: ~7 new Python files (`_gherkin_go/` package), ~3 new Go files (`gherkin_go/bridge/`), ~6 new test files, vendored Go dependencies

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Pure BDD Integration | PASS | Internal parsing optimization; no Gherkin semantics change; feature files unchanged |
| II. Realistic Runtime Evidence | PASS | No reporter or NDJSON changes; existing evidence pipeline untouched |
| III. Explicit Returns | PASS | Go functions return explicit `*C.char`; Python wrapper returns `dict` or raises deterministic exceptions (`GherkinParseError`, `GherkinGoNotAvailable`) |
| IV. Broad Compatibility | PASS | Python 3.10-3.14, pytest>=7; Go toolchain is build-time only, not runtime |
| V. Quality & Formatting | PASS | New Python code passes ruff/mypy; Go code passes `go vet`; all docs in English |

**Re-check gates**: No violations. All principles satisfied.

## Agentic Implementation Strategy

*GATE: Define how Superpowers and subagents will be leveraged.*

**Superpowers**: `test-driven-development` for all new code, `systematic-debugging` for cgo/cross-platform issues, `verification-before-completion` before claiming work done

**Subagent Dispatch**: Dispatch independent pieces in parallel:
- Go bridge code + Go build → one subagent (Go context)
- Python ctypes bridge (`_bridge.py`, `_types.py`) → one subagent
- Python public API (`__init__.py`) + setuptools build command (`_build.py`) → one subagent
- Integration into `collector_batch.py` → one subagent
- Tests (unit, integration, build) → parallel subagents after contracts defined

Each subagent receives: precise TDD contract (RED-GREEN-REFACTOR), target file paths, and the cross-backend equivalence requirement.

## Project Structure

### Documentation (this feature)

```text
specs/023-go-gherkin-parser/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   └── json-bridge.md   # Go↔Python JSON contract
└── tasks.md             # Phase 2 output (/speckit.tasks)
```

### Source Code (repository root)

```text
gherkin_go/                     # Go module: bridge + vendored deps
  go.mod                        # module github.com/pytest-bdd/gherkin-go-bridge
  go.sum
  bridge/
    bridge.go                   # //export C functions: ParseGherkinDocument, ParseGherkinMarkdown, FreeCString, Version
  vendor/                       # go mod vendor output (committed)
    cucumber/gherkin/go/...
    cucumber/messages/go/...

src/pytest_bdd/
  _gherkin_go/                  # Python integration package
    __init__.py                 # Public API: parse(text, *, mimetype) -> dict
    _bridge.py                  # ctypes low-level: library load, C calls, memory management
    _build.py                   # setuptools BuildGoCommand
    _types.py                   # GherkinParseError, GherkinGoNotAvailable
  collector_batch.py            # [MODIFIED] Add Go backend selection in _parse_feature_file()

tests/
  unit/
    test_gherkin_go_bridge.py   # ctypes bridge unit tests
    test_gherkin_go_parse.py    # parse() function tests
    test_gherkin_go_fallback.py # Backend selection and fallback tests
  feature/
    test_gherkin_go_collection.py  # Integration: full collection with Go backend
  build/
    test_gherkin_go_build.py    # BuildGoCommand tests
```

**Structure Decision**: Single-project layout. Go module lives at repo root (`gherkin_go/`) for `go build` to resolve correctly. Python package lives under `src/pytest_bdd/_gherkin_go/` following existing project convention. Shared library output goes into `src/pytest_bdd/_gherkin_go/` as package data for wheel inclusion.

## Complexity Tracking

> No constitution violations. This section intentionally empty.
