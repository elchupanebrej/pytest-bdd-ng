# Implementation Plan: Distributed Reporting Stream

**Branch**: `011-merge-xdist-reporting` | **Date**: 2026-03-09 | **Spec**: `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/specs/011-merge-xdist-reporting/spec.md`
**Input**: Feature specification from `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/specs/011-merge-xdist-reporting/spec.md`

**Documentation Language Rule**: This plan and generated feature artifacts MUST be written in English.

## Summary

Replace the reporter-owned worker/controller handoff with an xdist-native
transport that rides the existing `execnet.Channel` through a project-local
remote-module adapter. The controller remains the only writer of the final
NDJSON artifact, structural payloads are deduplicated semantically, runtime
payloads remain traceable per worker attempt, and validation must cover every
supported xdist remote gateway mode. The validation path must also be runnable
from the repository GitHub CI configuration, and new acceptance helpers should
stay Python-first wherever practical, with bash retained only for thin
shell-specific container entry wrappers.

## Technical Context

**Language/Version**: Python 3.10-3.14
**Primary Dependencies**: `pytest>=7`, `pytest-xdist`, `execnet`,
`cucumber-messages`, `pluggy`, `jsonschema`, `filelock`, Docker/Compose,
`tox>=4.2`, GitHub Actions workflow orchestration
**Storage**: Controller-owned final NDJSON artifact on disk; in-memory
controller aggregation state; optional worker-local transient spool files only
as non-authoritative crash buffers
**Testing**: `pytest`, contract tests, targeted message and end-to-end suites,
Docker/Compose remote acceptance, `tox` envs
`py314-pytestlatest-xdist-remote-{socket,via,ssh}-lin`, GitHub Actions
`.github/workflows/main.yml`, `ruff`, `pre-commit`
**Target Platform**: Cross-platform Python library/plugin development with a
Linux CI path for Docker-backed remote acceptance; local development on
Linux/macOS/Windows
**Project Type**: Single Python library and pytest plugin repository
**Performance Goals**: Preserve deterministic final-stream ordering, preserve
per-worker runtime evidence, avoid any manual worker-artifact merge step, and
keep targeted remote acceptance coverage runnable within the repository CI
budget
**Constraints**: No reporter-managed TCP listener; no `rsync` dependency; no
permanent xdist fork; fail fast when xdist/channel integration is unsupported;
all new tests must be runnable from GitHub CI; prefer Python helpers over bash
except for thin shell-specific container startup wrappers
**Scale/Scope**:
`/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/src/pytest_bdd/plugin/gherkin_message_reporter/`,
`/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/src/pytest_bdd/model/message_consolidation.py`,
`/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/src/pytest_bdd/model/message_transport.py`,
`/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/tests/messages/`,
`/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/tests/contract/`,
`/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/tests/e2e/`,
`/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/.github/workflows/main.yml`,
and `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/tox.ini`

**Cross-Platform Validation Rule**: Non-native platform test environments MUST
use the Docker skill, except Windows targets which MAY use non-Docker execution
paths.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Pre-Phase 0 Gate Assessment

| Gate | Status | Evidence |
|------|--------|----------|
| I. Spec-Driven Delivery | PASS | `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/specs/011-merge-xdist-reporting/spec.md` defines the xdist/execnet transport requirement, supported gateway modes, fail-fast behavior, GitHub CI validation, and Python-first helper policy. |
| II. Independent Story Increments | PASS | User stories remain separable across consolidated run output, structural deduplication, and runtime traceability. |
| III. Validation-First Changes | PASS | The plan includes unit, contract, local xdist, Docker-backed remote acceptance, tox, and GitHub CI-aligned validation entrypoints before implementation. |
| IV. Deterministic Compatibility and Contracts | PASS | Versioned contract artifacts define the worker/controller boundary and final-stream behavior, and the plan preserves those contracts while extending them with CI and helper-policy constraints. |
| V. Task-Traceable Commits and Pre-Commit Enforcement | PASS | No planning exception is required; implementation remains responsible for task-linked commits and clean pre-commit runs. |
| Additional Constraint: English-only artifacts | PASS | All planning artifacts are written in English. |
| Additional Constraint: No normal-control `None` returns outside hooks | PASS | The design uses explicit manifests, diagnostics, and deterministic exceptions rather than `None`-return control flow. |

**Gate Result (Pre-Design)**: PASS

## Project Structure

### Documentation (this feature)

```text
/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/specs/011-merge-xdist-reporting/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── xdist-consolidated-stream.md
│   └── xdist-worker-controller-boundary.md
└── tasks.md
```

### Source Code (repository root)

```text
/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/
├── .github/
│   └── workflows/
│       └── main.yml
├── tox.ini
├── src/pytest_bdd/
│   ├── model/
│   │   ├── message_consolidation.py
│   │   ├── message_transport.py
│   │   └── message_validation.py
│   └── plugin/
│       └── gherkin_message_reporter/
│           ├── entrypoint.py
│           ├── hook.py
│           ├── plugin.py
│           └── xdist_remote.py
└── tests/
    ├── contract/
    │   ├── test_xdist_consolidated_stream_contract.py
    │   └── test_xdist_worker_controller_boundary_contract.py
    ├── e2e/
    │   ├── test_xdist_message_aggregation.py
    │   ├── test_xdist_remote_message_aggregation.py
    │   └── fixtures/
    │       └── remote_xdist/
    │           ├── verify_report.py
    │           ├── controller-entrypoint.sh
    │           ├── worker-entrypoint.sh
    │           ├── controller.Dockerfile
    │           ├── worker.Dockerfile
    │           └── docker-compose.yml
    └── messages/
        ├── message_stream_assertions.py
        ├── test_messages_feature_suite.py
        ├── test_xdist_message_consolidation.py
        └── test_xdist_remote_transport.py
```

**Structure Decision**: Keep the existing single-project Python library layout.
The feature is confined to the reporter plugin, consolidation model, contracts,
remote acceptance harness, and CI entrypoints already present in the
repository. Acceptance orchestration and verification should stay in Python
modules under `tests/` wherever practical; shell wrappers remain only where
container entrypoints must directly exec `execnet.script.socketserver` or
`sshd`.

## Phase 0: Outline & Research

Research tasks generated from dependencies and integration scope:

1. Confirm the supported xdist integration point for installing a project-local
   remote worker module without maintaining a permanent xdist fork.
2. Confirm the event framing rules for reporter payloads sent as namespaced
   xdist/execnet events using builtin serializable containers only.
3. Confirm the partial-run model that combines incremental worker chunks with a
   terminal manifest for deterministic controller-side consolidation.
4. Confirm the repository-supported CI execution path for remote acceptance
   coverage through `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/tox.ini`
   and `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/.github/workflows/main.yml`.
5. Confirm the Python-first helper boundary for acceptance orchestration and
   report verification, including the narrow cases where shell wrappers remain
   necessary.

**Phase 0 Output**:
`/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/specs/011-merge-xdist-reporting/research.md`

## Phase 1: Design & Contracts

1. Retain the runtime-entity model in
   `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/specs/011-merge-xdist-reporting/data-model.md`
   and explicitly record that CI wiring and helper implementation language do
   not introduce additional runtime entities.
2. Maintain the worker/controller boundary and consolidated-stream contract
   artifacts in
   `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/specs/011-merge-xdist-reporting/contracts/`,
   adding GitHub CI validation and Python-helper constraints where required.
3. Update
   `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/specs/011-merge-xdist-reporting/quickstart.md`
   with local pytest commands, GitHub CI-aligned tox entrypoints, and the
   helper-implementation guidance for the remote acceptance harness.
4. Update agent context via
   `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/.specify/scripts/bash/update-agent-context.sh codex`.

**Phase 1 Outputs**:

- `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/specs/011-merge-xdist-reporting/data-model.md`
- `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/specs/011-merge-xdist-reporting/contracts/xdist-worker-controller-boundary.md`
- `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/specs/011-merge-xdist-reporting/contracts/xdist-consolidated-stream.md`
- `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/specs/011-merge-xdist-reporting/quickstart.md`
- `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/AGENTS.md`

## Post-Design Constitution Check

| Gate | Status | Evidence |
|------|--------|----------|
| I. Spec-Driven Delivery | PASS | `research.md`, `data-model.md`, `quickstart.md`, and both contract artifacts map directly to FR-001..FR-023 and SC-001..SC-009. |
| II. Independent Story Increments | PASS | The design keeps US1 consolidated output, US2 structural deduplication, and US3 runtime traceability independently testable. |
| III. Validation-First Changes | PASS | `quickstart.md` defines targeted pytest commands plus GitHub CI-aligned tox entrypoints for local and remote validation, including Docker-backed remote acceptance. |
| IV. Deterministic Compatibility and Contracts | PASS | Contracts define the xdist worker/controller boundary, final-stream invariants, supported gateway families, fail-fast behavior, and CI validation expectations. |
| V. Task-Traceable Commits and Pre-Commit Enforcement | PASS | No constitution violation was introduced in planning artifacts; task-linked commits and pre-commit enforcement remain implementation-phase requirements. |
| Additional Constraint: English-only artifacts | PASS | All generated planning artifacts remain in English. |
| Additional Constraint: No normal-control `None` returns outside hooks | PASS | The design keeps deterministic diagnostics, explicit completion manifests, and Python helper utilities with explicit success/failure returns. |

**Gate Result (Post-Design)**: PASS

## Complexity Tracking

No constitution violations detected. No exceptions required.
