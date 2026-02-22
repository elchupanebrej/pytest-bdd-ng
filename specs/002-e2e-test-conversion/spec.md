<!-- markdownlint-disable MD013 -->

# Feature Specification: E2E Test Conversion to Feature Documentation

**Feature Branch**: `002-e2e-test-conversion`
**Created**: 2026-02-22
**Status**: Draft
**Input**: Split from `001-add-py314-pytest39-support` to isolate E2E conversion work

## Clarifications

### Session 2026-02-22

- Q: Should E2E conversion stay in compatibility spec? → A: No, it is a separate feature and must be tracked in a separate spec
- Q: Should converted tests preserve original intent? → A: Yes, intent parity is mandatory while keeping docs user-friendly
- Q: Should fixes rewrite history? → A: No, fixes must be follow-up commits

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Learn usage from feature docs (Priority: P1)

As a library user, I can read and run documentation-oriented feature files for end-to-end behavior so I do not need to inspect low-level pytest modules to understand usage.

**Independent Test**: Run converted scenarios from `features/` and verify behavior/intent is explicit and runnable.

**Acceptance Scenarios**:

1. **Given** a user-facing E2E behavior currently covered in pytest tests, **When** conversion is completed, **Then** equivalent behavior is represented in a `features/*.feature*` file.
2. **Given** converted feature documentation, **When** a user reads it, **Then** what is validated and why is explicit without referencing deleted source tests.

---

### User Story 2 - Preserve technical coverage boundaries (Priority: P2)

As a maintainer, I can keep technical/regression-heavy scenarios in pytest tests when they are not suitable as documentation-first scenarios.

**Independent Test**: Validate retained technical tests still run in `tests/` and are tagged/classified to prevent accidental future deletion.

**Acceptance Scenarios**:

1. **Given** a technical test that validates internal mechanics, **When** conversion is assessed, **Then** it remains in `tests/` with a clear non-convertible classification.
2. **Given** a converted user-facing scenario, **When** cleanup is performed, **Then** only duplicate pytest versions are removed.

---

### User Story 3 - Audit conversion parity per commit (Priority: P2)

As a reviewer, I can audit each conversion commit and its fix commit as a pair so conversion quality is traceable and noise in history is reduced.

**Independent Test**: For each converted test, parity audit records source, converted file, verdict, and follow-up commit.

**Acceptance Scenarios**:

1. **Given** a conversion commit, **When** parity audit runs, **Then** it records intent match, assertion quality, and clarity checks.
2. **Given** a failed parity check, **When** remediation is applied, **Then** remediation lands in a new commit and audit status is updated.

### Edge Cases

- Mixed tests containing both user-facing and low-level assertions must be split: user-facing part in `features/`, low-level part remains in `tests/`.
- Converted docs must not link to test files that are expected to be deleted.
- Auto-discovery/autoload behavior must be preserved; conversions must not rely on duplicated manual runs to pass.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: User-facing E2E scenarios MUST be represented in `features/` as executable documentation.
- **FR-002**: Technical/regression-heavy scenarios MUST remain in `tests/` and be explicitly marked with `@pytest.mark.e2e_retain_technical`.
- **FR-003**: Converted scenarios MUST preserve the original test intent and include explicit assertions, not only "no exception" checks.
- **FR-004**: Converted feature files MUST include a clear description of what is tested and why.
- **FR-005**: Converted feature files MUST NOT depend on links to source pytest files that are deleted.
- **FR-006**: Duplicate pytest tests MAY be removed only when converted coverage is verified as parity-complete.
- **FR-007**: Every conversion task MUST have an audit entry mapping source test, converted file, verdict, and remediation commit.
- **FR-008**: Conversion fixes MUST be delivered in follow-up commits; no history rewrite for parity remediation.
- **FR-009**: Conversion classification MUST use canonical pytest markers `@pytest.mark.e2e_convert_candidate` and `@pytest.mark.e2e_retain_technical`, and those markers MUST be registered in `pytest.ini`.

### Key Entities

- **ConversionCandidate**: Source pytest test evaluated for conversion with priority and convertibility reason.
- **ConvertedScenario**: Feature file scenario created from candidate test with intent/assertion mapping.
- **ParityAuditEntry**: Record that links source test, converted file, verdict, and fix commit.
- **RetentionMarker**: Canonical pytest marker `@pytest.mark.e2e_retain_technical` for tests intentionally kept in pytest form.

### Assumptions

- Project documentation is primarily feature-file based.
- Not all tests are suitable for conversion; technical coverage must remain in pytest where appropriate.
- Commit-level traceability is required for conversion quality control.

### Dependencies

- Stable E2E harness in `tests/e2e/` for executing converted scenarios.
- Markdown lint and test tooling for validating converted docs.

### Retention Marker Policy

- `@pytest.mark.e2e_convert_candidate`: marks tests eligible for conversion to feature-based E2E documentation.
- `@pytest.mark.e2e_retain_technical`: marks tests that remain technical/non-convertible and must not be deleted during conversion cleanup.
- Marker registration in `pytest.ini` is mandatory to keep marker usage explicit and lint-clean.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: At least 80% of tests marked `@pytest.mark.e2e_convert_candidate` in `specs/002-e2e-test-conversion/e2e-migration-inventory.md` are represented in runnable `features/*.feature.md` scenarios.
- **SC-002**: 100% of converted scenarios have parity audit entries with explicit verdicts.
- **SC-003**: 100% of retained technical tests include a non-convertible classification marker.
- **SC-004**: 100% of conversion-related fix actions are delivered as follow-up commits linked from audit records.
