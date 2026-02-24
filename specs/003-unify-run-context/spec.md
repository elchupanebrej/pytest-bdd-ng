<!-- markdownlint-disable MD013 -->

# Feature Specification: Unified Test Run Context Model

**Feature Branch**: `003-unify-run-context`
**Created**: 2026-02-24
**Status**: Draft
**Input**: User description (translated to English): "The current Cucumber test-run execution model is fragmented and often passed indirectly. I need all hook parameters to reference a shared execution model that includes all test-run execution objects and tracks which objects are currently active (execution context tracking)."

## Clarifications

### Session 2026-02-24

- Q: What language must be used for specifications? → A: Specifications must be written in English only.
- Q: How much may the current external API change? → A: External API changes must be minimal and backward compatible; no removals/renames, and any additions must be non-breaking.
- Q: How should hooks receive execution context data? → A: `execution_context` must be a field/reference inside existing hook parameter models, not a separate hook argument.
- Q: What is the required context scope model? → A: Use one session-level root execution context with hierarchical child contexts for feature/scenario/step nodes.
- Q: How much of `gherkin_document` should be refactored for context support? → A: Perform a broad refactor of `src/pytest_bdd/model/gherkin_document.py` into multiple modules to support shared context modeling.
- Q: When should `SessionExecutionContext` be created and exposed? → A: Create it at `pytest_sessionstart`, store it in `pytest.config.stash`, expose it as a session-scoped fixture, and keep it available from `pytest_bdd_before_scenario` onward.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Access Shared Context In Hooks (Priority: P1)

As a maintainer writing or reviewing hook behavior, I can access one shared execution context from every hook parameter so I do not depend on indirect state passing.

**Why this priority**: This is the core outcome: hooks must become deterministic and easier to reason about.

**Independent Test**: Trigger the supported hook lifecycle and verify each hook parameter can resolve the same current execution context and see consistent active objects.

**Acceptance Scenarios**:

1. **Given** a running BDD test flow with active run, feature, scenario, and step objects, **When** any supported hook receives parameters, **Then** each parameter can reach the same shared execution context.
2. **Given** multiple hook invocations within one scenario, **When** hook parameters access context repeatedly, **Then** they observe the same active-object state for that point in lifecycle.
3. **Given** early lifecycle hook execution starting at `pytest_bdd_before_scenario`, **When** hooks and fixtures resolve session context, **Then** they receive the same `SessionExecutionContext` instance from fixture injection and `pytest.config.stash`.

---

### User Story 2 - Track Active Lifecycle Objects (Priority: P2)

As a maintainer, I can rely on the shared execution context to track which test-run objects are currently active at each lifecycle stage.

**Why this priority**: Correct active-object tracking prevents cross-scenario leakage and lifecycle confusion.

**Independent Test**: Execute a suite with multiple features and scenarios and verify active-object transitions are correct before, during, and after each lifecycle boundary.

**Acceptance Scenarios**:

1. **Given** a transition from one scenario to another, **When** hooks query the shared context, **Then** inactive previous objects are not reported as active.
2. **Given** a failed step or interrupted scenario, **When** after-hooks run, **Then** the shared context still reports a valid active-object state for cleanup and reporting.

---

### User Story 3 - Provide Clear Context For Diagnostics (Priority: P3)

As a maintainer, I receive clear context behavior when requested objects are unavailable so debugging hook logic is fast and predictable.

**Why this priority**: Better diagnostics reduce time spent investigating context-related test failures.

**Independent Test**: Simulate lifecycle points where some objects are intentionally inactive and verify context access yields explicit, predictable outcomes.

**Acceptance Scenarios**:

1. **Given** a hook asks for a lifecycle object that is not active, **When** context access is evaluated, **Then** the system returns a clear and consistent unavailable-state result.
2. **Given** context-dependent hook logic fails, **When** maintainers inspect failure details, **Then** they can identify which lifecycle objects were active at that moment.

### Edge Cases

- Hook parameters are accessed before the first scenario starts.
- Hook parameters are accessed after scenario teardown completes.
- Nested or repeated hooks request context concurrently within one scenario lifecycle point.
- Lifecycle ends early because of failure or interruption, and context must remain internally consistent.
- Background/setup sections run without a regular step sequence.
- Reporting callbacks run when no step is active and must still resolve session-level context from hierarchy/stash.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST provide a session-level root execution context for the active BDD test run, with hierarchical child contexts for feature, scenario, and step scopes.
- **FR-002**: System MUST expose `execution_context` as a field/reference on existing hook parameter models, not as a separate top-level hook argument.
- **FR-003**: System MUST include all core test-run lifecycle objects in the shared context model.
- **FR-004**: System MUST track which lifecycle objects are currently active at any hook execution point.
- **FR-005**: System MUST keep child-context active-object tracking isolated between separate scenarios and features while preserving visibility through the same session root context.
- **FR-006**: System MUST update active-object state at each lifecycle transition in deterministic order.
- **FR-007**: System MUST provide a consistent outcome when a requested lifecycle object is not active.
- **FR-008**: System MUST keep context state coherent when execution is interrupted by failures.
- **FR-009**: System MUST allow hooks to read active context without requiring implicit global state assumptions.
- **FR-010**: System MUST preserve current observable hook behavior for flows not affected by context access.
- **FR-011**: System MUST keep existing public hook/plugin APIs backward compatible, with no required caller-side changes for currently supported usage patterns.
- **FR-012**: System MUST restrict external API evolution in this feature to additive, non-breaking extensions only.
- **FR-013**: System MUST broadly refactor `src/pytest_bdd/model/gherkin_document.py` into multiple cohesive modules so context-related models can be reused by the session-root and child-context hierarchy.
- **FR-014**: System MUST create `SessionExecutionContext` at `pytest_sessionstart` and expose it as a session-scoped fixture for early runtime stages.
- **FR-015**: System MUST store the canonical `SessionExecutionContext` in `pytest.config.stash` and keep fixture and stash references consistent for the same test session.
- **FR-016**: System MUST use the context hierarchy as the primary source for reporting flows where lifecycle context is available, with graceful fallback when a specific object scope is inactive.

### Key Entities *(include if feature involves data)*

- **Shared Execution Context**: Canonical model that represents current test-run state and lifecycle visibility.
- **Session Root Context**: The root execution context created once per test session and used to anchor all child contexts.
- **Lifecycle Object**: A runtime object participating in BDD execution (for example run, feature, scenario, step).
- **Active Object Set**: Snapshot of lifecycle objects currently valid for a specific hook execution point.
- **Hook Invocation Context**: The effective context view seen from a specific hook call.

## Assumptions

- Existing hook types remain supported and continue to execute in the same lifecycle order.
- Teams rely on hook parameters as the primary extension point for test-run behavior.
- Context consumers need deterministic read access, not custom lifecycle mutation controls.
- Specification artifacts for this feature are maintained in English only.
- Existing integrations using current public APIs must continue to run without mandatory code changes.
- Broad refactoring of `gherkin_document` can be delivered without breaking existing public APIs.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of supported hook entry points can access the shared execution context through existing hook parameter models.
- **SC-002**: In acceptance tests covering lifecycle transitions, active-object state matches expected lifecycle stage in 100% of cases.
- **SC-003**: In multi-scenario validation runs, zero cross-scenario active-object leaks are observed.
- **SC-004**: Context-related hook failures provide enough active-state detail for maintainers to identify root cause within one inspection cycle.
- **SC-005**: Compatibility validation demonstrates zero required changes for existing public API consumers in covered integration suites.
- **SC-006**: In covered reporting integration tests, context-aware reporting paths resolve lifecycle state from the hierarchy/stash in 100% of validated events.
