# Research: E2E Conversion

## Decision 1: Conversion boundary

- Decision: Convert only user-facing scenarios; keep technical/regression scenarios in pytest tests.
- Rationale: Preserves documentation clarity without losing low-level regression coverage.

## Decision 2: Parity quality gate

- Decision: Require parity audit per conversion (intent, assertions, clarity, stale-link checks).
- Rationale: Prevents semantic drift during conversion.

## Decision 3: Fix workflow

- Decision: Apply parity fixes in follow-up commits rather than rewriting conversion history.
- Rationale: Keeps review trail explicit and matches governance requirements.
