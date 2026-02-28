# Feature Specification: Non-empty BDD Headings in Feature Files

**Feature Branch**: `005-no-empty-bdd-headings`
**Created**: 2026-02-25
**Status**: Draft
**Language**: English
**Input**: User description: "В feature файлах в папке features не должно быть Feature и Scenario с пустыми заголовками"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Block Empty Parsed Headings (Priority: P1)

As a maintainer, I want validation to reject empty `Feature` and `Scenario` titles in feature files so that suite behavior is explicit and readable.

**Why this priority**: Empty parsed headings reduce readability and hide intent in core BDD assets used in daily development and review.

**Independent Test**: Add one feature file with an empty parsed `Feature` title and one with an empty parsed `Scenario` title; run validation and confirm both are rejected with actionable errors.

**Acceptance Scenarios**:

1. **Given** a file in `features/` with an empty parsed `Feature` title, **When** validation runs, **Then** validation fails and reports file path and line.
2. **Given** a file in `features/` with an empty parsed `Scenario` or `Scenario Outline` title, **When** validation runs, **Then** validation fails and reports file path and line.
3. **Given** files with non-empty parsed titles, **When** validation runs, **Then** validation succeeds.

---

### User Story 2 - Normalize Existing Repository Files (Priority: P2)

As a maintainer, I want existing feature files in `features/` to comply with the same title rule so the repository baseline is clean.

**Why this priority**: New checks are only useful if current repository content already satisfies them.

**Independent Test**: Run validation against current `features/` content and confirm no violations remain.

**Acceptance Scenarios**:

1. **Given** the current repository content under `features/`, **When** validation runs, **Then** there are zero empty parsed heading violations.

---

### User Story 3 - Keep Scope Focused on Real Parsed Headings (Priority: P3)

As a contributor, I want the rule to target only parsed BDD headings so documentation examples and literal snippets are not incorrectly rejected.

**Why this priority**: Prevents noisy false positives and keeps the rule aligned with user-facing BDD structure.

**Independent Test**: Include keyword-like text with empty labels in non-parsed snippets and confirm validation result is unaffected.

**Acceptance Scenarios**:

1. **Given** keyword-like text in non-parsed snippet sections, **When** validation runs, **Then** no violation is reported for those snippets.

### Edge Cases

- Titles containing only spaces or tabs after `Feature:`, `Scenario:`, or `Scenario Outline:` are treated as empty.
- Mixed heading depth in markdown (for example `## Scenario:` and `### Scenario:`) still must have non-empty parsed titles.
- Multiple violations in one file are all reported in a single validation run.
- Files outside `features/` are not evaluated by this feature.

### Assumptions

- Scope is limited to files under the repository `features/` directory.
- The rule applies to parsed BDD headings (`Feature`, `Scenario`, `Scenario Outline`) only.
- Existing validation/quality gates can surface blocking failures during contributor workflow.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST detect empty parsed `Feature` titles in files under `features/`.
- **FR-002**: The system MUST detect empty parsed `Scenario` and `Scenario Outline` titles in files under `features/`.
- **FR-003**: The system MUST treat missing text and whitespace-only text after a heading keyword as empty.
- **FR-004**: The system MUST report each violation with at least file path, line reference, and heading type.
- **FR-005**: The system MUST fail validation when one or more empty parsed heading violations are present.
- **FR-006**: The repository baseline under `features/` MUST contain no empty parsed heading violations.
- **FR-007**: The validation rule MUST ignore non-parsed snippet content so that only real parsed headings are enforced.

### Key Entities *(include if feature involves data)*

- **Feature Document**: A file under `features/` containing parsed BDD headings and scenarios.
- **Heading Record**: A parsed heading entry with type (`Feature`, `Scenario`, `Scenario Outline`), title text, and line reference.
- **Validation Violation**: A single detected rule breach containing location and remediation message.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of feature documents under `features/` have non-empty parsed `Feature` and `Scenario`/`Scenario Outline` titles.
- **SC-002**: Validation reports 100% of seeded empty-heading violations in acceptance test fixtures.
- **SC-003**: Validation output provides file and line details for every detected violation.
- **SC-004**: Pull-request quality checks block merges whenever any empty parsed heading violation is present.
