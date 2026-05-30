<!-- markdownlint-disable MD013 -->

# Research: Unified Session-Root Execution Context

## Decision 1: Initialize session root at `pytest_sessionstart`

- Decision: Create `SessionExecutionContext` during `pytest_sessionstart` and keep it alive for the full pytest session.
- Rationale: Guarantees early availability for runtime hooks and deterministic lifecycle ownership without lazy first-use side effects.
- Alternatives considered:
  - Lazy creation on first BDD hook: rejected because early reporting/setup code can observe uninitialized context.
  - Per-scenario root contexts: rejected because it breaks shared session-level visibility.

## Decision 2: Canonicalize through `pytest.config.stash`

- Decision: Store the canonical `SessionExecutionContext` in `pytest.config.stash` under a dedicated stash key and treat stash as the single source of session truth.
- Rationale: `pytest.config.stash` is pytest-native session-scoped storage and avoids ad-hoc globals.
- Alternatives considered:
  - Module-level global state: rejected due to plugin isolation and test contamination risks.
  - Session object custom attributes only: rejected because stash provides clearer key ownership and collision control.

## Decision 3: Expose session context as a session-scoped fixture

- Decision: Provide a session-scoped fixture that resolves `SessionExecutionContext` directly from stash.
- Rationale: Meets fixture injection requirement while ensuring fixture and stash references are identical.
- Alternatives considered:
  - Fixture creates independent object: rejected because it violates canonical identity across consumers.
  - Function-scoped fixture wrappers only: rejected because session identity consistency is mandatory.

## Decision 4: Keep `execution_context` field-based on hook parameter models

- Decision: Continue to expose `execution_context` as a field/reference on existing hook parameter objects; do not introduce a separate top-level hook argument as the primary contract.
- Rationale: Preserves compatibility and aligns with clarified feature requirements.
- Alternatives considered:
  - Mandatory explicit hook argument: rejected due to API churn and migration cost.
  - New wrapper object replacing existing parameters: rejected because it would be externally breaking.

## Decision 5: Reporting reads hierarchy first, then degrades gracefully

- Decision: Reporting paths should consume hierarchy state (session/feature/scenario/step nodes) whenever available and fallback to session-level context plus structured unavailable-object diagnostics when a scope is inactive.
- Rationale: Preserves diagnostic quality and keeps reporting consistent across normal and failure/teardown stages.
- Alternatives considered:
  - Reporting uses only ad-hoc event data: rejected because lifecycle coherence is lost.
  - Hard failure on inactive node during reporting: rejected because teardown/failure reporting must remain robust.

## Decision 6: Broad `gherkin_document` modularization remains required

- Decision: Keep the broad split of `src/pytest_bdd/model/gherkin_document.py` into cohesive modules (`core`, `registry`, `lookup`) with compatibility import support.
- Rationale: Enables reuse across context hierarchy and reporting while keeping backward-compatible import behavior.
- Alternatives considered:
  - Keep monolith and patch utility functions only: rejected as insufficient for reuse and maintenance.

## Decision 7: External API evolution remains additive-only

- Decision: Enforce additive-only public API changes via baseline comparison (`removed_symbols=[]`, `renamed_symbols=[]`).
- Rationale: Required by compatibility constraints and consumer migration policy.
- Alternatives considered:
  - Manual review without automated guard: rejected due to repeatability and regression risk.
