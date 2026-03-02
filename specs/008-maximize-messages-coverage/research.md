# Research Notes: Maximize Messages Capability Coverage

## Decision 1: Canonical Schema Baseline and Resolution Strategy
- **Decision**: Use `messages/jsonschema/src/Envelope.json` from the repository submodule as the canonical baseline. Resolve packaged artifacts via `importlib.resources`; for development and test-only paths, resolve via `git` repository paths.
- **Rationale**: The feature requires deterministic baseline tracking and prohibits relative module-path discovery. This strategy keeps artifact sourcing reproducible across local runs, CI, and packaged execution.
- **Alternatives considered**:
  - Relative `__file__` path traversal: rejected because it is brittle and explicitly prohibited.
  - Environment variable path overrides: rejected to avoid hidden configuration drift.
  - Runtime network fetch of schema: rejected due to non-determinism and offline fragility.

## Decision 2: Weekly Baseline Drift Execution Model
- **Decision**: Use a dedicated weekly CI workflow that runs baseline diff generation only, stores diff artifacts, and fails when added/changed/removed capability IDs are detected.
- **Rationale**: Existing CI triggers are not scheduled weekly, and a dedicated drift workflow isolates governance signal from broader matrix noise.
- **Alternatives considered**:
  - Add schedule to existing full matrix workflow: rejected as noisy and less actionable.
  - Manual local cadence: rejected because it cannot enforce weekly guarantees.
  - Submodule/tag-only checks: rejected because they do not produce actionable capability deltas.

## Decision 3: Runtime Validation Strictness and Diagnostics
- **Decision**: Keep fail-fast validation for coverage gates, but standardize structured diagnostics (`json_path`, `schema_path`, validator name, and context) so failures are actionable.
- **Rationale**: The specification requires hard failure on missing or structurally invalid coverage; structured diagnostics preserve developer productivity while enforcing strictness.
- **Alternatives considered**:
  - Warning-only reporting: rejected because gaps could ship silently.
  - Aggregate-all-errors only mode: rejected as default gate because it slows triage-critical runs.

## Decision 4: Deterministic Outcome Mapping Across Entry Points
- **Decision**: Compute canonical outcome mapping once and make all reporting surfaces consume that canonical mapping and status vocabulary.
- **Rationale**: Independent per-reporter mapping introduces terminology drift and order-dependent behavior in hook execution.
- **Alternatives considered**:
  - Reporter-specific mapping logic: rejected due to inconsistency risk.
  - Fallback remapping of unknown statuses: rejected because it hides defects.

## Decision 5: Opt-In Coverage Tracing with Minimal Default Overhead
- **Decision**: Keep dynamic traceability opt-in via a dedicated boolean CLI flag (`store_true`, default `False`), and gate heavy tracing work so disabled runs incur near-zero additional cost.
- **Rationale**: This aligns with existing plugin option patterns and preserves default test performance while enabling deep coverage when requested.
- **Alternatives considered**:
  - Always-on tracing: rejected due to broad overhead.
  - Multi-source config precedence only (CLI+INI tri-state): deferred unless needed by future policy.

## Decision 6: Contract Layering and Versioning
- **Decision**: Keep two complementary contract layers: feature-scoped OpenAPI for governance operations/policy and JSON Schema for generated governance artifact structure. Keep runtime output as NDJSON envelopes aligned with latest approved protocol.
- **Rationale**: This matches existing repository contract patterns and separates operational policy from artifact shape validation.
- **Alternatives considered**:
  - OpenAPI-only contracts: rejected because artifact shape constraints become weaker.
  - JSON-Schema-only contracts: rejected because operation-level workflow semantics become less explicit.

## Clarification Resolution Summary
All technical-context unknowns have been resolved in this research phase:
- Baseline source and path policy
- Weekly diff execution model
- Validation strictness and diagnostic policy
- Mapping consistency strategy
- Tracing opt-in behavior
- Contract layering/versioning
