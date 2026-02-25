<!-- markdownlint-disable MD013 -->

# Feature Specification: Migrate Documentation Generation to Jinja2

**Feature Branch**: `004-migrate-jinja2-docs`
**Created**: 2026-02-24
**Status**: Draft
**Language**: English
**Input**: User description: "Ты не создал спеку на миграцию на Jinja2"

## Clarifications

### Session 2026-02-24

- Q: What level of output compatibility is required between old and new generation? → A: Semantic parity only; formatting differences are allowed if meaning and structure are preserved.

### Session 2026-02-25

- Q: What content boundaries must `docs/features/features.rst` follow? → A: It must stay focused on feature-file-driven generated documentation and must not contain internal implementation details or conversion history; such content must live in a separate document.
- Q: Where should non-BDD internal notes be located? → A: Runtime execution-context/API compatibility notes belong in `docs/internal/execution-context-and-api-compatibility.rst`; conversion traceability belongs in `specs/002-e2e-test-conversion/conversion-parity-audit.md`; conversion-quality policy (lint/pre-commit) belongs in `docs/internal/documentation-generation-notes.rst`.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Preserve Generated Output Parity (Priority: P1)

As a maintainer, I want template generation to use Jinja2 while keeping generated outputs functionally equivalent, so existing workflows and tests keep passing.

**Why this priority**: Output parity is the highest-risk part of migration and directly affects reliability.

**Independent Test**: Run generation commands and compare produced output against expected baseline behavior for representative scenarios.

**Acceptance Scenarios**:

1. **Given** existing generation inputs, **When** outputs are produced with the new template engine, **Then** generated artifacts match expected structure and semantics.
2. **Given** existing quote, unicode, and formatting cases, **When** generation runs, **Then** output remains valid and consistent with prior user-visible behavior.

---

### User Story 2 - Preserve Manual Documentation Content (Priority: P2)

As a documentation maintainer, I want manual edits in mixed generated/manual documentation files to be preserved during regeneration, so curation work is not lost.

**Why this priority**: Regeneration safety is required for documentation quality and trust in tooling.

**Independent Test**: Regenerate documentation from a source tree where the target index already contains manual sections and verify manual content is preserved.

**Acceptance Scenarios**:

1. **Given** a documentation index containing both generated and manual sections, **When** regeneration is executed, **Then** generated sections are refreshed and manual sections remain unchanged.
2. **Given** preexisting generated markers, **When** regeneration is executed, **Then** only marked generated blocks are replaced.

---

### User Story 3 - Keep Contributor Workflow Stable (Priority: P3)

As a contributor, I want migration validation to be explicit and reproducible, so template-engine changes can be reviewed and maintained safely.

**Why this priority**: Clear validation lowers maintenance risk after migration.

**Independent Test**: Execute targeted generation/documentation tests and lint checks and verify they pass with the migrated templates.

**Acceptance Scenarios**:

1. **Given** the migrated templates, **When** targeted generation and documentation tests run, **Then** they pass without requiring downstream behavior changes.
2. **Given** a commit is prepared, **When** pre-commit checks run, **Then** documentation generation validation is executed and fails on out-of-date generated docs.
3. **Given** repository packaging metadata, **When** the project is installed, **Then** required template assets for generation are available.

### Edge Cases

- Existing documentation index has no generated marker block.
- Existing documentation index has both manual prefix and manual suffix around generated content.
- Generation includes files with unicode and nested quote combinations.
- Regeneration is run when no source changes exist.
- Mixed feature formats are present in one run.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST use Jinja2 as the template engine for generation flows covered by this migration scope.
- **FR-002**: The system MUST preserve semantic parity of generated outputs for supported generation scenarios, allowing non-functional formatting differences.
- **FR-003**: The system MUST preserve manual documentation content when regenerating mixed manual/generated index files.
- **FR-004**: The system MUST update only generated sections when explicit generated-section boundaries are present.
- **FR-005**: The system MUST support consistent output for special-content cases, including unicode and quote-heavy inputs.
- **FR-006**: The system MUST keep template assets discoverable and packaged for runtime generation commands.
- **FR-007**: The system MUST include automated validation that covers generation parity and documentation regeneration safety.
- **FR-008**: The system MUST keep contributor workflows operational without requiring user-facing migration steps.
- **FR-009**: The system MUST include documentation generation in pre-commit checks so out-of-date generated docs fail validation before commit.
- **FR-010**: The system MUST ensure generated documentation artifacts are regenerated as part of migration completion and kept in sync with generator output.
- **FR-011**: The system MUST keep `docs/features/features.rst` focused on generated feature documentation navigation and user-facing context, excluding internal implementation/change-history details.
- **FR-012**: The system MUST store internal implementation notes for documentation generation outside `docs/features/features.rst`.
- **FR-013**: The system MUST keep runtime execution-context/API compatibility notes and conversion traceability policy in internal/spec artifacts, not in `docs/features/features.rst`.

### Key Entities *(include if feature involves data)*

- **Template Asset Set**: All template resources used by generation workflows.
- **Generated Documentation Block**: The replaceable section owned by generation logic.
- **Manual Documentation Block**: Human-maintained content that must remain untouched by regeneration.
- **Generation Parity Case**: A testable input/output scenario used to verify migration correctness.

## Assumptions

- Current generation behavior is the baseline for parity validation.
- Migration scope is limited to generation paths currently used in repository workflows.
- Manual documentation content outside generated blocks is authoritative and must not be overwritten.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of targeted semantic-parity tests pass after migration.
- **SC-002**: 100% of targeted documentation regeneration safety tests pass for mixed manual/generated files.
- **SC-003**: 0 manual documentation regressions are introduced in validated regeneration scenarios.
- **SC-004**: Required template assets are present in packaging validation for 100% of covered generation commands.
- **SC-005**: Pre-commit execution fails in 100% of sampled cases where generated documentation is stale and passes once docs are regenerated.
- **SC-006**: 0 internal implementation/change-history sections remain in `docs/features/features.rst` after migration validation.
- **SC-007**: 100% of sampled non-BDD internal notes are located outside `docs/features/features.rst` in designated internal/spec documents.
