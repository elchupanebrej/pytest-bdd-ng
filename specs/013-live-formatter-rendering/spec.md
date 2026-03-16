# Feature Specification: Live Formatter Rendering

**Feature Branch**: `013-live-formatter-rendering`  
**Created**: 2026-03-10  
**Status**: Draft  
**Input**: User description: "Formatters must use live incremental rendering: they has to consume stream of messages during run (and can report by their own approach). messages must be streamed to main thread during xdist run. only master thread uses formatter for messages reporting"

## Clarifications

### Session 2026-03-12

- Q: Where must shared test utility functions introduced by this feature live? → A: Cross-layer reusable utilities must move to shared product utility packages, while pure test-only helpers must move to shared test-support packages rather than staying inside individual test modules.
- Q: How must the live formatter reporting implementation be decomposed? → A: The reporting implementation must be split into separate plugin modules so message-stream handling is isolated from reporter-specific rendering, with separate reporter plugins for each supported formatter.
- Q: When may generated helper scripts remain inline in Python string literals? → A: Inline scripts are allowed only when they stay under 20 lines; anything longer must be moved into repository resources or templates and rendered from those assets.
- Q: How must the split reporter modules integrate with pytest? → A: Reporter modules must be implemented as real pytest or pluggy plugins that participate through hook registration rather than acting only as plain helper modules invoked by custom registries.
- Q: How must shared reporter state be scoped? → A: Live-reporting state must be kept in plugin, session, request, or config-owned objects rather than mutable module-level globals, and uppercase module-level names are reserved for true immutable constants only.

### Session 2026-03-14

- Q: How must the reporter root object be bounded after the live-reporting split? → A: The main reporter object must stop acting as an oversized aggregate root; service-graph assembly, formatter request resolution, xdist role decisions, and live-output or Node-runtime preparation must move into dedicated collaborators with narrower ownership boundaries.
- Q: How must the entrypoint interact with the reporter instance? → A: The entrypoint must use one explicit public lifecycle contract for reporter setup and teardown and must not fall back to duck-typed access to private reporter attributes or private methods.
- Q: How must runtime services depend on one another? → A: Runtime services must declare only explicit narrow collaborator dependencies and must not reach sibling services through reporter-backed service-locator accessors.
- Q: How must standalone formatter replay integrate with the reporting runtime? → A: Standalone replay must use a first-class application service boundary rather than constructing synthetic pytest Config or pluginmanager objects to mimic an in-process pytest runtime.
- Q: How must formatter plugins own their behavior? → A: Formatter plugins must own their request-building and runtime-asset behavior through their own plugin modules or dedicated collaborators rather than acting mainly as declarative wrappers over one shared monolithic base implementation.
- Q: How must formatter discovery be governed? → A: Formatter discovery must use one canonical source of truth per execution mode, and package-scan fallback must not remain as a second discovery policy for supported runtime paths that already rely on pytest11 or hook-based discovery.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - See live formatter updates during a run (Priority: P1)

Users should be able to watch formatter output appear while a test session is still running, rather than waiting until the run has already finished.

**Why this priority**: Live visibility is the core value of the feature because it lets users monitor progress, failures, and summary signals while work is still in flight.

**Independent Test**: Start a long-running test session with a supported formatter and confirm that visible formatter output appears before the session completes while the final reported results still match the completed run.

**Acceptance Scenarios**:

1. **Given** a test session that takes long enough to observe progress, **When** the user starts the run with a live-capable formatter enabled, **Then** the formatter begins presenting incremental output before the session completes.
2. **Given** a formatter that naturally shows most of its information near the end of a run, **When** the user starts a test session, **Then** that formatter still consumes the live execution stream used by other formatters and does not switch to a separate after-run reporting mode.

---

### User Story 2 - Keep distributed live reporting centralized (Priority: P2)

Users running tests across multiple workers should see one coherent live formatter stream produced by a single reporting authority, even though execution messages originate from many workers.

**Why this priority**: Distributed execution must remain understandable and trustworthy; duplicated or competing formatter output from workers would make live reporting noisy and unreliable.

**Independent Test**: Start a distributed multi-worker run with a live-capable formatter and confirm that worker messages are relayed to one reporting authority, only that authority renders formatter output, and the final output remains complete and non-duplicated.

**Acceptance Scenarios**:

1. **Given** a distributed test session with multiple workers, **When** workers produce execution messages, **Then** those messages are relayed to a single central reporting authority for live formatter rendering.
2. **Given** a distributed test session with multiple workers, **When** live formatter output is displayed, **Then** worker processes do not emit their own formatter rendering and users see one consolidated live stream.

### Edge Cases

- What happens when execution messages arrive in bursts during a long-running session?
- What happens when a distributed worker is delayed or disconnects after some live messages have already been shown?
- How does the system handle a formatter that emits little visible output until late in the run while still consuming the live stream?
- How does the system prevent duplicate formatter output when the same execution event passes through distributed reporting paths?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST deliver execution messages to active formatters incrementally during a test run instead of waiting for run completion.
- **FR-002**: Users MUST be able to observe formatter output during the run whenever the selected formatter chooses to emit output from the live stream.
- **FR-003**: System MUST preserve message order within each execution source when delivering live messages to formatters.
- **FR-004**: During distributed multi-worker execution, system MUST relay worker-generated execution messages to a single central reporting authority before formatter output is rendered.
- **FR-005**: During distributed multi-worker execution, worker processes MUST NOT render formatter output directly.
- **FR-006**: During distributed multi-worker execution, the single central reporting authority MUST use the live message stream as the only source for formatter rendering.
- **FR-007**: System MUST keep final formatter results consistent with the completed test run after live rendering has occurred.
- **FR-008**: System MUST prevent duplicate formatter output for the same execution event during distributed runs.
- **FR-009**: System MUST present an actionable error when live message delivery is interrupted or cannot be completed reliably.
- **FR-010**: Formatters that naturally show most information late in the run MUST still consume the same live message stream used by other formatters.
- **FR-011**: Shared utility functions introduced to support this feature MUST NOT remain inside individual test modules. Utilities reused across runtime and tests MUST be extracted into shared product utility packages, while pure test-only helpers MUST be extracted into shared test-support packages.
- **FR-012**: The live formatter reporting implementation MUST be decomposed into separate plugin modules so message-stream handling is isolated from reporter-specific rendering, and each supported formatter is implemented through its own reporter plugin module rather than accumulating formatter-specific logic in one growing plugin file.
- **FR-013**: Generated helper scripts MAY remain inline in Python string literals only when they are shorter than 20 lines. Longer generated scripts MUST be stored in repository resources or templates and rendered from those assets at runtime.
- **FR-014**: Reporter-specific modules created for this feature MUST be implemented as real pytest or pluggy plugins that participate through hook registration, lifecycle callbacks, and plugin discovery rather than acting only as helper classes or registry entries invoked outside the hook system.
- **FR-015**: Live-reporting runtime state MUST be scoped to plugin instances or pytest-owned session, config, or request objects. Mutable module-level global variables MUST NOT be used for reporter coordination, and uppercase module-level names MUST be limited to immutable constants with protocol or configuration significance.
- **FR-016**: The main live-reporting reporter object MUST be reduced to a narrow coordination boundary. Formatter request resolution, service-graph assembly, xdist role selection, and live-output or Node-runtime preparation MUST be delegated to dedicated collaborators instead of accumulating in one aggregate root class.
- **FR-017**: The reporter entrypoint MUST configure and unconfigure the reporting runtime through one explicit public lifecycle contract. Entry-point code MUST NOT fall back to duck typing against private reporter methods, private reporter attributes, or compatibility branches for partially structured reporter objects.
- **FR-018**: Runtime services introduced for live reporting MUST declare explicit narrow collaborator dependencies. A service MUST NOT access sibling services through reporter-backed service-locator accessors when the dependency can be injected or passed directly.
- **FR-019**: Standalone formatter replay MUST be implemented through a first-class application service boundary. Supported standalone rendering flows MUST NOT depend on synthetic pytest `Config` objects, `SimpleNamespace` stand-ins, or ad hoc pytest pluginmanager construction that only imitates the in-process pytest runtime.
- **FR-020**: Each supported formatter plugin MUST own its formatter-specific request-building and runtime-asset behavior through its plugin module or formatter-specific collaborators. Shared formatter base layers MAY provide reusable primitives, but they MUST NOT remain the primary home of formatter-specific behavior for most plugins.
- **FR-021**: Formatter discovery MUST use one canonical source of truth per execution mode. For supported runtime paths that already depend on pytest11 or hook-based discovery, package scanning MUST NOT remain as a second discovery mechanism for the same formatter inventory.

### Assumptions

- Existing formatter selection behavior remains available; this feature changes when formatter output is rendered and which reporting authority is allowed to render it during distributed runs.
- Distributed execution already provides a coordinating authority that can receive worker-generated execution messages.
- Users rely on live formatter output for situational awareness during execution, but they still expect the final reported results to reflect the completed run accurately.

### Key Entities *(include if feature involves data)*

- **Execution Message**: A single reportable event created while tests are running, such as progress, outcome, or summary input.
- **Live Formatter Output**: User-visible reporting generated incrementally from execution messages before the run completes.
- **Central Reporting Authority**: The single coordinating authority responsible for rendering formatter output during distributed runs.
- **Standalone Formatter Rendering Service**: The first-class application boundary that replays canonical NDJSON envelopes into formatter outputs outside a live pytest session.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: In validation runs lasting at least 30 seconds, users see the first formatter output before 25% of total run time has elapsed.
- **SC-002**: In 100% of validated distributed runs, formatter output is emitted by one reporting authority only.
- **SC-003**: In 100% of validated standard and distributed runs, final formatter results match completed run outcomes with no missing or duplicate reported events.
- **SC-004**: At least 95% of validation runs intended to demonstrate live reporting show visible formatter activity before run completion.
- **SC-005**: In 100% of validated distributed runs, users do not observe out-of-order updates within the event stream from a single execution source.
