<!-- markdownlint-disable MD013 -->

# Research: Strict Non-Null Lifecycle Refactoring

## Decision 1: Keep the scope on internal lifecycle-managed runtime state

- Decision: Focus the refactor on internal lifecycle-managed objects in `Run`, `ScenarioRun`, lifecycle access helpers, reporter consumers, and parse-error emission boundaries.
- Rationale: These flows promise deterministic stage-driven availability and are the places where `None` currently obscures lifecycle invariants. They deliver the highest value for the requested refactor.
- Alternatives considered:
  - Refactor every `Optional[...]` in the repository at once: rejected because many optionals model external payload variability rather than lifecycle rules.
  - Limit the work to one slot such as `step_run`: rejected because `run_access`, reporter consumers, and parser boundaries would still leak nullable handling across the same lifecycle.

## Decision 2: Represent every covered inactive lifecycle slot with a dedicated Empty-State Object

- Decision: Every in-scope lifecycle-managed type that can be inactive by design should have its own dedicated Empty-State Object rather than using `None` or a generic sentinel.
- Rationale: A dedicated object makes the state explicit, keeps the contract stable, and prevents routine caller-side branching on missing values.
- Alternatives considered:
  - Keep returning `None` for inactive slots: rejected because it violates the clarified spec and the constitution rule against routine `None` returns outside hooks.
  - Use one generic empty wrapper for every slot: rejected because different lifecycle types need different contract-compatible fields and behaviors.

## Decision 3: Require Empty-State Objects to preserve a contract-compatible subset

- Decision: Empty-State Objects should expose the subset of fields and behaviors that covered consumers legitimately use from the populated object.
- Rationale: This keeps consumer logic polymorphic and avoids reintroducing `None` checks or type-dispatch branches in normal code paths.
- Alternatives considered:
  - Give Empty-State Objects only metadata and force consumers to branch: rejected because it defeats the purpose of the refactor.
  - Make Empty-State Objects fully mimic every behavior of populated objects: rejected because that can hide invalid lifecycle usage and blur the difference between empty and populated semantics.

## Decision 4: Centralize invariant enforcement through reusable lifecycle guards

- Decision: Enforce lifecycle availability rules at centralized lifecycle boundaries through reusable guards instead of repeated inline `if value is None` checks inside consumer methods.
- Rationale: Central guards make lifecycle ownership explicit, reduce duplicated logic, and keep deterministic failure behavior consistent across hooks, reporters, and helper accessors.
- Alternatives considered:
  - Let each method defend itself with ad-hoc checks: rejected because invariants drift and become harder to review.
  - Replace all failures with implicit empty objects: rejected because genuine lifecycle order violations must remain deterministic failures.

## Decision 5: Preserve public hook and plugin compatibility while tightening internals

- Decision: Keep the public `run` hook argument, `run_context` fixture/stash identity, hook names, hook argument shapes, and decorator symbol surface unchanged while tightening internal lifecycle guarantees behind them.
- Rationale: The feature is an internal runtime refactor, not a public API redesign. Existing compatibility tests treat those surfaces as externally visible contracts.
- Alternatives considered:
  - Introduce new public wrapper types in hook signatures: rejected because it creates avoidable migration risk.
  - Hide the new guarantees only in undocumented internals: rejected because explicit contract artifacts are part of the constitution.

## Decision 6: Treat reporting and parse-error flows as guarded boundaries, not nullable helpers

- Decision: Reporter snapshots and parse-error emission should consume centralized lifecycle guard results and explicit Empty-State Objects rather than ad-hoc nullable helper returns.
- Rationale: These boundaries are frequent downstream consumers of lifecycle state and must remain deterministic even when the runtime is idle, incomplete, or externally unresolved.
- Alternatives considered:
  - Return `None` snapshots or no-op lambdas from helpers: rejected because that turns missing state back into the dominant contract.
  - Push all fallback logic into reporter implementations: rejected because each reporter would duplicate the same lifecycle policy.

## Decision 7: Keep external schema optionals out of primary scope unless promoted into runtime state

- Decision: Leave message-schema, transport, and historical payload optionals outside the primary refactor unless they are converted into internal lifecycle-managed objects.
- Rationale: Those optionals often reflect third-party protocol shape rather than lifecycle modeling mistakes inside the runtime.
- Alternatives considered:
  - Normalize all external optionals now: rejected because it expands scope without directly serving the lifecycle invariant goal.
  - Ignore enrichment boundaries completely: rejected because unresolved enrichment used by covered consumers still needs an explicit contract-compatible empty state.

## Decision 8: Validate with targeted lifecycle, reporting, contract, and compatibility suites

- Decision: Use targeted hook/runtime tests, feature lifecycle tests, reporter and reference-resolution tests, contract tests, compatibility suites, and repository quality gates as the planning validation baseline.
- Rationale: The refactor changes lifecycle semantics across multiple layers. Regression coverage must prove both behavior preservation and stronger non-null guarantees.
- Alternatives considered:
  - Rely on unit tests for one module only: rejected because downstream reporters and hook consumers are core beneficiaries of the change.
  - Depend on full matrix execution only: rejected because it is slower and less diagnostic than targeted lifecycle suites during implementation.
