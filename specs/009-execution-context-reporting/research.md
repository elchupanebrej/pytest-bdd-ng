# Phase 0 Research: Execution Context Reporting Consistency

## Decision 1: Remove `Feature` From the Runtime Boundary Entirely

- Decision: Eliminate `src/pytest_bdd/model/gherkin_document/core.py::Feature` from parser, locator, collector, hook, fixture, and reporting flows.
- Rationale: The wrapper duplicates data already present in `GherkinDocument`, `Source`, and `Pickle`, and it creates a second mutable boundary that conflicts with the run-owned execution model.
- Alternatives considered:
  - Keep `Feature` as an internal adapter but hide it from hooks and fixtures: rejected because parser, locator, and reporter code would still depend on adapter-specific helpers and state.
  - Preserve `Feature` as a compatibility shim: rejected because it prolongs the migration and leaves two competing feature-state models.

## Decision 2: Canonical Collection Payload Is `Source + GherkinDocument + Pickle`

- Decision: Feature collection and parametrization should operate on canonical cucumber message objects and raw source content only.
- Rationale: These objects are already the protocol truth, they are serializable, and they align with reporting/governance requirements without extra wrapping.
- Alternatives considered:
  - Introduce a new feature wrapper class instead of `Feature`: rejected because it recreates the same boundary problem under a different name.

## Decision 3: `Run` Owns Session-Wide Feature Bindings and Shared Object Registry

- Decision: Add a run-owned feature binding record keyed by feature URI that stores `Source`, `GherkinDocument`, compiled `Pickle` objects, and derived feature metadata, while the session-wide identifiable-object registry remains owned by `Run`.
- Rationale: Feature-level lookup state is session-scoped and shared across plugins, so both the binding map and the canonical ID index belong in the session root rather than on per-feature wrappers or per-plugin caches.
- Alternatives considered:
  - Rebuild the feature registry from `GherkinDocument` on every consumer read: rejected because it repeats work and encourages consumer-specific helper logic.
  - Store feature bindings directly in `config.stash` as standalone values: rejected because `Run` is already the canonical session state root.

## Decision 4: `pytest_bdd_id_generator` Lives in `config.stash`

- Decision: Move `pytest_bdd_id_generator` from ad-hoc `config` attributes into `pytest config.stash` as a session-shared runtime service.
- Rationale: The ID generator is shared mutable runtime state and should follow the same stash-backed access pattern as `Run` and `EnvelopeRegistry`.
- Alternatives considered:
  - Keep `config.pytest_bdd_id_generator` as an implementation detail: rejected because it creates a second transport mechanism for runtime state and violates the clarified contract.
  - Store a fresh ID generator per plugin instance: rejected because IDs must remain deterministic and shared across collection, runtime, and reporting flows.

## Decision 5: `ScenarioRun` Holds the Active Feature Binding Reference

- Decision: `ScenarioRun` should store the active feature binding key or resolved binding reference alongside `gherkin_document`, `source`, and `pickle`.
- Rationale: Scenario-scoped execution needs fast access to feature metadata and AST lookups without reconstructing wrappers or consulting fixture state.
- Alternatives considered:
  - Keep feature-only data on `Run` and resolve it ad hoc everywhere: rejected because it spreads lookup rules across plugins.

## Decision 6: Hooks Receive `Run`, Not `Feature`

- Decision: Hook APIs remain centered on `run: Run`, and hook implementations recover `ScenarioRun`, `GherkinDocument`, `Source`, `Pickle`, and step objects from the run graph.
- Rationale: `Run` is already version-stable and avoids repeated hook signature churn when runtime details change.
- Alternatives considered:
  - Expose `Feature` plus `Pickle` in hook signatures: rejected because it reintroduces the adapter and duplicates state access patterns.

## Decision 7: Fixtures Must Not Expose `Feature`

- Decision: Remove the `feature` fixture from the executable runtime surface. Consumers use `gherkin_document`, `feature_source`, `pickle`, and `run_context` instead.
- Rationale: A fixture returning `Feature` would preserve the forbidden adapter on the public runtime API even if internal code stopped using it.
- Alternatives considered:
  - Keep `feature` as a legacy compatibility fixture backed by canonical data: rejected because the spec forbids `Feature` in fixtures and because the project already accepted immediate breaking changes for semantic cleanup.

## Decision 8: Reporter and Scenario Serialization Read Through Run-Owned Bindings

- Decision: Reporter and scenario serialization logic should derive feature names, descriptions, tags, line numbers, step keywords, and table/doc-string lookups from `Run` / `ScenarioRun` helpers backed by the feature binding registry.
- Rationale: This keeps the reporting layer read-only and removes the remaining dependency on `Feature` helper methods.
- Alternatives considered:
  - Inline AST-walking logic in each reporter: rejected because it duplicates lookup code and weakens determinism.

## Decision 9: The Execution/Message Adapter Stays, but `Feature` Is Not Part of It

- Decision: Keep `ExecutionMessageAdapter` as the only execution-to-message translation layer, but limit its inputs to run-owned bindings and canonical message objects.
- Rationale: The adapter boundary is still valuable for protocol conversion and replay projection, but it must not take a feature wrapper dependency.
- Alternatives considered:
  - Collapse the adapter into reporters once `Feature` is removed: rejected because message conversion would spread across plugins again.

## Decision 10: Collection Event Ordering Must Stay `Source -> Feature Document -> Pickle`

- Decision: Collection emits `pytest_bdd_source_read`, then `pytest_bdd_feature_read`, then `pytest_bdd_pickle_read`, with all three events using canonical message objects.
- Rationale: This ordering matches the natural parse/compile pipeline and lets reporters and governance tooling observe feature materialization without wrapper coupling.
- Alternatives considered:
  - Emit combined feature+pickle events only: rejected because it hides intermediate states and weakens diagnostics for parse/compile failures.

## Decision 11: Governance Rules Remain Strictly Runtime-Observed

- Decision: Runtime-required capability fields still require real runtime observation, and any uncovered capability still needs an explicit `Partly-Applicable` or `Non-Implementable` decision with evidence.
- Rationale: Removing `Feature` should reduce modeling ambiguity, not relax the evidence bar for reporting coverage.
- Alternatives considered:
  - Treat feature-wrapper removal as sufficient justification for deferred governance work: rejected because the contract remains CI-enforced.
