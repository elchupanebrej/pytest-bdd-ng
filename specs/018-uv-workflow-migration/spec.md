<!-- markdownlint-disable MD013 -->

# Feature Specification: Standardize Project Workflows on `uv`

**Feature Branch**: `018-uv-workflow-migration`
**Created**: 2026-04-11
**Status**: Draft
**Input**: User description: "Project has to use uv as main env coordinator. uv-tox must be used for testing, setup documentation has to be updated"

## Clarifications

### Session 2026-04-14
- Q: Depth of Testing Tool replacement → A: Hybrid approach (`tox-uv`): Replace conda completely with uv for Python versions, but keep tox (with tox-uv) for test matrix coordination.
- Q: Execution of standalone tools → A: Ephemeral Execution: Rely entirely on `uvx` for tool invocations (`uvx pre-commit`, `uvx tox`) to provide a zero-setup experience.
- Q: Scope of CI Migration → A: Migrate CI: Completely replace `conda`, `setup-python`, and other environment bootstrapping tools in `.github/workflows` with `astral-sh/setup-uv`.
- Q: Prerequisite handling in Readme → A: uv must be a part of pyproject.toml because of testing. No extra prerequisite in Readme are needed.
- Q: Non-entrypoint script execution via uv → A: Scripts that are not entrypoints of a project cannot be run via uv natively without issues; they must be mapped as formal entrypoints in pyproject.toml.
- Q: Rationale for uv dependency tracking → A: uv is not utilized internally by the core engine; it is tracked in `pyproject.toml` exclusively because specific test Features depend on it (or could depend on it).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Contributors set up the project through one primary workflow (Priority: P1)

As a contributor, I want one clearly documented environment workflow for the project so I can install dependencies, enter the project environment, and start working without having to choose between competing setup paths.

**Why this priority**: A single canonical setup flow reduces onboarding friction, avoids stale contributor habits, and lowers the chance of environment-specific failures.

**Independent Test**: A contributor can follow the primary setup instructions from a clean machine and reach a working development environment without relying on alternative package or environment managers.

**Acceptance Scenarios**:
1. **Given** a new contributor starts from the project setup documentation, **When** they complete the documented setup flow, **Then** they obtain a working development environment through `uv` as the primary coordinator.
2. **Given** a contributor needs to install or sync project dependencies, **When** they follow the canonical workflow, **Then** the instructions direct them through `uv` rather than a separate primary environment-management path.

---

### User Story 2 - Maintainers run the test matrix through the canonical test entrypoint (Priority: P1)

As a maintainer, I want the supported test workflow to run through `uv-tox` so that validation commands are consistent across local development, contributor guidance, and automation.

**Why this priority**: Test command consistency is required to keep contributor instructions, local execution, and release validation aligned.

**Independent Test**: A maintainer can discover the supported test commands in project guidance and run the documented test matrix through `uv-tox` without needing a separate canonical tox invocation path.

**Acceptance Scenarios**:
1. **Given** a maintainer wants to run the project's supported test environments, **When** they consult the project commands and setup guidance, **Then** the documented test entrypoint uses `uv-tox`.
2. **Given** a contributor follows the standard testing instructions, **When** they execute the documented commands, **Then** those commands align with the project's canonical validation workflow.

---

### User Story 3 - Documentation matches the actual contributor workflow (Priority: P2)

As a contributor or maintainer, I want setup and workflow documentation to match the current project expectations so I do not lose time following obsolete instructions.

**Why this priority**: Documentation drift makes migrations fail in practice even when the code and configuration are correct.

**Independent Test**: Reviewers can compare the documented setup and test instructions against the approved workflow and confirm there are no conflicting or outdated primary-path instructions.

**Acceptance Scenarios**:
1. **Given** a contributor reads the setup documentation, **When** they look for installation and environment guidance, **Then** the instructions describe the `uv`-based workflow as the main path.
2. **Given** a contributor reads the testing documentation, **When** they look for the supported test entrypoint, **Then** the guidance points to `uv-tox`.
3. **Given** the documentation set is reviewed after the migration, **When** reviewers search for setup and testing instructions, **Then** outdated primary workflow guidance is either removed or clearly downgraded from canonical status.

---

### Edge Cases

- Existing contributor commands referenced in repository guidance must not leave readers with two conflicting "official" workflows.
- Project validation guidance must remain usable for contributors who only need to run a subset of checks rather than the full test matrix.
- Any platform-specific setup notes that remain necessary must be expressed as exceptions to the main `uv` workflow, not as separate primary onboarding paths.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The project MUST define `uv` as the primary environment coordination workflow for contributor setup and day-to-day development, completely eliminating `conda` for Python version provisioning by using `uv python install` instead.
- **FR-002**: The project MUST provide a canonical dependency installation and environment preparation path that is driven through `uv`, avoiding the need for manual virtual environment creation.
- **FR-003**: The project MUST define `uvx` (e.g. `uvx tox`, `uvx pre-commit`) as the canonical way to run standalone tools to ensure ephemeral, zero-install execution and eliminate global tool pollution.
- **FR-004**: Project guidance MUST identify which routine validation commands contributors are expected to run through `uvx tox`.
- **FR-005**: Setup documentation MUST describe the required prerequisites and the ordered steps needed to start contributing with the `uv`-based workflow.
- **FR-006**: Testing documentation MUST describe how contributors and maintainers run the supported test matrix through `uv-tox`.
- **FR-007**: Documentation updates MUST remove or explicitly de-emphasize conflicting legacy setup and test workflow instructions so only one primary workflow is presented.
- **FR-008**: The migrated workflow MUST preserve the project's ability to support its currently documented Python-version compatibility expectations.
- **FR-009**: Contributors MUST be able to identify, from repository documentation alone, how to set up the project, install development dependencies, and run the primary validation commands.
- **FR-010**: GitHub Actions CI workflows MUST completely migrate to `astral-sh/setup-uv`, substituting all `setup-python` and conda infrastructure with `uv` routines to strictly mirror the native local workflow.

### Key Entities

- **Contributor workflow**: The documented sequence a contributor follows to install prerequisites, prepare the project environment, and run routine development commands.
- **Canonical setup path**: The single project-approved setup route presented as the primary onboarding path.
- **Canonical test entrypoint**: The project-approved command path for running tox-based validation and test environments.
- **Setup documentation**: Repository documentation that explains prerequisites, installation, environment preparation, and first-run steps.
- **Validation guidance**: Repository documentation that explains how contributors and maintainers run the supported checks and test matrix.

### Assumptions

- The project intends to keep tox-compatible environment definitions, while changing the canonical execution path to `uv-tox`.
- The migration applies to contributor-facing and maintainer-facing workflow guidance rather than changing the project's public runtime API.
- Existing compatibility promises for supported Python versions remain in scope and must continue to be reflected in the documented workflow.
- Some historical commands may continue to exist for transition or compatibility reasons, but they will no longer be presented as the primary project workflow.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A contributor can complete the documented project setup and reach a ready-to-work environment using the canonical `uv` workflow in 15 minutes or less on a clean machine with prerequisites installed.
- **SC-002**: 100% of repository documentation that describes the primary setup flow identifies `uv` as the canonical environment coordinator.
- **SC-003**: 100% of repository documentation that describes the primary tox-based validation flow identifies `uv-tox` as the canonical test entrypoint.
- **SC-004**: Reviewers can identify setup, dependency installation, and primary test commands from the repository documentation without encountering conflicting "official" workflows.
