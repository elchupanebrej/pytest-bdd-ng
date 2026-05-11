# Feature Specification: Go Gherkin Parser

**Feature Branch**: `023-go-gherkin-parser`
**Created**: 2026-05-11
**Status**: Draft
**Input**: User description: "Replace pure-Python gherkin.parser.Parser().parse() with Go-compiled shared library via cgo ctypes bridge, while keeping the existing Python parser as fallback."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Faster Feature Parsing with Automatic Fallback (Priority: P1)

As a pytest-bdd user with many feature files, I want features to be parsed significantly faster without any configuration changes, so that my test suite collection time is reduced.

**Why this priority**: This is the core value proposition — users get immediate performance benefits by default without changing their workflow.

**Independent Test**: Install pytest-bdd with Go parser support, run an existing test suite with many feature files, and verify collection time decreases compared to pure-Python parsing. If Go parser is unavailable (environment without Go toolchain), verify that parsing still works correctly via Python fallback with no errors.

**Acceptance Scenarios**:

1. **Given** pytest-bdd is installed with Go parser shared library, **When** feature files are collected and parsed in `auto` backend mode, **Then** parsing uses the Go parser and produces identical GherkinDocument results as the Python parser.
2. **Given** pytest-bdd is installed without Go parser shared library, **When** feature files are collected and parsed in `auto` backend mode, **Then** parsing falls back to Python parser and produces correct results.
3. **Given** a feature file with invalid Gherkin syntax, **When** parsed via Go parser, **Then** a structured parse error is raised matching the format of Python parser's CompositeParserException.
4. **Given** a feature file with null bytes in the text, **When** parsed via Go parser, **Then** parsing completes without crash and null bytes are handled gracefully.

---

### User Story 2 - Explicit Backend Selection via Environment Variable (Priority: P2)

As a power user or CI operator, I want to explicitly control which parser backend is used, so that I can force a specific parser for debugging, benchmarking, or when I know one backend has issues.

**Why this priority**: Enables controlled testing and debugging. Lower priority than automatic behavior because the default should work for most users.

**Independent Test**: Set `PYTEST_BDD_GHERKIN_BACKEND=python`, run tests, verify only Python parser is used. Set `PYTEST_BDD_GHERKIN_BACKEND=go`, run tests, verify Go parser is used or an error is raised if unavailable. Set `PYTEST_BDD_GHERKIN_BACKEND=auto`, verify automatic selection.

**Acceptance Scenarios**:

1. **Given** `PYTEST_BDD_GHERKIN_BACKEND=python`, **When** feature files are parsed, **Then** only the Python parser is used regardless of Go library availability.
2. **Given** `PYTEST_BDD_GHERKIN_BACKEND=go` and Go library is available, **When** feature files are parsed, **Then** only the Go parser is used.
3. **Given** `PYTEST_BDD_GHERKIN_BACKEND=go` and Go library is NOT available, **When** feature files are parsed, **Then** a clear error is raised indicating Go parser is unavailable.
4. **Given** `PYTEST_BDD_GHERKIN_BACKEND` is not set (default `auto`), **When** the first successful Go parse occurs, **Then** an INFO log message confirms the Go parser version being used.

---

### User Story 3 - Build pytest-bdd Wheel with Go Parser Embedded (Priority: P3)

As a pytest-bdd package maintainer or CI pipeline, I want the Go parser to be compiled and included in the Python wheel during the build process, so that users receive a ready-to-use wheel with native parser support.

**Why this priority**: This is a build-time concern that enables P1 and P2. It must work, but end users don't interact with it directly.

**Independent Test**: Run the wheel build on a machine with Go toolchain, verify the resulting wheel contains the shared library (`.so`/`.dll`/`.dylib`). Run the wheel build on a machine without Go toolchain, verify the wheel is still produced (without shared library) and installs without errors.

**Acceptance Scenarios**:

1. **Given** Go toolchain is available on PATH, **When** `build_go` setuptools command runs, **Then** a shared library is compiled and placed in the package data directory.
2. **Given** Go toolchain is NOT available on PATH, **When** `build_go` setuptools command runs, **Then** a warning is printed and the wheel is still produced successfully.
3. **Given** Go source files have not changed since last build, **When** `build_go` setuptools command runs, **Then** compilation is skipped (cached).
4. **Given** the built wheel is installed in a clean environment, **When** the Go parser module is imported, **Then** the shared library is loadable via ctypes.

---

### Edge Cases

- What happens when the Go shared library is compiled for a different architecture (e.g., x86 `.dll` loaded on x64 Python)? The library fails to load, `GherkinGoNotAvailable` is raised, and Python fallback takes over in `auto` mode.
- What happens when the Go parser panics or segfaults during parsing? The ctypes wrapper catches the failure, logs the error, and falls back to Python parser for that specific file in `auto` mode. In `go` mode, the error is raised.
- What happens when multiple worker processes use the Go parser simultaneously (via multiprocessing)? Each process loads its own copy of the shared library — no shared state, fully safe.
- What happens when Python forgets to free the C string returned by Go? A `__del__` cleanup on the Python wrapper object calls `FreeCString` during garbage collection. If GC doesn't run, the memory leaks until process exit.
- What happens with Markdown Gherkin (`.feature.md`) files? A separate Go C-exported function `ParseGherkinMarkdown` handles markdown-formatted Gherkin, mirroring the Python `MarkdownGherkinParser`.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST provide a Go parser backend that parses Gherkin feature text and returns a GherkinDocument in the same JSON structure as the existing Python `gherkin.parser.Parser().parse()`.
- **FR-002**: System MUST support both plain Gherkin (`.feature`) and Markdown Gherkin (`.feature.md`) parsing in the Go backend.
- **FR-003**: System MUST automatically select the Go parser when available in `auto` backend mode (default behavior).
- **FR-004**: System MUST fall back to the Python parser in `auto` mode when the Go parser is unavailable, fails to load, or encounters an unrecoverable error during parsing.
- **FR-005**: Users MUST be able to select the parser backend via the `PYTEST_BDD_GHERKIN_BACKEND` environment variable with values `auto`, `go`, or `python`.
- **FR-006**: In `go` backend mode, system MUST NOT fall back to Python parser — it MUST raise an error if Go is unavailable.
- **FR-007**: System MUST log the Go parser version on first successful use at INFO level.
- **FR-008**: System MUST log the reason for fallback at WARNING level when Go parser is unavailable in `auto` mode.
- **FR-009**: Go and Python parsers MUST produce byte-identical `GherkinDocument` dicts for the same valid Gherkin input.
- **FR-010**: The Go shared library MUST be compiled via `go build -buildmode=c-shared` during the wheel build process as a setuptools Command.
- **FR-011**: The wheel build MUST succeed (without Go parser) even when the Go toolchain is not installed.
- **FR-012**: The Go build step MUST cache its output and skip recompilation when source files are unchanged.
- **FR-013**: Python MUST call `FreeCString` (or its wrapper) after every Go parse call to avoid native memory leaks.
- **FR-014**: The Go parser MUST handle both valid and invalid Gherkin input, returning either a GherkinDocument or a structured error list in a well-defined JSON format.

### Key Entities

- **GherkinDocument**: The parsed Abstract Syntax Tree of a feature file, containing Feature, Scenarios, Steps, Tags, and their positions. Same structure in both Python and Go backends.
- **GherkinParseError**: A structured error containing source location (URI, line, column) and error message. Maps to Python's `CompositeParserException`.
- **GherkinGoNotAvailable**: An exception indicating the Go shared library could not be loaded. Triggers fallback behavior in `auto` mode.
- **Shared Library**: A platform-specific compiled artifact (`.so`, `.dll`, `.dylib`) embedded in the Python wheel package data, loaded via ctypes.

## Agentic Validation Constraints

- **TDD Contract**: The specifications detailed here form the "WHAT" defined by Speckit. They must be rigid enough to drive automated RED-GREEN-REFACTOR cycles by subagents leveraging Superpowers.
- **Validation**: All acceptance scenarios must be mechanically verifiable without human intuition to serve as strict unit-test targets.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Feature file collection and parsing is measurably faster with the Go parser than with the pure-Python parser on the same hardware with 100+ feature files (measured by wall-clock time, with at least a 2x speedup expected).
- **SC-002**: Both Go and Python backends produce identical parse results for all valid Gherkin test fixtures in the `gherkin/testdata/good/` dataset.
- **SC-003**: The wheel build succeeds on all three major platforms (Linux, Windows, macOS) both with and without Go toolchain installed.
- **SC-004**: An existing pytest-bdd test suite with 100% Python parser usage continues to pass without modification after the Go parser is added (backward compatibility).
- **SC-005**: In `auto` mode, when the Go parser fails at runtime, the user's test run completes successfully using the Python fallback with no loss of test results.

## Assumptions

- The Go toolchain (Go 1.21+) is available on the build machine for producing wheels with Go parser support. Wheels without Go support are still functional.
- The `cucumber/gherkin/go` library (v28+) produces GherkinDocument JSON compatible with the `cucumber-messages` Python package schema used by pytest-bdd.
- Users running on standard platforms (amd64 Linux, x86_64 Windows, arm64/aarch64 macOS) are the primary target. Other architectures may need manual compilation.
- The performance benefit justifies the added build complexity. A benchmark will be run before the feature ships to verify the speedup.
- The existing `gherkin-official>=33` dependency remains in pyproject.toml as the Python fallback parser.
