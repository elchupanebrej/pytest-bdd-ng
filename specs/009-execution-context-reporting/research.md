# Phase 0 Research: Execution Context Reporting Consistency

## Decision 1: Execution/Reporting Ownership Split

- Decision: Execution plugins (`scenario_runner` flow) are the only writers of `ExecutionContext`; reporting plugins are read-only consumers.
- Rationale: Eliminates duplicated mutable state (`current_*`), prevents reporter-side drift, and enforces FR-011..FR-014.
- Alternatives considered:
  - Shared read/write ownership: rejected due to race-prone implicit coupling.
  - Reporter-maintained mirrors: rejected due to state divergence and hidden lifecycle bugs.

## Decision 2: Registry Ownership in Context, Not Feature Model

- Decision: AST/object registry ownership remains in `ExecutionContext` and is shared across plugin boundaries via `config.stash` context entries.
- Rationale: Keeps `Feature` representational and centralizes runtime lookup authority.
- Alternatives considered:
  - Keep registry in `Feature`: rejected because model layer would carry runtime mutable state.
  - Duplicate registry in `Feature` and context: rejected due to synchronization risk.

## Decision 3: Adapter Boundary Is Mandatory

- Decision: Introduce a dedicated `ExecutionMessageAdapter` layer as the only conversion boundary between execution model and cucumber message model.
- Rationale: Isolates message-schema evolution, simplifies governance auditing, and satisfies FR-015/FR-016.
- Alternatives considered:
  - Keep conversion distributed in reporter methods: rejected due to drift and maintenance overhead.
  - Full immediate replacement of runtime types: rejected as high-risk, high-churn refactor.

## Decision 4: Deterministic Serialize/Deserialize Strategy

- Decision: Execution model round-trip (execution -> message -> execution) uses adapter mapping + context-owned registries (AST registry + message ID index), not `ExecutionContext.as_dict()` snapshots.
- Rationale: `as_dict()` is intentionally lossy for object/link reconstruction; deterministic ID mapping is required by FR-017/FR-018.
- Alternatives considered:
  - Serialize/deserialize from `ExecutionContext.as_dict()`: rejected because link graph cannot be reconstructed.
  - Regenerate IDs on deserialize: rejected because references lose identity consistency.
  - Canonicalize Python `id(...)` as external key: rejected because values are process-local and unstable.

## Decision 5: Message Reference Index Keying

- Decision: Message-object registry keys are deterministic and worker-safe: `(worker_id, payload_kind, payload_id)`.
- Rationale: Prevents xdist collisions and ensures consistent replay/merge behavior.
- Alternatives considered:
  - Key only by `payload_id`: rejected due to worker collision risk.
  - Maintain global stash-only message registry: rejected due to mixed ownership and stale-entry risk.

## Decision 6: Missing Data Policy Is Non-Fabricating

- Decision: Missing context or unresolved references produce deterministic diagnostics; no synthetic state or fake events are generated.
- Rationale: Preserves truthful coverage and auditable governance outcomes (FR-007, FR-010).
- Alternatives considered:
  - Silent fallback defaults: rejected because failures become non-observable.
  - Synthetic backfilling: rejected because it contaminates runtime evidence.

## Decision 7: Contract Coverage for Runtime + Governance

- Decision: Maintain explicit contracts for (1) execution/reporting ownership boundary, (2) adapter conversion semantics, and (3) governance gate rules.
- Rationale: These are the cross-module integration points with highest regression and compliance impact.
- Alternatives considered:
  - No contract artifacts: rejected due to low maintainability for cross-plugin behavior.
  - Single merged contract: rejected to keep operational and release-governance responsibilities separable.
