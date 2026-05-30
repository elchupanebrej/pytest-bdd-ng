# Feature Specification: Cucumber Formatter Support

**Feature Branch**: `012-cucumber-formatters-support`
**Created**: 2026-03-10
**Status**: Draft
**Input**: User description: "Все репортеры из списка должны поддерживаться также как html реопртер - ключом в командной строке https://github.com/cucumber/cucumber-js/blob/main/docs/formatters.md"

## Clarifications

### Session 2026-03-10

- Q: Can multiple terminal-output reporters be active in the same pytest run? → A: No. Terminal reporter interaction is out of scope; at most one terminal-output reporter may be active per run.
- Q: If more than one terminal-output formatter flag is provided, how should the system behave? → A: Fail fast before test execution with a clear configuration error.
- Q: If a file-based formatter targets a path under a missing directory, how should the system behave? → A: Fail fast with a clear filesystem error and do not create directories automatically.
- Q: How should stream-capable terminal formatters behave during execution? → A: Stream-capable terminal formatters must receive serialized messages incrementally during session execution, including under pytest-xdist, with worker messages forwarded immediately to the controller/main process and live terminal rendering driven there without waiting for final NDJSON consolidation.
- Q: How should `summary` participate in live terminal rendering? → A: `summary` must be fed from the same live incremental message stream as other terminal formatters; if its visible output naturally appears mostly near the end, that is acceptable, but it must not use a separate post-run-only pipeline.
- Q: What ordering semantics should live terminal rendering use under pytest-xdist? → A: Preserve message order within each worker stream, and render inter-worker traffic in controller arrival order rather than delaying output to reconstruct final canonical NDJSON ordering.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Configure formatters via command-line flags (Priority: P1)

Users should be able to generate test execution reports using all natively supported cucumber-js formatters by simply providing the corresponding command-line flag (e.g., `--cucumber-json`, `--cucumber-junit`), matching the existing `--cucumber-html` behavior.

**Why this priority**: Command-line parity with cucumber-js makes the plugin easier to adopt for users migrating from cucumber environments and provides essential reporting formats (like JUnit and JSON) for CI/CD integrations out-of-the-box.

**Independent Test**: Can be fully tested by running a sample test suite with each flag, verifying that the corresponding output file is generated and contains valid data in the expected format, and confirming that stream-capable terminal formatters emit visible output before session completion in both single-process and xdist runs.

**Acceptance Scenarios**:

1. **Given** a standard pytest suite with pytest-bdd-ng, **When** the user runs `pytest --cucumber-json=report.json`, **Then** a valid Cucumber JSON report is generated at `report.json`.
2. **Given** a standard pytest suite with pytest-bdd-ng, **When** the user runs `pytest --cucumber-junit=report.xml`, **Then** a valid JUnit XML report is generated at `report.xml`.
3. **Given** a standard pytest suite with pytest-bdd-ng, **When** the user runs `pytest --cucumber-summary`, **Then** the tests execution summary is printed using the `@cucumber/summary-formatter` and the formatter is fed from the live incremental terminal-reporting stream rather than a separate post-run-only pipeline.
4. **Given** a standard pytest suite with pytest-bdd-ng, **When** the user runs `pytest --cucumber-progress`, **Then** the progress report is printed using the `@cucumber/progress-formatter`.
5. **Given** a standard pytest suite with pytest-bdd-ng, **When** the user runs `pytest --cucumber-pretty`, **Then** the rich execution report is printed using `@cucumber/pretty-formatter`.
6. **Given** a standard pytest suite with pytest-bdd-ng, **When** the user runs `pytest --cucumber-usage=usage.txt`, **Then** a usage report is written to `usage.txt`.
7. **Given** a standard pytest suite with pytest-bdd-ng, **When** the user runs `pytest --cucumber-summary --cucumber-progress`, **Then** pytest fails before test execution with a clear error explaining that only one terminal-output formatter may be active per run.
8. **Given** a standard pytest suite with pytest-bdd-ng, **When** the user runs `pytest --cucumber-json=missing-dir/report.json`, **Then** pytest fails with a clear filesystem error and does not create `missing-dir` automatically.
9. **Given** a standard pytest suite with long-running steps, **When** the user runs `pytest --cucumber-progress`, **Then** progress output becomes visible during session execution rather than only after session completion.
10. **Given** a pytest-xdist suite with multiple workers, **When** the user runs one stream-capable terminal formatter, **Then** worker messages are forwarded immediately to the controller and the controller updates terminal output during the live run.
11. **Given** a pytest-xdist suite with multiple workers, **When** the active terminal formatter receives live messages from workers, **Then** event order is preserved within each worker stream and cross-worker rendering follows controller arrival order without blocking on global reordering.

### Edge Cases

- What happens when a user specifies a formatter flag but the underlying npm package for that formatter is not installed?
- File-output formatters may be combined in the same run, but terminal-output formatter interaction is out of scope and no more than one terminal-output formatter may be active per run.
- If more than one terminal-output formatter is requested, pytest must fail fast before test execution with a clear configuration error.
- If a file-based formatter output path references a missing directory, pytest must fail with a clear filesystem error and must not create directories automatically.
- Under pytest-xdist, live terminal formatter output must be rendered by the controller/main process from incrementally forwarded worker messages rather than from worker-local stdout.
- Under pytest-xdist, live terminal rendering must preserve per-worker event order but may interleave workers according to controller arrival order.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST provide pytest command-line flags for the following cucumber formatters: `summary`, `progress`, `progress-bar`, `pretty`, `json`, `junit`, `snippets`, `usage`, `usage-json`.
- **FR-002**: System MUST generate output to terminal when no file path is specified and the formatter supports stdout (e.g., `summary`, `progress`, `pretty`).
- **FR-003**: System MUST write output to the specified file path when a flag is provided with an argument (e.g., `--cucumber-json=path/to/file.json`).
- **FR-004**: System MUST attempt to auto-provision missing formatter npm dependencies via global `npm install -g` before rendering formatter output.
- **FR-005**: If auto-provisioning fails, system MUST emit a clear error message that instructs the user which package to install manually.
- **FR-006**: System MUST allow multiple formatters to be executed during a single pytest run when their requested outputs do not conflict, generating multiple outputs simultaneously.
- **FR-007**: System MUST permit at most one terminal-output formatter to be active during a single pytest run.
- **FR-008**: If more than one terminal-output formatter flag is provided, system MUST fail before test execution and emit a clear configuration error describing the conflict.
- **FR-009**: If a file-based formatter output path references a directory that does not exist, system MUST fail with a clear filesystem error and MUST NOT create the directory automatically.
- **FR-010**: Stream-capable terminal-output formatters MUST receive cucumber message events incrementally during session execution and may emit visible terminal output before session completion.
- **FR-011**: Under pytest-xdist, worker reporting messages MUST be forwarded incrementally to the controller/main process, and the active terminal formatter MUST be driven from that controller-side live message stream.
- **FR-012**: Live terminal formatting MUST NOT require waiting for finalized canonical NDJSON consolidation before rendering terminal-visible progress updates.
- **FR-013**: `summary` MUST use the same live incremental terminal-reporting pipeline as other terminal formatters, even if the formatter's own visible output is naturally concentrated near the end of the run.
- **FR-014**: Under pytest-xdist live rendering, message order MUST be preserved within each worker stream, while inter-worker rendering MAY follow controller arrival order instead of delaying output to reconstruct final canonical NDJSON order.

### Key Entities

- **Formatter Flag**: A pytest CLI option (e.g. `--cucumber-junit`) corresponding to a specific cucumber formatter.
- **Underlying Node.js Process**: The Node.js worker/process that reads the NDJSON stream and runs the corresponding `@cucumber/*` formatter.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can generate reports for all 10 standard cucumber-js formatters directly via pytest command-line flags.
- **SC-002**: 100% of generated file reports (JSON, JUnit, Usage-JSON) successfully parse with standard tools designed for those formats.
- **SC-003**: If tests are distributed across workers (e.g., with pytest-xdist), all requested outputs correctly reflect the consolidated suite execution.
- **SC-004**: For at least one stream-capable terminal formatter, visible terminal output appears before session finish in both single-process and pytest-xdist runs.
- **SC-005**: Under pytest-xdist live terminal rendering, acceptance tests confirm per-worker order preservation and confirm that cross-worker output is emitted without waiting for global post-run reordering.
