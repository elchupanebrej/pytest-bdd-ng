<!-- markdownlint-disable MD013 -->

# Feature Specification: Strict Non-Null Lifecycle Refactoring

**Feature Branch**: `016-strict-non-null`
**Created**: 2026-03-18
**Status**: Draft
**Input**: User description: "Мы не должны использовать Optional[Type] обьекты. Хочу рефакторинг который после которого практически не будет проверок на None. В исключительный случаях можно приметнить EmptyObject паттерн. Все места где есть какой-либо lifecycle, включающий пустые обьекты - должны быть гарантирующие инварианты, что обьект не пустой и что проверка на None не нужна"

## Clarifications

### Session 2026-03-19

- Q: How must inactive lifecycle-managed objects be represented and validated in covered flows? → A: In-scope lifecycle access must return either a populated object or a dedicated Empty-State Object; lifecycle invariant enforcement must be centralized at the lifecycle boundary rather than repeated as inline `None` checks inside consumer methods.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Safe Lifecycle Access (Priority: P1)

As a maintainer changing runtime flows, I need lifecycle-bound objects to be present whenever the lifecycle says they are available, so I can extend behavior without first defending every access against missing state.

**Why this priority**: This is the core value of the refactoring. If normal lifecycle access still depends on absence checks, the feature fails its main goal.

**Independent Test**: Can be fully tested by exercising a primary lifecycle from creation through consumption and confirming that consumers use the object directly without branching on missing state.

**Acceptance Scenarios**:

1. **Given** a lifecycle stage where a runtime object is declared available, **When** a maintainer reads or passes that object to downstream logic, **Then** the object is always present and no caller-side absence guard is required.
2. **Given** a lifecycle transition that activates a previously unavailable object, **When** the transition completes, **Then** all subsequent lifecycle steps receive a valid object that satisfies the documented contract.

---

### User Story 2 - Explicit Empty-State Exceptions (Priority: P2)

As a maintainer handling exceptional flows, I need any intentionally empty lifecycle state to be represented explicitly and consistently, so exceptional behavior is visible without spreading absence checks through normal code paths.

**Why this priority**: The user explicitly allows empty objects only as exceptions. Those exceptions must stay deliberate and bounded instead of becoming a back door for nullable state.

**Independent Test**: Can be fully tested by exercising a documented exceptional lifecycle path and confirming that consumers interact with an explicit empty-state object through the same contract as the populated object.

**Acceptance Scenarios**:

1. **Given** a lifecycle path where no populated object can exist by design, **When** the empty-state representation is provided, **Then** downstream logic can continue through the shared contract without checking for missing state.
2. **Given** an empty-state representation is used, **When** a consumer requests behavior that requires populated data, **Then** the system responds with the documented empty-state behavior instead of exposing missing state to the caller.
3. **Given** an empty-state representation is used, **When** downstream logic reads the fields or behaviors required by that exceptional flow, **Then** it can do so through the same contract subset used for the populated object.

---

### User Story 3 - Enforced Lifecycle Invariants (Priority: P3)

As a reviewer or contributor, I need lifecycle rules to make object availability obvious, so I can identify invalid states early and reject changes that reintroduce nullable lifecycle handling.

**Why this priority**: Sustaining the refactoring requires explicit invariants. Without them, the codebase will drift back to defensive null handling over time.

**Independent Test**: Can be fully tested by inspecting a lifecycle boundary, verifying the documented invariant for object availability, and confirming that invalid transitions fail immediately instead of leaking missing state further downstream.

**Acceptance Scenarios**:

1. **Given** a lifecycle boundary that promises a populated object, **When** that boundary is entered without a valid object, **Then** the system rejects the transition with a deterministic failure rather than continuing with missing state.
2. **Given** a lifecycle boundary promises a reusable contract, **When** a consumer method executes behind that boundary, **Then** the method does not need to repeat inline absence checks for the same invariant.
3. **Given** a change introduces a new lifecycle stage, **When** the stage is reviewed against the documented invariants, **Then** object availability and any allowed empty-state behavior are explicit and testable.

### Edge Cases

- What happens when a caller reaches a lifecycle boundary before the object has been activated? The boundary must reject the transition immediately rather than returning missing state.
- How does the system handle flows where a populated object can never exist? The lifecycle must use an explicit empty-state object that preserves the shared contract and documents the restricted behavior.
- What happens when a lifecycle-managed accessor is invoked while its slot is inactive? The accessor must return the documented empty-state object only for semantically valid exceptional flows; otherwise the boundary must fail deterministically instead of returning `None`.
- What happens when a lifecycle is re-entered or advanced out of order? The system must preserve the same object-availability guarantees and fail deterministically if the invariant cannot be satisfied.
- How does the system handle external or historical data that can legitimately omit values? Those omissions remain outside this feature unless they participate in an internal lifecycle that promises object availability.
- How does the system allow shared code paths between populated and empty states? Approved empty-state objects must preserve the required consumer-facing subset of fields and behaviors so in-scope code can stay polymorphic.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST treat routine lifecycle-bound object access as non-empty once the lifecycle declares the object available.
- **FR-002**: The system MUST remove routine caller-side absence branching from in-scope lifecycle flows and replace it with lifecycle guarantees.
- **FR-003**: The system MUST define, for each in-scope lifecycle boundary, when the object becomes available, when it may be consumed, and when the lifecycle must reject further use.
- **FR-004**: The system MUST fail deterministically at the lifecycle boundary whenever a required object cannot be provided for a stage that promises object availability.
- **FR-005**: The system MUST allow an explicit empty-state object only for exceptional lifecycle paths where the absence of populated data is semantically valid.
- **FR-006**: The system MUST ensure that any approved empty-state object follows the same interaction contract subset as its populated counterpart so downstream consumers do not branch on missing state.
- **FR-007**: The system MUST document which lifecycle flows are in scope for strict non-empty guarantees and which flows remain outside scope because they represent external, optional, or historical data rather than internal lifecycle state.
- **FR-008**: The system MUST preserve existing observable behavior for successful populated-object flows while improving predictability of invalid-state failures.
- **FR-009**: The system MUST provide acceptance coverage for each in-scope lifecycle showing either direct populated-object access or an explicit empty-state object, with no caller-visible missing-state handling.
- **FR-010**: The system MUST NOT return `None` from an in-scope lifecycle accessor to represent an inactive lifecycle-managed object; it must return a populated object, an approved empty-state object, or a deterministic boundary failure.
- **FR-011**: The system MUST define and document a dedicated empty-state object for each lifecycle-managed type whose inactive-by-design state is in scope, rather than using generic missing-state values.
- **FR-012**: The system MUST centralize lifecycle invariant enforcement at the lifecycle boundary through a reusable guard mechanism so consumer methods do not re-implement the same absence check inline.
- **FR-013**: Approved empty-state objects MUST preserve the fields and behaviors required by their covered consumers so shared code paths can interact with populated and empty states polymorphically.

### Key Entities *(include if feature involves data)*

- **Lifecycle-Bound Object**: A domain object that is created, activated, consumed, and retired through an explicit lifecycle and is expected to be present once its lifecycle stage is reached.
- **Lifecycle Boundary**: A creation, transition, or consumption point where the system must guarantee object availability or reject the flow immediately.
- **Empty-State Object**: A dedicated explicit representation for an exceptional lifecycle path where populated data is intentionally unavailable but the required subset of the interaction contract must remain stable.
- **Lifecycle Guard**: A reusable lifecycle-boundary mechanism that decides whether a covered access path receives a populated object, an approved empty-state object, or a deterministic rejection before consumer logic executes.
- **Lifecycle Invariant**: A rule describing whether an object must exist, may not be used, or may be represented by an approved empty-state object at a specific lifecycle stage, and that rule must be enforced consistently at the boundary.

### Assumptions

- This refactoring targets internal lifecycle-managed objects first, because those are the places where nullable handling creates avoidable complexity and ambiguity.
- Legitimate optional data coming from user input, external contracts, or historical payloads is out of scope unless the system converts it into an internal lifecycle-managed object with stronger guarantees.
- Existing consumers are expected to keep their observable successful behavior after the refactoring, apart from no longer needing routine absence checks in the covered flows.
- Exceptional empty-state behavior is expected to be rare, explicitly documented, and reviewable as an exception rather than a default modeling choice.
- In-scope lifecycle accessors are allowed to reject invalid boundary entry, but they are not allowed to encode covered inactive lifecycle state as `None`.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: At least 90% of in-scope lifecycle interaction points can be exercised in acceptance coverage without caller-side missing-state checks.
- **SC-002**: 100% of in-scope lifecycle boundaries document whether they guarantee a populated object, reject the transition, or allow an explicit empty-state object.
- **SC-003**: 100% of approved empty-state scenarios are explicitly identified, and each is verifiable through acceptance coverage that uses the shared contract rather than caller-side absence branching.
- **SC-004**: Reviewers can determine the expected object availability for any in-scope lifecycle flow from the specification and acceptance scenarios without inferring hidden nullable behavior.
- **SC-005**: 100% of in-scope lifecycle accessors verified by acceptance coverage expose either a populated object, an approved explicit empty-state object, or a deterministic boundary failure; none expose missing state as the consumer contract.
