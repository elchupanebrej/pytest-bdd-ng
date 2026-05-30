# Feature Specification: General-to-Specialized Documentation Order

**Feature Branch**: `010-order-rst-docs`
**Created**: 2026-03-08
**Status**: Draft
**Input**: User description: "Нужно чтоб документация генерировалась в rst из feature файлов от более общих к более специализированным так как тесты выступают документацией для конечного пользователя. Желательно минимально менять механизм и по возможности обойтись нумерацией"

## Clarifications

### Session 2026-03-08

- Q: What is the required boundary for moving logic out of `src/pytest_bdd/script/bdd_tree_to_rst.py`? → A: Keep the script responsible for tree traversal and data collection; move RST rendering, headings, and output structure logic into templates as far as practical.
- Q: What is the role of `pandoc` in heading-level handling? → A: Prefer using `pandoc` where it helps normalize heading levels and reduce script logic, but do not make it a mandatory requirement for every case.
- Q: Where should numeric ordering live? → A: Use numeric prefixes in file and directory names as the source of ordering, but do not expose those prefixes in reader-facing headings or navigation labels.
- Q: Should numeric prefixes affect generated page paths? → A: Keep numeric prefixes in generated page paths and filenames; hide them only in reader-facing headings and navigation labels.
- Q: What is the fallback policy for missing or duplicate ordering prefixes? → A: Require numeric prefixes for all sibling items in each ordered navigation scope; missing or duplicate prefixes are generation errors.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Read Topics in Learning Order (Priority: P1)

As an end user, I want generated documentation to guide me from the most general topics to more specialized ones, so I can learn the product capabilities in a natural order.

**Why this priority**: The generated documentation is part of the user-facing learning path, so reader order directly affects comprehension.

**Independent Test**: Generate documentation from a curated set of broad and specialized source topics and verify that navigation presents the broad topics first within each section.

**Acceptance Scenarios**:

1. **Given** a section contains both introductory and specialized topics, **When** documentation is generated, **Then** the introductory topics appear before the specialized ones in the reader-facing navigation.
2. **Given** a nested section contains its own curated topic sequence, **When** documentation is generated, **Then** that subsection preserves its own general-to-specialized order independently of other sections.
3. **Given** a reader starts from the generated documentation index, **When** they follow the listed sequence, **Then** they encounter foundational topics before advanced topics in each curated section.

---

### User Story 2 - Curate Order with Lightweight Markers (Priority: P2)

As a documentation maintainer, I want to control topic order with lightweight numeric prefixes in source file and directory names, while keeping those prefixes hidden from reader-facing documentation labels, so I can shape the reading path without introducing a separate complex mechanism.

**Why this priority**: The requested behavior must stay easy to maintain and should fit the existing generation workflow with minimal change.

**Independent Test**: Add ordering markers to sibling source topics, regenerate the documentation, and verify that the generated order follows those markers without manual editing of the generated index.

**Acceptance Scenarios**:

1. **Given** sibling source topics have explicit ordering markers, **When** documentation is regenerated, **Then** the generated navigation follows that relative order.
2. **Given** a maintainer changes only the ordering marker of a topic, **When** documentation is regenerated, **Then** the topic moves to the new position without any manual reordering of generated output.
3. **Given** a new topic is added to an ordered sibling group, **When** it does not receive a unique numeric prefix, **Then** generation fails with a deterministic ordering error.

---

### User Story 3 - Keep Regeneration Predictable (Priority: P3)

As a contributor, I want ordered documentation generation to remain deterministic while keeping the generator script focused on traversal and data preparation, so regeneration stays trustworthy and rendering logic becomes easier to maintain in templates.

**Why this priority**: Documentation generation is part of repository maintenance, so ordering must not create unstable or high-overhead contributor workflows.

**Independent Test**: Run documentation generation repeatedly on the same ordered sources and verify that output order remains stable and that manual content outside the generated block is preserved.

**Acceptance Scenarios**:

1. **Given** the same ordered source set is regenerated multiple times, **When** generation completes, **Then** the navigation order is identical in every run.
2. **Given** sibling topics in one ordered scope contain a missing or duplicate numeric prefix, **When** documentation is generated, **Then** generation fails with a deterministic validation error instead of producing ambiguous output.
3. **Given** the documentation index contains manual text outside the auto-generated tree, **When** generation runs, **Then** that manual text remains unchanged.

### Edge Cases

- Two sibling topics declare the same numeric prefix within one navigation scope.
- A section contains sibling topics where one or more items have no numeric prefix.
- Only nested subsections need curated ordering while their parent section does not change.
- A topic changes order without any content change.
- Existing manual introduction or suffix content surrounds the auto-generated navigation block.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST generate reader-facing documentation navigation so each curated section progresses from more general topics to more specialized topics.
- **FR-002**: The system MUST allow maintainers to define sibling-topic order with lightweight numeric prefixes in source file and directory names as the preferred curation method.
- **FR-003**: The system MUST apply ordering independently within each navigation scope so top-level sections and nested subsections can each follow their own curated sequence.
- **FR-004**: The system MUST preserve the current documentation-generation workflow except for the ordering behavior required to present the curated sequence.
- **FR-005**: The system MUST regenerate ordered documentation without requiring manual edits to the generated navigation after each run.
- **FR-006**: The system MUST produce deterministic navigation output when the same ordered source set is regenerated multiple times.
- **FR-007**: The system MUST require every sibling topic in each ordered navigation scope to provide a numeric ordering prefix.
- **FR-008**: The system MUST fail generation with a deterministic validation error when a sibling topic is missing a required numeric prefix or when two sibling topics share the same numeric prefix within one navigation scope.
- **FR-009**: The system MUST preserve existing section grouping and boundaries unless a maintainer explicitly changes the curated order of items within those sections.
- **FR-010**: The system MUST preserve manual documentation content outside the auto-generated navigation block during regeneration.
- **FR-011**: The system MUST make the curated ordering convention clear enough that maintainers can place new topics in the intended reader sequence without manual post-processing.
- **FR-012**: The system MUST keep the generation coordinator focused on source discovery, tree traversal, and data preparation needed for documentation generation.
- **FR-013**: The system MUST express rendered documentation structure, headings, and other presentation-oriented output rules in templates as far as practical within the current workflow.
- **FR-014**: The system MUST reduce script-side rendering logic without requiring a broader rewrite of the existing generation flow.
- **FR-015**: The system MUST support delegating heading-level normalization to the template-driven rendering flow or an existing conversion step, using `pandoc` as a preferred option where it meaningfully reduces script logic.
- **FR-016**: The system MUST strip ordering prefixes from reader-facing headings and navigation labels in generated documentation.
- **FR-017**: The system MUST preserve ordering prefixes in generated page paths and filenames so ordering can rely on existing source naming without an additional path-mapping layer.

### Key Entities *(include if feature involves data)*

- **Documentation Source Topic**: A feature-derived documentation unit that contributes one generated page and belongs to a navigation scope.
- **Navigation Scope**: A set of sibling documentation items shown together in one generated section or subsection.
- **Ordering Cue**: A numeric prefix in a source file or directory name that determines relative position among sibling topics.
- **Generated Documentation Index**: The reader-facing reStructuredText navigation page that lists sections and topics derived from the source tree.
- **Generated Page Path**: The generated documentation path derived from the source tree, retaining numeric prefixes for stability and ordering.

## Assumptions

- The current documentation hierarchy already provides the correct section boundaries; this feature only needs to improve the order of items inside that hierarchy.
- Numeric prefixes may be introduced into source names if generated reader-facing labels remove them before display.
- Generated paths may retain numeric prefixes even when reader-facing labels remove them.
- Existing traversal and source-discovery behavior remain the baseline unless a change is required to support template-driven rendering responsibilities.
- Existing heading conversion behavior may remain heterogeneous as long as the resulting heading levels are correct and the script-side logic is reduced.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: In 100% of validation scenarios with valid sibling prefixes, generated navigation lists place broader topics before more specialized topics according to the curated sequence.
- **SC-002**: 100% of repeated generation runs on unchanged ordered sources produce the same navigation order.
- **SC-003**: In 100% of validated reordering scenarios, a maintainer can reposition a topic by changing only its ordering cue, with 0 required manual edits to the generated navigation file after regeneration.
- **SC-004**: 100% of validation scenarios with missing sibling prefixes or duplicate sibling prefixes fail with the documented deterministic validation error.
- **SC-005**: 0 validated regeneration scenarios overwrite manual content outside the auto-generated navigation block.
- **SC-006**: 100% of validation scenarios with valid sibling prefixes resolve to the documented deterministic order.
- **SC-007**: In 100% of validated generation scenarios, presentation-oriented output rules are provided by templates while the generation coordinator remains limited to traversal and data-preparation responsibilities.
- **SC-008**: In 100% of validated heading-level scenarios, heading normalization is achieved without expanding script-side presentation logic, and preferred conversion-assisted paths remain compatible with the current workflow.
- **SC-009**: In 100% of validated ordered-generation scenarios, numeric prefixes control sibling order while reader-facing headings and navigation labels omit those prefixes.
- **SC-010**: In 100% of validated ordered-generation scenarios, generated page paths retain numeric prefixes and require no separate path-remapping mechanism.
