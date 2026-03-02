# Research Notes: Maximize Messages Capability Coverage

## Decision 1: Mandatory Scope Source and Cardinality
- **Decision**: Treat `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/specs/008-maximize-messages-coverage/mandatory-hook-capability-ids.txt` as the normative mandatory-scope source (323 capability IDs).
- **Rationale**: Stakeholders explicitly designated this exact list as mandatory hook-populated fields for release readiness.
- **Alternatives considered**:
  - Continue using inferred uncovered IDs from ad-hoc runs: rejected because run-dependent lists are not deterministic.
  - Keep mandatory scope only in prose spec: rejected because it is not machine-enforceable.

## Decision 2: Governance Enforcement for Mandatory IDs
- **Decision**: Governance report generation must enforce that all mandatory IDs are `Implemented`; mandatory IDs cannot be accepted as `Non-Implementable`, `Not-Applicable`, or `Not-Acceptable`.
- **Rationale**: FR-014/FR-015 and SC-006 require implementation, not deferral, for mandatory list entries.
- **Alternatives considered**:
  - Allow deferred statuses for mandatory IDs with evidence: rejected because it violates acceptance criteria.
  - Keep only `blocked/pending` checks: rejected because deferred mandatory IDs can bypass strict mode.

## Decision 3: Capability Key Normalization Strategy
- **Decision**: Normalize runtime-observed payload keys and inventory keys to a single canonical capability ID shape before coverage/gov matching.
- **Rationale**: Current mixed casing/shape (`gherkin_document` vs `gherkinDocument`) causes false negatives even when data is emitted.
- **Alternatives considered**:
  - Preserve mixed formats and rely on manual mapping exceptions: rejected as brittle and error-prone.
  - Fork separate inventories per reporter format: rejected due to complexity and drift risk.

## Decision 4: Hook Formation Point Expansion
- **Decision**: Extend reporter formation points to populate missing mandatory fields for `attachment`, `externalAttachment`, and deep `gherkinDocument` branches, while preserving existing attachment semantics.
- **Rationale**: Current formation points do not emit many required fields (`source.*`, timestamps, rule/background AST depth, comments).
- **Alternatives considered**:
  - Leave formation unchanged and mark gaps as non-applicable: rejected by mandatory scope requirements.
  - Create synthetic post-processing filler values detached from hooks: rejected because it breaks traceability to runtime events.

## Decision 5: Dedicated Audit Data Strategy
- **Decision**: Keep a dedicated suite separate from the main suite and expand audit inputs to force mandatory paths (attachment calls, feature/rule/background/examples/docstring/datatable structures).
- **Rationale**: Main suite can evolve independently; dedicated suite must remain stable and exhaustive for mandatory coverage governance.
- **Alternatives considered**:
  - Reuse main suite only: rejected because coverage can regress silently when unrelated tests change.
  - Run audit assertions on production runs only: rejected due to nondeterministic run surfaces.

## Decision 6: Performance-Safe Validation Modes
- **Decision**: Preserve opt-in heavy coverage tracing for audit contexts; default runs keep lightweight validation behavior.
- **Rationale**: Exhaustive field tracking is expensive and should not degrade day-to-day feedback loops.
- **Alternatives considered**:
  - Always-on exhaustive tracing: rejected due to avoidable overhead.
  - Disable validation in default runs entirely: rejected because it weakens correctness guarantees.

## Decision 7: Contract Layering
- **Decision**: Keep OpenAPI + JSON Schema governance contracts and add a CLI contract schema for report-command mandatory-scope enforcement options.
- **Rationale**: This project exposes CLI workflows; command-level contract closes the gap between operation docs and executable parameters.
- **Alternatives considered**:
  - OpenAPI-only contracts: rejected because CLI constraints become implicit.
  - JSON-Schema-only contracts: rejected because operation semantics become less explicit.

## Decision 8: CI Gate Placement
- **Decision**: Keep dedicated coverage audit as an explicit CI gate and make mandatory coverage pass/fail non-optional for release flows.
- **Rationale**: Weekly baseline drift checks detect upstream changes but do not prove mandatory runtime implementation.
- **Alternatives considered**:
  - Keep audit as manual script only: rejected because it is easy to skip.
  - Merge audit into every default test job: deferred due to runtime cost and matrix explosion.

## Clarification Resolution Summary
All technical context unknowns required for planning are resolved:
- Mandatory-scope source and enforcement behavior
- Matching normalization requirements
- Hook formation expansion scope
- Dedicated audit strategy and performance posture
- Contract update strategy and CI gate placement
