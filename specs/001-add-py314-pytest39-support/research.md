# Research: Python/Pytest Compatibility Matrix

## Decision 1: Compatibility source of truth

- Decision: Treat pytest compatibility constraints as the source of truth for valid Python/pytest pairs.
- Rationale: The feature explicitly requires no additional project-specific caps beyond pytest-to-python compatibility.
- Alternatives considered:
  - Hard-code a fixed list of supported pairs: rejected because it drifts and reintroduces manual caps.
  - Support only latest pytest per Python version: rejected because it does not satisfy "all compatible pairs".

## Decision 2: Matrix generation strategy

- Decision: Generate full pair coverage by combining:
  - Project-supported Python versions available in CI/local matrix
  - Pytest versions within support window
  - Filtering rules that keep only pytest-compatible Python/pytest pairs
- Rationale: Ensures complete coverage while remaining deterministic and auditable.
- Alternatives considered:
  - Representative sampling: rejected by clarification requiring all compatible pairs.
  - Unbounded historical pytest versions: rejected due to excessive matrix size and low value.

## Decision 3: Validation contract format

- Decision: Define a simple REST-style contract describing matrix listing and pair validation.
- Rationale: Provides an explicit, testable interface for tooling and CI integration.
- Alternatives considered:
  - No contract artifact: rejected because behavior becomes implicit and harder to test.
  - GraphQL schema: rejected as unnecessary for this feature scope.

## Decision 4: Failure handling policy

- Decision: Fail fast with explicit reason codes for unsupported or unavailable pairs.
- Rationale: Required by FR-006 and reduces triage time.
- Alternatives considered:
  - Silent skip of unsupported pairs: rejected because it obscures coverage gaps.
  - Generic install error propagation only: rejected because it is not actionable.

## Decision 5: Documentation policy

- Decision: Publish support policy as "all pytest-compatible pairs" and include runnable commands to validate any pair.
- Rationale: Keeps contributor expectations aligned with the clarified requirement.
- Alternatives considered:
  - Document only CI-covered pairs: rejected because it can be read as an implicit cap.
