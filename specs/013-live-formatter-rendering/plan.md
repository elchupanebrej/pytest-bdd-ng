# Implementation Plan: Live Formatter Rendering

**Branch**: `013-live-formatter-rendering` | **Date**: `2026-03-14` | **Spec**: `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/specs/013-live-formatter-rendering/spec.md`
**Input**: Feature specification from `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/specs/013-live-formatter-rendering/spec.md`

## Summary

Deliver live incremental formatter rendering for standard and `pytest-xdist`
runs through an explicit reporting architecture: a narrow reporter coordination
root, a public lifecycle contract between the pytest entrypoint and the
reporting runtime, explicit collaborator dependencies between runtime services,
one real pytest plugin per formatter, and a first-class standalone rendering
service for NDJSON replay. Long generated scripts remain template-backed, live
reporting stays controller-owned during distributed runs, and formatter
discovery uses one canonical source per execution mode.

## Technical Context

**Language/Version**: Python 3.10-3.14 with Node.js runtime available on `PATH`  
**Primary Dependencies**: `pytest>=7`, `pluggy`, `pytest-xdist>=3.8.0`, `execnet`, `filelock`, `cucumber-messages`, `@cucumber/cucumber`, `@cucumber/pretty-formatter`  
**Storage**: In-memory reporting state plus temporary rendered script assets and canonical NDJSON artifacts on disk  
**Testing**: `pytest`, `tox`, `ruff`, contract tests, compatibility replay tests, hook and lifecycle tests, e2e formatter slices, xdist aggregation slices, documentation validation  
**Target Platform**: Local Python library and CLI plugin runtime on macOS/Linux, with Docker-backed coverage for non-native distributed acceptance paths  
**Project Type**: Python library and pytest plugin suite with CLI-compatible replay tooling  
**Performance Goals**: In validation runs lasting at least 30 seconds, first visible formatter output appears before 25% of total elapsed time; live delivery does not block on post-run consolidation  
**Constraints**: Controller-only rendering during distributed runs; no silent fallback to post-run-only rendering; formatter modules must be real pytest or pluggy plugins; reporter root must remain a narrow coordination boundary; entrypoint and runtime must communicate through one explicit lifecycle contract; runtime services must use explicit narrow dependencies instead of reporter-backed service-locator access; standalone replay must use a first-class application service boundary rather than synthetic pytest `Config` objects; generated helper scripts may remain inline only below 20 lines; supported runtime paths must not rely on package-scan formatter discovery when pytest11 or hook-based discovery is already available  
**Scale/Scope**: One live formatter session per run, one controller-owned distributed rendering authority, concurrent support for all currently exposed cucumber formatter requests across standard and xdist execution modes, and one supported standalone NDJSON replay service

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Pre-Design Gate

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Spec-Driven Delivery | PASS | Plan aligns to accepted clarifications in `FR-011` through `FR-021` with no unresolved `NEEDS CLARIFICATION` markers. |
| II. Independent Story Increments | PASS | Design still preserves one independently testable single-process story and one independently testable distributed controller-only story. |
| III. Validation-First Changes | PASS | Plan requires contract, hook, compatibility, e2e, docs, and tox validation for each moved architectural seam. |
| IV. Deterministic Compatibility and Contracts | PASS | CLI, xdist, plugin-boundary, and standalone-rendering boundaries are explicit and versionable in planning artifacts. |
| V. Task-Traceable Commits and Pre-Commit Enforcement | PASS | No exception required in design; implementation remains bound to task-scoped commits and pre-commit enforcement. |

**Gate Result**: PASS

### Post-Design Gate

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Spec-Driven Delivery | PASS | `research.md`, `data-model.md`, `quickstart.md`, and contracts now encode the narrow-root, explicit-lifecycle, standalone-service, formatter-ownership, and discovery-policy requirements. |
| II. Independent Story Increments | PASS | Artifacts preserve one story for local live rendering and one story for distributed controller-owned rendering without coupling them to unfinished lower-priority work. |
| III. Validation-First Changes | PASS | Quickstart validation now includes slices for public CLI, hook lifecycle, standalone replay boundary, distributed rendering, and documentation. |
| IV. Deterministic Compatibility and Contracts | PASS | Plugin boundary, standalone replay boundary, and xdist boundary remain explicit and testable. |
| V. Task-Traceable Commits and Pre-Commit Enforcement | PASS | No complexity exception required. |

**Gate Result**: PASS

## Project Structure

### Documentation (this feature)

```text
/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/specs/013-live-formatter-rendering/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── live-reporting-plugin-boundary.md
│   ├── pytest-live-formatters-cli.md
│   ├── standalone-rendering-boundary.md
│   └── xdist-live-reporting-boundary.md
└── tasks.md
```

### Source Code (repository root)

```text
/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/src/pytest_bdd/
├── plugin/
│   ├── cucumber_formatter_support/
│   ├── cucumber_summary.py
│   ├── cucumber_progress.py
│   ├── cucumber_progress_bar.py
│   ├── cucumber_pretty.py
│   ├── cucumber_json_formatter.py
│   ├── cucumber_junit.py
│   ├── cucumber_usage.py
│   ├── cucumber_usage_json.py
│   ├── cucumber_snippets.py
│   └── gherkin_message_reporter/
│       ├── entrypoint.py
│       ├── plugin.py
│       ├── lifecycle_runtime.py
│       ├── transport_runtime.py
│       ├── scenario_runtime.py
│       ├── step_catalog_runtime.py
│       ├── hook_catalog_runtime.py
│       ├── attachment_runtime.py
│       ├── live_formatter_runtime.py
│       ├── standalone_renderer.py
│       ├── session.py
│       └── resources/templates/
├── script/
│   └── render_cucumber_formatters.py
└── util/
    └── cucumber_formatters.py

/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/src/pytest_bdd_worker_bootstrap/
└── xdist_remote.py

/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/tests/
├── compatibility/
├── contract/
├── doc/
├── e2e/
├── hook/
├── messages/
├── model/
└── support/
    └── templates/
```

**Structure Decision**: Keep the existing library and test layout, but treat
formatter plugins as peer pytest plugins at `src/pytest_bdd/plugin/` and keep
`gherkin_message_reporter/` focused on orchestration, lifecycle, transport,
runtime assets, and standalone replay services. The standalone replay path is
an explicit application boundary, not a synthetic in-process pytest runtime.

## Complexity Tracking

No constitution violations or justified exceptions are required for this
feature plan.

## Phase 0: Research Summary

Phase 0 resolves all current design questions without leaving `NEEDS
CLARIFICATION` markers:

1. Keep one long-lived formatter session per pytest run.
2. Render only on the controller/main authority during distributed runs.
3. Attach all formatter requests to the same live stream.
4. Preserve per-source order and use controller arrival order across sources.
5. Surface live delivery interruption as a hard runtime/reporting error.
6. Preserve existing CLI flags and replay entrypoints as compatibility surfaces.
7. Keep automatic capture switching in the product path rather than helper-only workarounds.
8. Split runtime responsibilities between orchestration and formatter-specific modules.
9. Render long generated scripts from repository templates/resources.
10. Register split reporter modules as real pytest or pluggy plugins through hook registration.
11. Keep mutable live-reporting state in plugin/session/config/request-owned objects only.
12. Reduce the reporter root to a narrow coordination boundary and move assembly concerns into dedicated collaborators.
13. Formalize one public lifecycle contract between the entrypoint and the reporting runtime.
14. Replace reporter-backed service-locator access with explicit narrow service dependencies.
15. Make standalone replay a first-class application service instead of a synthetic pytest runtime.
16. Move formatter-specific request and runtime-asset behavior into formatter plugins or formatter-owned collaborators.
17. Use one canonical formatter discovery source per execution mode and remove supported package-scan fallback paths.

See `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/specs/013-live-formatter-rendering/research.md`.

## Phase 1: Design Summary

### Runtime Assembly Boundaries

- `entrypoint.py` remains the public pytest registration surface only.
- The reporter root exposes one explicit lifecycle contract for setup, teardown,
  and public rendering calls.
- Formatter request resolution, xdist authority decisions, runtime asset
  preparation, and service-graph assembly move into dedicated collaborators
  rather than remaining owned by one aggregate root class.

### Service Dependency Rules

- Runtime services declare only direct collaborator dependencies.
- Service modules may call other services only through explicitly provided
  collaborators, not through reporter-backed service-locator properties.
- Cross-service collaboration must remain visible in constructor or method
  signatures so dependency review is local and testable.

### Standalone Rendering Boundary

- Standalone NDJSON replay is modeled as a first-class rendering service.
- The standalone service accepts canonical NDJSON plus normalized formatter
  requests and returns render results through an explicit public API.
- Supported standalone flows must not require synthetic pytest `Config`
  objects, `SimpleNamespace` stand-ins, or ad hoc pluginmanager construction.

### Formatter Plugin Ownership and Discovery

- Each formatter plugin owns its formatter-specific request-building and
  runtime-asset behavior.
- Shared formatter support code is limited to reusable primitives and shared
  abstractions; it must not remain the primary home of formatter-specific logic
  for most plugins.
- Pytest runtime discovery remains hook-based and pytest11-driven.
- Standalone discovery uses one explicit catalog path for replay mode, with no
  package-scan fallback in supported environments.

### Data and Contract Artifacts

- Data model now includes a standalone rendering service boundary, reporter
  coordination root, explicit service dependency graph, and formatter discovery
  policy.
- Plugin boundary contract now requires a narrow reporter root, explicit
  lifecycle contract, explicit service dependencies, formatter-owned behavior,
  and one discovery policy per execution mode.
- Standalone rendering boundary contract now defines the supported replay
  service interface and forbids synthetic pytest runtime emulation.

### Validation Strategy

- Contract tests prove CLI stability, plugin boundaries, and standalone replay
  boundary obligations.
- Hook/lifecycle tests prove startup, capture, registration, and entrypoint to
  reporter lifecycle integration.
- E2E tests prove live output in single-process and xdist runs.
- Compatibility replay tests prove canonical NDJSON remains the stable replay
  artifact and that standalone rendering uses the explicit service boundary.

## Phase 2: Implementation Strategy

1. Extract reporter assembly, formatter request normalization, xdist role
   decisions, and runtime asset preparation away from the reporter root so
   `plugin.py` becomes a narrow coordination surface.
2. Replace entrypoint duck typing and private-state fallback with one explicit
   public lifecycle contract shared by the reporter runtime.
3. Convert reporter services to explicit narrow collaborator dependencies and
   remove reporter-backed service-locator access patterns.
4. Introduce a first-class standalone rendering service API and migrate the
   CLI replay path to that boundary instead of synthetic pytest runtime
   objects.
5. Move formatter-specific request-building and runtime-asset behavior into the
   formatter plugin modules or formatter-owned collaborators, leaving shared
   support code as reusable primitives only.
6. Eliminate supported package-scan discovery fallback so pytest runtime and
   standalone replay each use one canonical formatter discovery path.
7. Re-run contract, hook, e2e, compatibility, docs, and one broad tox matrix
   slice after each architectural seam is moved.
