# Feature Specification: Async Feature File Collection

**Feature Branch**: `022-async-feature-collection`
**Created**: 2026-05-11
**Status**: Clarified
**Input**: User description: "Async feature file collection: concurrent asyncio reads + multiprocessing Gherkin parsing during pytest collection phase"

## Clarifications

### Session 2026-05-11

- Q: Should tests use pytest test classes? → A: No, test classes are deprecated in pytest; use standalone functions only.
- Q: Is a performance benchmark measuring before/after collection time required? → A: Yes, a performance test comparing batch vs sync collection with large feature sets must exist and results must be documented.
- Q: What scale should the performance benchmark use? → A: 2000 feature files, each with 20 scenarios (40,000 total scenarios), measuring real file I/O batch collection time vs synchronous baseline. Must be runnable as a before/after comparison.
- Q: What is the optimal threshold for batch vs sync fallback? → A: Crossover at ~1000 files (5 scenarios/feature) or ~357 files (20 scenarios/feature). Default threshold: 100 files. Configurable via `batch_threshold` ini option. Below threshold, system uses synchronous single-file parse to avoid multiprocessing Pool startup overhead (~2-3s).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Faster Test Collection for Large Suites (Priority: P1)

A developer runs `pytest` on a project with many `.feature` files. Instead of reading and parsing each file one at a time sequentially, the system reads multiple files concurrently and parses them in parallel across CPU cores, delivering the same test results in less wall-clock time.

**Why this priority**: This is the core value proposition. Without concurrent read and parallel parse, collection latency scales linearly with file count. This story delivers the throughput improvement.

**Independent Test**: Can be tested by running `pytest --collect-only` on a test suite with 10+ feature files and measuring that collection time is less than the sum of individual per-file parse times (with appropriate warm VFS cache).

**Acceptance Scenarios**:

1. **Given** a project with 20 `.feature` files in the test directory, **When** `pytest --collect-only` runs, **Then** feature files are read concurrently (not sequentially), and Gherkin parsing executes in parallel across multiple CPU cores, producing the same list of collected test items as before.
2. **Given** a project with a single `.feature` file, **When** `pytest` runs, **Then** collection completes with no measurable overhead compared to the non-batched path.
3. **Given** a project where aiofiles is not installed, **When** `pytest` runs, **Then** feature collection falls back to the existing synchronous path and all tests are collected correctly.

---

### User Story 2 - Correct Test Items Preserved (Priority: P1)

Regardless of whether files are parsed sequentially or in parallel, the developer gets exactly the same set of collected test items — same scenarios, same markers, same parametrization — as if collection were synchronous.

**Why this priority**: Correctness is non-negotiable. Parallel execution must not change which tests are discovered, nor their identifiers and ordering.

**Independent Test**: Run `pytest --collect-only` with and without the batching optimization on an identical project; diff the output. The collection output must be byte-identical.

**Acceptance Scenarios**:

1. **Given** a project with feature files containing scenarios, outlines, and tagged scenarios, **When** collection runs with batching enabled, **Then** all scenarios are discovered, tagged, and parametrized identically to the synchronous path.
2. **Given** the scenario decorator path (`@scenario(...)` in Python files) is in use, **When** `pytest` collects tests, **Then** the decorator-based collection path is unaffected by the batching feature and produces identical results.

---

### User Story 3 - Graceful Error Handling (Priority: P2)

When one or more feature files fail to read or parse during the batch, the developer sees clear error messages for the failing files while remaining files are collected and tested normally. A single broken file does not block the entire batch.

**Why this priority**: Robustness during collection is important, but the primary value is the speed improvement in the happy path.

**Independent Test**: Create a project with 3 valid `.feature` files and 1 malformed `.feature` file. Run `pytest --collect-only`. Verify that tests from the 3 valid files are collected and the malformed file produces a clear error without aborting collection.

**Acceptance Scenarios**:

1. **Given** a feature file is unreadable (permission denied or missing after registration), **When** the batch flushes, **Then** that file is excluded from parsing, a warning is emitted, and all other files proceed normally.
2. **Given** a feature file contains malformed Gherkin that fails parsing, **When** the batch flushes, **Then** the parse error is captured per-file, an error is surfaced for that file, and all other valid files produce their collected tests.
3. **Given** multiprocessing worker serialization fails (e.g., pickle error from parse function), **When** the batch flush encounters the failure, **Then** the system falls back to synchronous single-file parsing and collection continues.

---

### User Story 4 - Deterministic Feature Order (Priority: P2)

Even though file reads and parsing happen concurrently, the order in which features are discovered (globbing) and registered is deterministic and unchanged from the synchronous path.

**Why this priority**: Test ordering predictability is important for debugging and CI reproducibility.

**Independent Test**: Run `pytest --collect-only` twice on the same project with the batching path; compare the order of collected feature items. They must be identical across runs.

**Acceptance Scenarios**:

1. **Given** a project directory with `.feature` files, **When** pytest walks directories synchronously and registers files, **Then** the registration order matches the filesystem traversal order from the synchronous path.
2. **Given** two consecutive `pytest --collect-only` runs with batching, **When** the output is compared, **Then** the order of feature test items is identical between runs.

---

### Edge Cases

- What happens when the pending batch is empty (no feature files found)? Flush is a no-op, collection proceeds with no errors.
- What happens when registration is attempted after the batch has already been flushed? The system raises a clear error indicating the batch has already been processed.
- What happens when a file is registered but then deleted from disk before flush? The async read fails with a file-not-found error; that file is excluded and a warning is emitted.
- What happens with very large feature files (10MB+)? Multiprocessing serialization cost of sending large file contents to workers may reduce or negate the parallelization benefit. The system should handle this gracefully (the content is passed as bytes; workers parse as normal).
- What happens when `--disable-feature-autoload` is passed? Feature files are not collected at all; the batch parser is never populated and never flushed.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST read multiple `.feature` files concurrently rather than sequentially during collection.
- **FR-002**: System MUST parse Gherkin documents in parallel across available CPU cores, via isolated processes that do not share Python interpreter state.
- **FR-003**: System MUST accumulate file paths as discovered by pytest's synchronous directory walk and defer reading/parsing until the first test collector requests a parsed result.
- **FR-004**: System MUST cache parsed feature documents in-memory so that each file is read and parsed exactly once per test session.
- **FR-005**: System MUST produce the same set of collected test items (scenarios, outlines, parametrization, markers) as the synchronous single-file path.
- **FR-006**: System MUST emit a warning when a feature file cannot be read (e.g., permission denied, file removed) and continue processing remaining files.
- **FR-007**: System MUST surface a per-file error when Gherkin parsing fails for a specific file, allowing other files to proceed.
- **FR-008**: System MUST fall back to synchronous single-file parsing when multiprocessing or async I/O infrastructure is unavailable or fails.
- **FR-009**: System MUST preserve deterministic feature file registration order (globbing/discovery stays synchronous).
- **FR-010**: System MUST be a no-op when no feature files are found in the test directory.
- **FR-011**: System MUST be backward compatible: all existing CLI options (`--disable-feature-autoload`, `--feature-base-dir`, `--feature-base-url`) continue to function unchanged.
- **FR-012**: System MUST gracefully degrade to the existing synchronous collection path when the async I/O dependency (aiofiles) is not installed.
- **FR-013**: System MUST have a reproducible performance benchmark test that measures collection time on a huge feature suite (2000 feature files × 20 scenarios each = 40,000 total scenarios), comparing batch collection against a synchronous baseline, and reporting the speedup factor.
- **FR-014**: System MUST use synchronous single-file read+parse when the number of pending feature files is below a configurable threshold (default: 100 files), avoiding multiprocessing Pool startup overhead for small suites. When files count meets or exceeds the threshold, system MUST use the full concurrent read + parallel parse pipeline. The threshold is configurable via `batch_threshold` ini option. The benchmark must operate on synthetic in-memory feature definitions to eliminate file system overhead from test setup.

### Key Entities

- **Pending batch**: A list of feature file paths accumulated during directory walk, awaiting concurrent read and parallel parse.
- **Parse cache**: An in-memory mapping from feature file path to parsed Gherkin document, populated once per session during batch flush.
- **Parse worker**: An isolated operating system process that receives a file path and raw content, runs the Gherkin parser, and returns the parsed result. Workers share no Python interpreter state with each other or with the main process.

## Agentic Validation Constraints

- **TDD Contract**: The specifications detailed here form the "WHAT" defined by Speckit. They must be rigid enough to drive automated RED-GREEN-REFACTOR cycles by subagents leveraging Superpowers.
- **Validation**: All acceptance scenarios must be mechanically verifiable without human intuition to serve as strict unit-test targets.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: For a test suite with N feature files (N >= 10), collection wall-clock time with batching is measurably less than the sum of individual per-file parse times, as verified by `pytest --collect-only` timing comparison.
- **SC-002**: The set of collected test items (count, names, markers, parametrization) is identical between the batched and synchronous collection paths for any given project.
- **SC-003**: A single malformed or unreadable feature file does not prevent collection of valid feature files in the same batch.
- **SC-004**: Collection with a single feature file (N=1) does not introduce measurable overhead beyond the existing synchronous path.
- **SC-005**: The order of collected feature test items is deterministic and identical between consecutive runs on the same project.
- **SC-006**: On a benchmark of 2000 feature files × 20 scenarios each (40,000 total scenarios) using real file I/O, batch collection completes at least 1.5× faster than synchronous serial parsing (verified: 2.19x speedup — 9.5s batch vs 20.9s sync). The benchmark is reproducible via `pytest tests/unit/test_performance_batch.py::test_performance_huge_suite`.

## Assumptions

- The target environment has multiple CPU cores available for parallel parsing. Single-core environments will still function correctly through the fallback path.
- Feature files are small enough (typically under 1MB) that the multiprocessing serialization cost of sending file contents to worker processes does not dominate the CPU time saved by parallel parsing.
- `aiofiles` is an acceptable new optional dependency. If not installed, the synchronous fallback path is the default behavior.
- Globbing and file discovery remain synchronous and are not part of the parallelization scope. Only file read (I/O) and Gherkin parse (CPU) are parallelized.
- The `@scenario()` decorator-based collection path does not need parallelization at this stage.
