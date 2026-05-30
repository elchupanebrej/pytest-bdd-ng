# Research Notes: Maximize Messages Capability Coverage

## Decision 1: Runtime Extraction-First Strategy
- **Decision**: Capabilities are treated as runtime-required when they can be extracted from real Python runtime events or available pytest-bdd hook surfaces after extending reporter integration where technically feasible.
- **Rationale**: This matches the clarified scope that coverage must come from real execution, not synthetic probe payloads. It also prevents premature `Non-Implementable` classification when runtime extraction is actually achievable by plugin changes.
- **Alternatives considered**:
  - Freeze current runtime extraction surface and classify remaining fields as `Non-Implementable`: rejected because it underuses available runtime context and creates false governance debt.
  - Define runtime-required only from currently observed fields in one suite: rejected because it ignores extractable-but-not-yet-emitted fields.

## Decision 2: Reporter Runtime Purity
- **Decision**: Reporter emission path remains runtime-pure: only real events are emitted, with no synthetic probe envelopes and no test-only substitutions in production flow.
- **Rationale**: Keeps external plugin behavior truthful and prevents test instrumentation from leaking into user-facing API semantics.
- **Alternatives considered**:
  - Add synthetic event mode in reporter behind flags: rejected due to behavioral coupling and accidental misuse risk.
  - Always enrich missing fields during emission: rejected because it fabricates evidence.

## Decision 3: Post-Factum Governance Layer
- **Decision**: Coverage reconciliation and governance status calculation are executed from emitted NDJSON artifacts after test run completion.
- **Rationale**: Maintains clear separation of concerns: runtime reporting captures facts; governance computes decisions from facts.
- **Alternatives considered**:
  - Inline governance decisions during event emission: rejected due to runtime complexity and reduced debuggability.
  - Manual governance without deterministic analyzer: rejected due to drift and non-reproducible release decisions.

## Decision 4: Strict Non-Implementable Eligibility
- **Decision**: `Non-Implementable` is allowed only for objectively unreachable capabilities in Python runtime, and each such decision must include a hard technical limitation statement plus reproducible proof bundle.
- **Rationale**: Enforces honest exceptions and aligns governance with stakeholder requirement: only hard impossibility is acceptable.
- **Alternatives considered**:
  - Allow `Non-Implementable` for not-yet-implemented plugin extraction work: rejected because this is implementation backlog, not impossibility.
  - Allow generic rationale text without technical proof: rejected because it is not auditable.

## Decision 5: Deterministic Gate Model
- **Decision**: Use canonical sets per release target:
  - `I`: canonical inventory IDs,
  - `R`: runtime-required IDs,
  - `O`: runtime-observed IDs from real NDJSON,
  - `D`: validated governance decisions with unique (`capability_id`, `release_target`).

  Gate rules:
  1. Inventory integrity: `R ⊆ I` and all IDs are unique/known.
  2. Runtime-required gate: `R ⊆ O`.
  3. Non-runtime gate: each `c ∈ I - R` is either in `O` or has a valid explicit decision in `D`.
  4. Blocker gate: no unresolved blockers (`Pending`, `Not-Acceptable`) at release sign-off.
  5. Decision integrity: no duplicate decisions per capability per release target.
- **Rationale**: Ensures deterministic, testable, and explainable release outcomes.
- **Alternatives considered**:
  - Single aggregate score without explicit gates: rejected because failure source becomes opaque.
  - Optional strict mode toggles for release gate: rejected because policy enforcement must be deterministic.

## Decision 6: Evidence Requirements for Hard Limitations
- **Decision**: For each `Non-Implementable` entry, mandatory evidence bundle includes:
  - hard technical limitation statement,
  - reproducible runtime evidence reference,
  - decision owner,
  - review timestamp in current release cycle,
  - explicit `recheck_trigger`.
- **Rationale**: Converts exceptions into auditable engineering records and allows future reevaluation when runtime/hook surfaces evolve.
- **Alternatives considered**:
  - Owner + rationale only: rejected as insufficient for audit.
  - Runtime trace only without limitation statement: rejected because it proves absence, not impossibility.

## Decision 7: Runtime Extension Surface Prioritization
- **Decision**: Prioritize reporter/runtime extensions for currently extractable-but-unemitted capability families before classifying anything as `Non-Implementable`.
- **Rationale**: Codebase review shows several capabilities are available from existing runtime/hook context but are not emitted yet (for example `hook.type`, `testCase.testRunStartedId`, parse/suggestion/undefined-parameter envelopes, and richer hook/parameter source references).
- **Alternatives considered**:
  - Continue classifying all missing fields as governance exceptions: rejected because these are mostly implementation gaps, not hard impossibility.
  - Delay reporter extension until post-release: rejected because runtime-required gate would become artificially weak.

## Decision 8: Hard-Unreachable Boundary (Current Runtime)
- **Decision**: Treat Java-native provenance details (`*.javaMethod.*`, `*.javaStackTraceElement.*`) as candidate hard-unreachable fields in Python runtime unless proven otherwise by real bridge data.
- **Rationale**: Python runtime does not natively produce JVM-origin method/stack semantics; fabricating those values would violate runtime purity.
- **Alternatives considered**:
  - Populate Java fields via synthetic placeholders: rejected because it produces false evidence.
  - Classify all source reference fields as unreachable: rejected because Python source-location fields are available and should be emitted.

## Clarification Resolution Summary
All planning-time unknowns are resolved for this feature:
- Runtime purity boundary is explicit.
- Runtime-required scope derivation policy is explicit.
- Non-implementable eligibility and required proof are explicit.
- CI gate semantics are deterministic and fully specified.
- Runtime extension points and candidate hard-unreachable boundaries are explicitly documented.
