<!-- markdownlint-disable MD013 -->

# Feature Specification: Python and Pytest Compatibility Alignment

**Feature Branch**: `001-add-py314-pytest39-support`
**Created**: 2026-02-20
**Status**: Draft
**Input**: User description: "I need support of python 3.14 and pytest 3.9 in the project"

## Clarifications

### Session 2026-02-20

- Q: Should support be limited to specific Python/pytest versions or follow broader compatibility rules? → A: Follow pytest compatibility matrix
- Q: Should automated validation cover all compatible pairs or only a representative subset? → A: Cover all compatible pairs
- Q: Should all currently uncommitted files be included in this feature scope? → A: Include every currently uncommitted file

### Session 2026-02-22

- Q: Should Python/pytest compatibility work and end-to-end test conversion remain in one spec? → A: No; keep compatibility in this spec and move end-to-end conversion to a separate spec
- Q: How should Python 3.9 and pytest<6.2.5 be treated after EOL? → A: Treat Python 3.9 and pytest<6.2.5 as explicitly unsupported: fail fast with clear messaging, remove from CI/tox/docs
- Q: What is the new supported Python range? → A: 3.10-3.14
- Q: How should this change be scoped in the specification? → A: Keep this in current spec and add explicit deprecation scope section (EOL removal + compatibility floor)
- Q: How should automated validation be scoped after deprecating EOL versions? → A: Execute CI/tests only for supported pairs (Python 3.10-3.14, pytest>=6.2.5), and add explicit negative checks for unsupported EOL pairs
- Q: How should the non-repo support-ticket success criterion be handled? → A: Replace it with a repo-verifiable metric based on documented compatibility command validation in CI

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Run tests on compatible versions (Priority: P1)

As a project maintainer, I can execute the project test suite successfully across Python and pytest version combinations that are compatible per pytest's compatibility rules so that project support is not artificially restricted by this library.

**Why this priority**: This is the core requested capability and directly determines whether users on the target versions can use the project.

**Independent Test**: Can be fully tested by running the standard project test command matrix across selected compatible Python and pytest combinations and confirming the suite completes without library-imposed version-cap errors.

**Acceptance Scenarios**:

1. **Given** the project is checked out with dependencies installed, **When** maintainers run tests in a Python plus pytest combination supported by pytest's compatibility rules, **Then** tests execute without compatibility errors caused by library-imposed version caps.
2. **Given** the project's declared support rules, **When** contributors inspect documentation, **Then** it states that supported combinations follow pytest compatibility constraints rather than project-specific version pinning by default.

---

### User Story 2 - Validate compatibility in CI matrix (Priority: P2)

As a release manager, I can verify that automated validation covers all Python and pytest combinations allowed by the pytest compatibility matrix so regressions are detected before release.

**Why this priority**: Automated verification prevents accidental breakage after compatibility is introduced.

**Independent Test**: Can be tested by running configured matrix jobs across all pytest-compatible pairs and confirming those jobs produce pass/fail results rather than being skipped or undefined.

**Acceptance Scenarios**:

1. **Given** the automated validation matrix configuration, **When** the matrix is executed, **Then** it includes jobs for every pytest-compatible Python/pytest pair and reports explicit results.

---

### User Story 3 - Keep existing supported versions stable (Priority: P3)

As a maintainer, I can add support for the new versions without unintentionally removing or degrading existing supported version combinations.

**Why this priority**: Backward compatibility protects current users and lowers release risk.

**Independent Test**: Can be tested by running representative existing supported-version jobs before and after this feature and confirming no new compatibility regressions attributable to this change.

**Acceptance Scenarios**:

1. **Given** existing supported runtime/test-runner combinations, **When** the compatibility update is applied, **Then** those existing combinations remain runnable with no new version-gating failures introduced by this feature.

---

### Out of Scope

- Converting existing tests from `tests/` into documentation-style `features/` files is explicitly out of scope for this specification.
- Any migration of end-to-end scenarios into `features/` MUST be implemented in a separate feature specification and branch.

### Deprecation Scope

- Python 3.9 is deprecated and out of support for this feature because it has reached EOL.
- pytest versions lower than 6.2.5 are deprecated and out of support for this feature because they are EOL.
- Unsupported combinations MUST fail fast with clear actionable guidance.
- CI, tox environments, and contributor-facing documentation MUST exclude deprecated combinations.

### Edge Cases

- What happens when a requested Python and pytest pair is not a compatible pair according to pytest constraints? The project must provide a clear compatibility outcome and fail with actionable messaging.
- What happens when a requested pair is compatible in theory but unavailable from package sources in the execution environment? The project must provide explicit failure guidance.
- How does the system handle deprecated behavior differences between target and previously supported versions? Compatibility expectations must remain deterministic and documented.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The project MUST define support policy as Python/pytest combinations that are compatible per pytest's compatibility matrix, bounded by explicit EOL support floors in this specification.
- **FR-002**: The project MUST NOT impose additional library-specific version restrictions that exclude otherwise pytest-compatible Python/pytest pairs above the declared support floors.
- **FR-003**: The project MUST provide automated validation for every supported Python/pytest pair (Python 3.10-3.14 with pytest>=6.2.5), and explicit negative validation for deprecated EOL pairs.
- **FR-004**: The project MUST ensure version-selection configuration allows contributors to intentionally run checks for any requested pytest-compatible Python/pytest pair.
- **FR-005**: The project MUST keep existing documented supported combinations valid unless explicitly deprecated in this feature scope.
- **FR-006**: The project MUST expose clear failure messaging when a requested compatibility combination is unavailable or unsupported in a given environment, including explicit EOL reasons for Python 3.9 and pytest<6.2.5.
- **FR-007**: The project MUST update contributor-facing documentation to state support policy, compatibility source of truth, and expected validation commands.
- **FR-008**: The feature scope MUST include all currently uncommitted files in this branch, including implementation code, tests, workflows, ignore/configuration files, and specification artifacts required to deliver and validate this feature.
- **FR-009**: The supported Python range for this feature MUST be 3.10 through 3.14.
- **FR-010**: The minimum supported pytest version for this feature MUST be 6.2.5.
- **FR-011**: CI and tox configuration MUST exclude Python 3.9 and pytest<6.2.5 environments.
- **FR-012**: The test suite MUST include explicit negative checks proving unsupported EOL combinations fail fast with actionable diagnostics.

### Key Entities *(include if feature involves data)*

- **Compatibility Matrix Entry**: A defined support tuple that includes runtime version, test framework version, compatibility status based on pytest rules, and validation context.
- **Validation Job**: An executable verification unit that maps to one or more compatibility matrix entries and reports pass/fail status.
- **Support Declaration**: Contributor-facing project metadata and documentation that communicate officially supported versions.

### Assumptions

- Support policy is driven by pytest compatibility constraints instead of hard-coding a single pytest or Python version target.
- Existing supported versions remain in scope unless they are separately deprecated in a future request.
- "Support" means documented compatibility plus automated validation coverage, not only local ad-hoc execution.
- All currently uncommitted files in this branch are treated as intentional deliverables for this feature.
- Python 3.9 and pytest<6.2.5 are intentionally removed from support due to EOL.

### Dependencies

- Availability of requested Python runtimes in the project validation environment.
- Availability of requested pytest versions from accepted package sources.
- Access to automated validation infrastructure where matrix entries are executed.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of validation runs for all supported Python/pytest pairs complete with a reported result (pass or fail), with no skipped or undefined status due to missing matrix configuration, and explicit negative checks pass for unsupported EOL pairs.
- **SC-002**: Maintainers can execute the documented command path for any selected pytest-compatible Python/pytest pair in under 10 minutes from a clean checkout.
- **SC-003**: 100% of documented compatibility command examples in contributor-facing docs and quickstart are executed in CI validation at least once per pre-release cycle and complete with expected outcomes.
- **SC-004**: Existing documented supported-version validation jobs show no newly introduced compatibility failures attributable to this feature across one full pre-release validation cycle.
