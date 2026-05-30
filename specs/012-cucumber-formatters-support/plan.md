# Implementation Plan: Cucumber Formatter Support

**Branch**: `012-cucumber-formatters-support` | **Date**: 2026-03-10 | **Spec**: `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/specs/012-cucumber-formatters-support/spec.md`
**Input**: Feature specification from `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/specs/012-cucumber-formatters-support/spec.md`

**Documentation Language Rule**: This plan and generated feature artifacts MUST be written in English.

## Summary

Add pytest CLI parity for the supported `cucumber-js` formatters by extending the
existing gherkin message reporter. The feature should collect formatter requests
during pytest configuration, validate them before test execution, render outputs
only from the final canonical NDJSON stream after session completion and xdist
consolidation, auto-provision missing formatter npm packages through global
`npm install -g`, and fail fast for terminal formatter conflicts or file output
paths that target missing directories. The legacy `--cucumberjson` path remains
outside this contract, and any existing standalone NDJSON renderer is treated
as implementation reuse rather than additional acceptance scope for this spec.

## Technical Context

**Language/Version**: Python 3.10-3.14 with a Node.js runtime available on `PATH`
**Primary Dependencies**: `pytest>=7`, `pluggy`, `cucumber-messages`,
`filelock`, `packaging`, `@cucumber/cucumber`,
`@cucumber/pretty-formatter`
**Storage**: In-memory reporter state plus canonical NDJSON artifacts and
generated formatter files on disk
**Testing**: `pytest` e2e, compatibility, and hook tests; `ruff`;
repository `pre-commit` hooks
**Target Platform**: Cross-platform Python library/plugin development on
Linux, macOS, and Windows, with local `node` and `npm` available when
formatter rendering is requested
**Project Type**: Single Python library and pytest plugin repository
**Performance Goals**: Keep formatter overhead post-run only, preserve one
canonical render pass per requested run, and avoid additional live-stream
synchronization complexity during pytest execution
**Constraints**: At most one terminal-output formatter per run; fail fast
before test execution when terminal-output formatter flags conflict; do not
create missing directories for file outputs; resolve npm packages locally
first and auto-provision missing ones globally; render only after canonical
NDJSON finalization and xdist consolidation; preserve legacy `--cucumberjson`
compatibility outside the new formatter mapping; treat same normalized file
output path requested by multiple formatters as a configuration conflict
**Scale/Scope**:
`/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/src/pytest_bdd/plugin/gherkin_message_reporter/`,
`/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/src/pytest_bdd/util/npm_resource.py`,
`/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/tests/e2e/test_cucumber_formatters.py`,
`/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/tests/e2e/test_cucumber_formatters_feature.py`,
`/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/tests/hook/test_gherkin_reporter_context_lifecycle.py`,
and documentation under
`/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/features/07 Report/`

## Constitution Check

### Pre-Phase 0 Gate Assessment

| Gate | Status | Evidence |
|------|--------|----------|
| I. Spec-Driven Delivery | PASS | `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/specs/012-cucumber-formatters-support/spec.md` now defines formatter scope, terminal conflict behavior, and fail-fast filesystem behavior. |
| II. Independent Story Increments | PASS | The feature is concentrated in one user story with independently testable terminal, file, and validation scenarios. |
| III. Validation-First Changes | PASS | The plan requires e2e, hook, and compatibility validation before implementation is considered complete, including explicit fail-fast diagnostics. |
| IV. Deterministic Compatibility and Contracts | PASS | The design will define CLI and renderer-boundary contracts with deterministic output-mode, package, and validation rules. |
| V. Task-Traceable Commits and Pre-Commit Enforcement | PASS | No planning exception is required; implementation remains responsible for task-linked commits and clean pre-commit runs. |
| Additional Constraint: English-only artifacts | PASS | All planning artifacts are written in English. |
| Additional Constraint: No normal-control `None` returns outside hooks | PASS | The design centers on explicit validation states and deterministic exceptions rather than sentinel `None` returns. |

**Gate Result (Pre-Design)**: PASS

## Project Structure

### Documentation (this feature)

```text
/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/specs/012-cucumber-formatters-support/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── pytest-cucumber-formatters-cli.md
│   └── formatter-rendering-boundary.md
└── tasks.md
```

### Source Code (repository root)

```text
/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/
├── src/pytest_bdd/
│   ├── plugin/
│   │   ├── cucumber_json/
│   │   │   └── entrypoint.py
│   │   └── gherkin_message_reporter/
│   │       ├── entrypoint.py
│   │       ├── hook.py
│   │       └── plugin.py
│   ├── script/
│   │   └── render_cucumber_formatters.py
│   └── util/
│       └── npm_resource.py
└── tests/
    ├── compatibility/
    │   └── test_render_cucumber_formatters.py
    ├── e2e/
    │   ├── _cucumber_formatters.feature
    │   ├── cucumber_formatter_support.py
    │   ├── test_cucumber_formatters.py
    │   ├── test_cucumber_formatters_feature.py
    │   └── test_e2e.py
    └── hook/
        └── test_gherkin_reporter_context_lifecycle.py
```

**Structure Decision**: Keep the existing single-project Python plugin layout.
The work is centered in the gherkin message reporter, shared npm/package
resolution helpers, CLI entrypoints, and acceptance/compatibility coverage
already present in the repository.

## Phase 0: Outline & Research

Research tasks generated from dependencies and integration scope:

1. Confirm the canonical render timing for formatter outputs relative to
   pytest session completion and xdist NDJSON consolidation.
2. Confirm the validation model for mutually exclusive terminal-output
   formatter flags and how early the failure should surface.
3. Confirm the filesystem contract for file outputs, including the treatment
   of missing parent directories.
4. Confirm the npm dependency resolution order and the fallback path for
   missing `@cucumber/cucumber` and `@cucumber/pretty-formatter`.
5. Confirm the stable mapping between pytest flags, formatter IDs, npm
   packages, and output modes.
6. Confirm the compatibility boundary between the new formatter flags and the
   legacy `--cucumberjson` entrypoint.

**Phase 0 Output**:
`/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/specs/012-cucumber-formatters-support/research.md`

## Phase 1: Design & Contracts

1. Model formatter definitions, requests, execution planning, and npm
   provisioning state in
   `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/specs/012-cucumber-formatters-support/data-model.md`.
2. Define the public pytest CLI contract in
   `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/specs/012-cucumber-formatters-support/contracts/pytest-cucumber-formatters-cli.md`.
3. Define the Python-to-Node rendering boundary in
   `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/specs/012-cucumber-formatters-support/contracts/formatter-rendering-boundary.md`.
4. Update
   `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/specs/012-cucumber-formatters-support/quickstart.md`
   with repository-specific usage, expected diagnostics, and validation slices.
   The quickstart remains focused on pytest CLI behavior defined by the spec
   and does not widen scope to standalone tooling examples.
5. Update agent context via
   `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/.specify/scripts/bash/update-agent-context.sh codex`.

**Phase 1 Outputs**:

- `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/specs/012-cucumber-formatters-support/data-model.md`
- `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/specs/012-cucumber-formatters-support/contracts/pytest-cucumber-formatters-cli.md`
- `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/specs/012-cucumber-formatters-support/contracts/formatter-rendering-boundary.md`
- `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/specs/012-cucumber-formatters-support/quickstart.md`
- `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/AGENTS.md`

## Post-Design Constitution Check

| Gate | Status | Evidence |
|------|--------|----------|
| I. Spec-Driven Delivery | PASS | `research.md`, `data-model.md`, `quickstart.md`, and both contract artifacts map directly to FR-001..FR-009 and SC-001..SC-003. |
| II. Independent Story Increments | PASS | The design keeps single-terminal-output validation, file-output generation, and dependency provisioning independently testable under the same story. |
| III. Validation-First Changes | PASS | `quickstart.md` and the contracts define concrete pytest validation slices plus explicit error cases for conflicts and missing directories. |
| IV. Deterministic Compatibility and Contracts | PASS | Contracts make formatter selection, output targets, validation errors, and the Python-to-Node handoff deterministic and reviewable. |
| V. Task-Traceable Commits and Pre-Commit Enforcement | PASS | No planning artifact introduces a constitution exception; implementation remains bound to task-linked commits and pre-commit enforcement. |
| Additional Constraint: English-only artifacts | PASS | All generated artifacts remain in English. |
| Additional Constraint: No normal-control `None` returns outside hooks | PASS | The design uses explicit request, plan, and provisioning states instead of control-flow `None` values. |

**Gate Result (Post-Design)**: PASS

## Complexity Tracking

No constitution violations detected. No exceptions required.
